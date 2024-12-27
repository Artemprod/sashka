import asyncio
import io
import json
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

import pandas
import pandas as pd
from loguru import logger
from sqlalchemy import text

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.querys import SQLQueryBuilder


# TODO можно подумать над тем чтобы внести инциализацию сесии менеджера внутрь
class Dialogs:

    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager
        self.sql_query = SQLQueryBuilder()


class UserMessages(Dialogs):
    def __init__(self, telegram_id, research_id, session_manager):
        super().__init__(session_manager)
        self.telegram_id = telegram_id
        self.research_id = research_id
        self._telegram_link = None

    @property
    async def telegram_link(self):
        if self._telegram_link is None:
            async with self.session_manager.async_session_factory() as session:
                result = await session.execute(text(self.sql_query.users_tg_link(self.telegram_id)))
                data = result.first()
                if data is not None:
                    self._telegram_link = data[0]  # Если data — это кортеж, нужно обращаться к первому элементу.
        return self._telegram_link  # Возвращает или _telegram_link, если найден, или None.

    async def get_user_messages(self) -> pandas.DataFrame:
        async with self.session_manager.async_session_factory() as session:
            result = await session.execute(text(self.sql_query.user_messages(self.telegram_id, self.research_id)))
            data = result.fetchall()  # получаем данные в виде списка
            columns = result.keys()  # получаем названия столбцов

            # Создаем DataFrame
            df = pd.DataFrame(data, columns=columns)
            df.set_index("user_telegram_id", inplace=True)
            df["created_at"] = pd.to_datetime(df["created_at"])
            df['is_user'] = True
            return df


class AssistantMessages(Dialogs):
    def __init__(self, telegram_id, research_id, session_manager):
        super().__init__(session_manager)
        self.telegram_id = telegram_id
        self.research_id = research_id

    async def get_assistant_messages(self) -> pandas.DataFrame:
        # Генерация SQL-запроса для ассистентских сообщений
        async with self.session_manager.async_session_factory() as session:
            result = await session.execute(text(self.sql_query.assistant_messages(self.telegram_id, self.research_id)))
            data = result.fetchall()  # Получаем данные в виде списка
            columns = result.keys()  # Получаем названия столбцов
            # Создаем DataFrame
            df = pd.DataFrame(data, columns=columns)
            df.set_index("user_telegram_id", inplace=True)
            df["created_at"] = pd.to_datetime(df["created_at"])
            df['is_user'] = False
            return df


class UserDialog(Dialogs):

    def __init__(self, telegram_id, research_id, session_manager):
        super().__init__(session_manager)

        self.telegram_id = telegram_id
        self.research_id = research_id
        self.user_messages = UserMessages(telegram_id=telegram_id, research_id=self.research_id,session_manager=session_manager)
        self.assistant_messages = AssistantMessages(telegram_id=telegram_id, research_id=self.research_id,session_manager=session_manager)
        self.dialog: Optional[pd.DataFrame] = None

    async def get_dialog(self):
        # Получаем сообщения от пользователя и ассистента
        user_messages_df = await self.user_messages.get_user_messages()
        assistant_messages_df = await self.assistant_messages.get_assistant_messages()


        # Объединяем сообщения в один DataFrame
        combined_df = pd.concat([user_messages_df, assistant_messages_df], ignore_index=True)

        # Фильтруем и структурируем данные по дате создания
        messages_by_date = combined_df[["text", "created_at", "is_user"]].set_index("created_at")
        dialog_df = messages_by_date.sort_index()

        telegram_link = pd.DataFrame({
            "text": [f"{await self.user_messages.telegram_link}"],
            "created_at": [pd.Timestamp.min],
            "is_user": [None]
        })

        final_df = pd.concat([telegram_link, dialog_df], ignore_index=True)
        self.dialog = final_df
        return self

    async def get_csv_file(self, path: str) -> str:
        await self.__def_validate_dialog()
        try:
            file = self.dialog.to_csv(path_or_buf=path, encoding='utf-8')
            logger.info(f"csv File {file} saved")
        except Exception as e:
            logger.error(" Faild to save csv file ")
            raise e
        else:
            return path

    async def get_csv_buffer(self) -> io.BytesIO:
        await self.__def_validate_dialog()
        output = io.BytesIO()
        try:
            # Записываем DataFrame в CSV-формат, указывая в качестве аргумента BytesIO
            self.dialog.to_csv(output, index=True, encoding='utf-8')
            logger.info("CSV file created successfully in buffer")
        except Exception as e:
            logger.error("Failed to create CSV file in buffer: %s", e)
            raise e
        output.seek(0)
        return output

    async def get_excel_buffer(self) -> io.BytesIO:
        await self.__def_validate_dialog()

        output = io.BytesIO()

        try:
            # Используем ExcelWriter с объектом BytesIO через менеджер контекста
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                self.dialog.to_excel(writer, sheet_name=str(self.telegram_id), index=False)
            logger.info("Excel file created successfully in buffer")

        except Exception as e:
            logger.error("Failed to create Excel file in buffer: %s", e)
            raise e

        output.seek(0)

        return output

    async def get_excel_file(self, path) -> io.BytesIO:
        await self.__def_validate_dialog()

        try:
            self.dialog.to_excel(path)
            logger.info("excel File  saved")
        except Exception as e:
            logger.error(" Faild to save excel file ")
            raise e
        else:
            return path

    async def __def_validate_dialog(self):
        if self.dialog is None or self.dialog.empty:
            await self.get_dialog()


