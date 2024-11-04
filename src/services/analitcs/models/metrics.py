import csv
from datetime import datetime
from pathlib import Path
from typing import List, Union

from pydantic import BaseModel, Field


class DialogMetrics(BaseModel):
    """Data class для хранения метрик диалога."""
    total_dialogs: int = Field(description="Общее количество диалогов")
    answered_first: int = Field(description="Количество ответов на первое сообщение")
    conversion_rate: float = Field(description="Процент конверсии")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время создания метрики")

    @classmethod
    def export_to_csv(cls, data: List['DialogMetrics'], filepath: Union[str, Path], encoding: str = 'utf-8') -> None:
        """
        Экспорт списка объектов DialogMetrics в CSV файл.

        Args:
            data: Список объектов DialogMetrics для экспорта
            filepath: Путь к файлу для сохранения CSV
            encoding: Кодировка файла (по умолчанию utf-8)

        Raises:
            ValueError: Если список данных пуст
            OSError: При проблемах с записью файла
        """
        if not data:
            raise ValueError("Список данных для экспорта не может быть пустым")

        filepath = Path(filepath)
        # Создаем директорию, если она не существует
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with filepath.open(mode='w', newline='', encoding=encoding) as csv_file:
                # Получаем поля из модели
                fieldnames = list(data[0].model_fields.keys())

                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
                # Записываем заголовки
                writer.writeheader()

                # Записываем данные
                for item in data:
                    # Конвертируем datetime в строку для CSV
                    row_dict = item.model_dump()
                    if isinstance(row_dict['timestamp'], datetime):
                        row_dict['timestamp'] = row_dict['timestamp'].isoformat()
                    writer.writerow(row_dict)

        except OSError as e:
            raise OSError(f"Ошибка при записи CSV файла: {e}")


if __name__ == "__main__":
    metrics_list = [
        DialogMetrics(total_dialogs=100, answered_first=60, conversion_rate=60.0),
        DialogMetrics(total_dialogs=150, answered_first=90, conversion_rate=60.0),
    ]

    DialogMetrics.export_to_csv(metrics_list, 'dialog_metrics.csv')