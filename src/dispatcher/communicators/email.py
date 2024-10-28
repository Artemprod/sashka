from src.dispatcher import BaseCommunicator


class EmailCommunicator(BaseCommunicator):
    registry_key = "email"

    def __init__(self, email_address, smtp_server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_address = email_address
        self.smtp_server = smtp_server

    async def get_code(self) -> str:
        # Ваша реализация
        pass