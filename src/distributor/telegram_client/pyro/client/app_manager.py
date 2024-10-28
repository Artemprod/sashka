import asyncio
from loguru import logger
from pyrogram import Client, errors, idle, raw

from src.dispatcher.communicators.reggestry import BaseCommunicator
from src.distributor.telegram_client.pyro.client.roters.router import Router
from src.distributor.telegram_client.pyro.exceptions.autrization import MaxAttemptsExceededError, \
    ClientAuthorizationConnectionError, AutorizationFaildError
from src.distributor.telegram_client.pyro.exceptions.connection import NoClientError, ClientConnectionError


# # DONE Установка кастомных настроект девайса для клиента и языка ( настройки будут передоваться вметсе с конфигами ДТО)
# # DONE Передача датакласса ( paydantic с настройками) загрущка из базы данных ( передеается клиент )
# # TODO  При повторной авторизации сделать проверку аккаунта на спам и блок
# # DONE  вынести все параметры которые отвечают за настроку ожидания в параметры класса
# # DONE  Заменить все Exceptions на кастомные ошибки

# TODO ЕСЛИ сделаю асинхронный доступ до методов чтобы иметь возмодность поличть домсутп кним не збыть убрать если что

# TODO Передовать дополнительные прараметры котрые будут доступны при передаче сообщения для инъекции
class Manager:
    auth_attempts = 4

    def __init__(self,
                 communicator,
                 client: Client = None,
                 dev_mode: bool = False,
                 ):

        self.app: Client = client
        self._communicator = communicator
        self.session_string = None
        self.is_authorize_status = False
        self.is_banned = False
        self.dev_mode = dev_mode
        logger.warning("CLIENT MANAGER DEV MODE IS ON") if self.dev_mode else logger.warning(
            "CLIENT MANAGER PRODUCTION MODE")

    @property
    def communicator(self) -> BaseCommunicator:
        return self._communicator

    @communicator.setter
    def communicator(self, new_communicator: BaseCommunicator) -> None:
        self._communicator = new_communicator

    async def get_app(self):
        return self.app

    async def dev_mode_get_code(self) -> str:
        if self.app.phone_number:
            return str(self.app.phone_number[5] * 5)
        raise ValueError("No phone number for testing")

    def include_router(self, router: Router):
        for handler, group in router.get_handlers():
            self.app.add_handler(handler, group)

    async def init_client(self):
        if self.app is None:
            raise NoClientError
        await self.connect_client()
        return self.app

    async def connect_client(self):
        try:
            if not self.app.is_connected:
                await self.app.connect()
                print("Клиент подключен")
        except Exception as e:
            print(f"Ошибка при подключении клиента: {e}")
            raise ClientConnectionError from e

    async def is_authorize(self):
        try:
            await self.init_client()
            await self.app.get_me()  # Проверка актуальности сессии
            print("Сессия активна")
            return True
        except errors.Unauthorized:
            print("Сессия неактивна, требуется авторизация")
            self.is_authorize_status = False
            return False
        except Exception as e:
            print(f"Ошибка при проверке сессии: {e}")
            return False

    async def authorize(self):
        try:
            app = await self.init_client()
            send_code_attempt = 0

            while send_code_attempt < Manager.auth_attempts:

                send_code = await self.app.send_code(self.app.phone_number)

                code_enter_attempts = 0
                logger.debug(f"CODE WAS SENT ON {app.phone_number}")
                logger.debug(f"SENT CODE DATA_________________ {send_code}")

                while code_enter_attempts < Manager.auth_attempts:

                    if not self.dev_mode:
                        code = await self._communicator.get_code()
                        logger.debug(f"PROD MOD CODE____________{code}")

                    else:
                        code = await self.dev_mode_get_code()
                        logger.debug(f"DEV MOD CODE____________{code}")

                    try:
                        await self.app.sign_in(phone_number=self.app.phone_number,
                                               phone_code_hash=send_code.phone_code_hash,
                                               phone_code=code)
                        print("Successfully signed in!")
                        return

                    except errors.PhoneCodeInvalid:
                        print("The phone code you entered is invalid.")
                        await self._communicator.send_error(message="The phone code you entered is invalid.")
                        code_enter_attempts += 1

                    except errors.PhoneCodeExpired:
                        print("The phone code you entered has expired.")
                        await self._communicator.send_error(message="The phone code you entered has expired.")
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
            await self._communicator.send_error(message="Exceeded the maximum number of attempts.")
            raise MaxAttemptsExceededError("Exceeded the maximum number of attempts.")

        except errors.PasswordHashInvalid:
            print('The cloud password is wrong.')
            await self._communicator.send_error(message='The cloud password is wrong.')
            raise

        except MaxAttemptsExceededError:
            print("Exceeded the maximum number of attempts.")
            await self._communicator.send_error(message="Exceeded the maximum number of attempts wait.")
            raise

        except errors.ApiIdInvalid:
            print("Api id invalid.")
            await self._communicator.send_error(message="Api id invalid.")
            raise


        except errors.PhoneNumberInvalid:
            print("The phone number you entered is invalid.")
            await self._communicator.send_error(message="The phone number you entered is invalid.")
            raise

        except Exception as e:
            print(f"An unexpected authorization error occurred: {e}")
            raise ClientAuthorizationConnectionError(message=e) from e

    async def initialize(self):

        if not self.app.is_connected:
            raise ConnectionError("Can't initialize a disconnected client")
        if self.app.is_initialized:
            raise ConnectionError("Client is already initialized")
        await self.app.dispatcher.start()
        self.app.updates_watchdog_task = asyncio.create_task(self.app.updates_watchdog())
        self.app.is_initialized = True

    async def run(self):

        try:
            await self.init_client()
            if not await self.is_authorize():
                await self.authorize()

            await self.app.invoke(raw.functions.updates.GetState())

            await self.initialize()
            self.app.me = await self.app.get_me()

            if self.app.me:
                self.is_authorize_status = True
                self.is_banned = False
                self.session_string = await self.app.export_session_string()
                await idle()

        except errors.SessionExpired:
            print("Сессия истекла, требуется повторная авторизация")
            await self.run()
            await asyncio.sleep(120)

        except errors.SessionRevoked:
            print("Сессия отозвана, требуется повторная авторизация")
            await self.run()
            await asyncio.sleep(120)

        except errors.PeerFlood:
            print("Флуд ошибка ")
            await self._communicator.send_error(message="Флуд ошибка")
            raise

        except errors.PhoneNumberBanned as e:
            print(f"Ошибка: Номер телефона заблокирован. {str(e)}")
            self.is_banned = True
            await self._communicator.send_error(message="The phone code you entered is invalid")
            raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise AutorizationFaildError(message=e)