class ResearchDialogs(Dialogs):



    def __init__(self, research_id, session_manager,research_status:str):
        super().__init__(session_manager)

        self._research_status:str = research_status
        self.dialogs: Dict[int, UserDialog] = {}
        self.research_id = research_id

    async def _generate_query(self):
        query_container = {
            "done": text(self.sql_query.users_in_done_research(research_id=self.research_id)),
            "in_progress": text(self.sql_query.users_in_progress_research(research_id=self.research_id))
        }

        query = query_container.get(self._research_status, None)
        if query is None:
            raise ValueError(f"No research with status {self._research_status}")
        else:
            return query

    async def _get_users_in_research(self) -> List[int]:
        async with self.session_manager.async_session_factory() as session:  # Создаем сессию

            # Генерируем запрос на оснвое статуса иследования
            query = await self._generate_query()

            result = await session.execute(query)  # Асинхронное выполнение запроса
            data = result.fetchall()  # Получаем все строки
            # Преобразуем результат в DataFrame
            df = pd.DataFrame(data, columns=result.keys())
            users = df['tg_user_id'].tolist()  # Извлекаем список user_id
            return users

    async def get_dialogs(self):
        user_ids = await self._get_users_in_research()
        tasks = []

        # Создаем диалоги для каждого пользователя
        for telegram_id in user_ids:
            dialog = UserDialog(telegram_id=telegram_id,research_id=self.research_id, session_manager=self.session_manager)
            tasks.append(dialog.get_dialog())

        try:
            dialogs = await asyncio.gather(*tasks)
            for dialog in dialogs:
                dialog: UserDialog
                self.dialogs[dialog.telegram_id] = dialog

            # Возвращаем все созданные диалоги
            return self
        except Exception as e:
            raise e

    async def to_json(self):
        dialogs_json = {}

        for user_id, dialog in self.dialogs.items():
            # Преобразуем DataFrame в словарь
            dialog_dict = dialog.dialog.to_dict(orient="index")

            # Обновляем ключи, преобразуя их из Timestamp в строку даты и времени
            formatted_dialog = {
                (index.to_pydatetime().strftime('%Y-%m-%d %H:%M:%S') if isinstance(index, pd.Timestamp)
                 else datetime.fromtimestamp(int(index) / 1000).strftime('%Y-%m-%d %H:%M:%S')): value
                for index, value in dialog_dict.items()
            }

            dialogs_json[user_id] = formatted_dialog

        # Преобразуем полный словарь в JSON-строку
        result_json = json.dumps(dialogs_json, ensure_ascii=False, indent=2)
        return result_json



    def __getitem__(self, user_telegram_id):
        return self.dialogs[user_telegram_id].dialog


