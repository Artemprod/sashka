import asyncio

from pyrogram import Client, errors, idle, raw

from src.dispatcher.communicators.reggestry import BaseCommunicator

from src.telegram_client.exceptions.autrization import ClientAuthorizationConnectionError, MaxAttemptsExceededError
from src.telegram_client.exceptions.connection import ClientConnectionError, NoClientError


# # TODO Установка кастомных настроект девайса для клиента и языка
# # TODO Передача датакласса ( paydantic с настройками) загрущка из базы данных
# # TODO  При повторной авторизации сделать проверку аккаунта на спам и блок
# # TODO  вынести все параметры которые отвечают за настроку ожидания в параметры класса
# # TODO  Заменить все Exceptions на кастомные ошибки


class Manager:
    auth_attempts = 4

    def __init__(self, client: Client = None):
        self.app: Client = client



    async def set_up_devise_settings(self):
        ...

    async def init_client(self):
        if self.app is None:
            raise NoClientError
        await self.connect_client()

    async def connect_client(self):
        try:
            if not self.app.is_connected:
                await self.app.connect()
                print("Клиент подключен")
        except Exception as e:
            print(f"Ошибка при подключении клиента: {e}")
            raise ClientConnectionError from e

    async def check_session(self):
        try:
            await self.init_client()
            await self.app.get_me()  # Проверка актуальности сессии
            print("Сессия активна")
            return True
        except errors.Unauthorized:
            print("Сессия неактивна, требуется авторизация")
            return False
        except Exception as e:
            print(f"Ошибка при проверке сессии: {e}")
            return False

    async def authorize(self, communicator: BaseCommunicator):
        try:
            await self.init_client()
            send_code_attempt = 0

            while send_code_attempt < Manager.auth_attempts:
                send_code = await self.app.send_code(self.app.phone_number)
                code_enter_attempts = 0

                while code_enter_attempts < Manager.auth_attempts:
                    code = await communicator.get_code()

                    try:
                        await self.app.sign_in(phone_number=self.app.phone_number,
                                               phone_code_hash=send_code.phone_code_hash,
                                               phone_code=code)
                        print("Successfully signed in!")
                        return

                    except errors.PhoneCodeInvalid:
                        print("The phone code you entered is invalid.")
                        await communicator.send_error(message="The phone code you entered is invalid.")
                        code_enter_attempts += 1

                    except errors.PhoneCodeExpired:
                        print("The phone code you entered has expired.")
                        await communicator.send_error(message="The phone code you entered has expired.")
                        break

                    except errors.SessionPasswordNeeded:
                        print('The cloud password is needed.')
                        await self.app.check_password(self.app.password)
                        return



                    except errors.FloodWait as e:
                        print(f"Too many attempts. Please wait {e} seconds.")
                        raise

                send_code_attempt += 1

            print("Exceeded the maximum number of attempts.")
            await communicator.send_error(message="Exceeded the maximum number of attempts.")
            raise MaxAttemptsExceededError("Exceeded the maximum number of attempts.")

        except errors.PasswordHashInvalid:
            print('The cloud password is wrong.')
            await communicator.send_error(message='The cloud password is wrong.')
            raise

        except MaxAttemptsExceededError:
            print("Exceeded the maximum number of attempts.")
            await communicator.send_error(message="Exceeded the maximum number of attempts wait.")
            raise

        except errors.ApiIdInvalid:
            print("Api id invalid.")
            await communicator.send_error(message="Api id invalid.")
            raise


        except errors.PhoneNumberInvalid:
            print("The phone number you entered is invalid.")
            await communicator.send_error(message="The phone number you entered is invalid.")
            raise

        except Exception as e:
            print(f"An unexpected authorization error occurred: {e}")
            raise ClientAuthorizationConnectionError(message=e) from e

    async def run(self, communicator: BaseCommunicator):

        try:
            await self.init_client()
            if not await self.check_session():
                await self.authorize(communicator)

            await self.app.invoke(raw.functions.updates.GetState())
            await self.app.initialize()

            await idle()

        except errors.SessionExpired:
            print("Сессия истекла, требуется повторная авторизация")
            await self.run(communicator)
            await asyncio.sleep(120)

        except errors.SessionRevoked:
            print("Сессия отозвана, требуется повторная авторизация")
            await self.run(communicator)
            await asyncio.sleep(120)

        except errors.PeerFlood:
            print("Флуд ошибка ")
            await communicator.send_error(message="Флуд ошибка")
            raise

        except errors.PhoneNumberBanned as e:
            print(f"Ошибка: Номер телефона заблокирован. {str(e)}")
            await communicator.send_error(message="The phone code you entered is invalid")
            raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
