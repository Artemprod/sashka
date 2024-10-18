import platform
import re

import sys

import os
from pathlib import Path
import logging
from io import StringIO, BytesIO
from mimetypes import MimeTypes
from pathlib import Path
from typing import Union

import pyrogram
from pyrogram import __version__, __license__, Client
from pyrogram import enums

from pyrogram.errors import (
    SessionPasswordNeeded,
    VolumeLocNotFound, ChannelPrivate,
    BadRequest
)

from pyrogram.mime_types import mime_types
from pyrogram.session import Auth, Session

from pyrogram.types import User, TermsOfService

from src.dispatcher.communicators.reggestry import ConsoleCommunicator

log = logging.getLogger(__name__)


class MyClient(Client):
    APP_VERSION = f"Pyrogram {__version__}"
    DEVICE_MODEL = f"{platform.python_implementation()} {platform.python_version()}"
    SYSTEM_VERSION = f"{platform.system()} {platform.release()}"

    LANG_CODE = "en"

    PARENT_DIR = Path(sys.argv[0]).parent

    INVITE_LINK_RE = re.compile(r"^(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.(?:org|me|dog)/(?:joinchat/|\+))([\w-]+)$")
    WORKERS = min(32, (os.cpu_count() or 0) + 4)  # os.cpu_count() can be None
    WORKDIR = PARENT_DIR

    # Interval of seconds in which the updates watchdog will kick in
    UPDATES_WATCHDOG_INTERVAL = 5 * 60

    MAX_CONCURRENT_TRANSMISSIONS = 1

    mimetypes = MimeTypes()
    mimetypes.readfp(StringIO(mime_types))

    def __init__(self,
                 name: str,
                 api_id: Union[int, str] = None,
                 api_hash: str = None,
                 app_version: str = APP_VERSION,
                 device_model: str = DEVICE_MODEL,
                 system_version: str = SYSTEM_VERSION,
                 lang_code: str = LANG_CODE,
                 ipv6: bool = False,
                 proxy: dict = None,
                 test_mode: bool = False,
                 bot_token: str = None,
                 session_string: str = None,
                 in_memory: bool = None,
                 phone_number: str = None,
                 phone_code: str = None,
                 password: str = None,
                 workers: int = WORKERS,
                 workdir: str = WORKDIR,
                 plugins: dict = None,
                 parse_mode: "enums.ParseMode" = enums.ParseMode.DEFAULT,
                 no_updates: bool = None,
                 takeout: bool = None,
                 sleep_threshold: int = Session.SLEEP_THRESHOLD,
                 hide_password: bool = False,
                 max_concurrent_transmissions: int = MAX_CONCURRENT_TRANSMISSIONS,
                 COMMUNICATOR: ConsoleCommunicator = ConsoleCommunicator()
                 ):
        super().__init__(name,
                         api_id,
                         api_hash,
                         app_version,
                         device_model,
                         system_version,
                         lang_code,
                         ipv6,
                         proxy,
                         test_mode,
                         bot_token,
                         session_string,
                         in_memory,
                         phone_number,
                         phone_code,
                         password,
                         workers,
                         workdir,
                         plugins,
                         parse_mode,
                         no_updates,
                         takeout,
                         sleep_threshold,
                         hide_password,
                         max_concurrent_transmissions)
        self.COMMUNICATOR = COMMUNICATOR

    async def authorize(self) -> User:
        if self.bot_token:
            return await self.sign_in_bot(self.bot_token)

        print(f"Welcome to Pyrogram (version {__version__})")
        print(f"Pyrogram is free software and comes with ABSOLUTELY NO WARRANTY. Licensed\n"
              f"under the terms of the {__license__}.\n")

        while True:
            try:
                if not self.phone_number:
                    while True:
                        value = await self.COMMUNICATOR.enter_phone_number()

                        if not value:
                            continue

                        confirm = await self.COMMUNICATOR.confirm()

                        if confirm == "y":
                            break

                    if ":" in value:
                        self.bot_token = value
                        return await self.sign_in_bot(value)
                    else:
                        self.phone_number = value

                sent_code = await self.send_code(self.phone_number)
            except BadRequest as e:
                print(e.MESSAGE)
                self.phone_number = None
                self.bot_token = None
            else:
                break

        sent_code_descriptions = {
            enums.SentCodeType.APP: "Telegram app",
            enums.SentCodeType.SMS: "SMS",
            enums.SentCodeType.CALL: "phone call",
            enums.SentCodeType.FLASH_CALL: "phone flash call",
            enums.SentCodeType.FRAGMENT_SMS: "Fragment SMS",
            enums.SentCodeType.EMAIL_CODE: "email code"
        }

        print(f"The confirmation code has been sent via {sent_code_descriptions[sent_code.type]}")

        while True:
            if not self.phone_code:
                self.phone_code = await self.COMMUNICATOR.get_code()

            try:
                signed_in = await self.sign_in(self.phone_number, sent_code.phone_code_hash, self.phone_code)
            except BadRequest as e:
                print(e.MESSAGE)
                self.phone_code = None
            except SessionPasswordNeeded as e:
                print(e.MESSAGE)

                while True:
                    print("Password hint: {}".format(await self.get_password_hint()))

                    if not self.password:
                        self.password = await self.COMMUNICATOR.enter_password()

                    try:
                        if not self.password:
                            confirm = await self.COMMUNICATOR.confirm()

                            if confirm == "y":
                                email_pattern = await self.send_recovery_code()
                                print(f"The recovery code has been sent to {email_pattern}")

                                while True:
                                    recovery_code = await self.COMMUNICATOR.recovery_code()

                                    try:
                                        return await self.recover_password(recovery_code)
                                    except BadRequest as e:
                                        print(e.MESSAGE)
                                    except Exception as e:
                                        log.exception(e)
                                        raise
                            else:
                                self.password = None
                        else:
                            return await self.check_password(self.password)
                    except BadRequest as e:
                        print(e.MESSAGE)
                        self.password = None
            else:
                break

        if isinstance(signed_in, User):
            return signed_in

        while True:
            first_name = await self.COMMUNICATOR.first_name()
            last_name = await self.COMMUNICATOR.last_name()

            try:
                signed_up = await self.sign_up(
                    self.phone_number,
                    sent_code.phone_code_hash,
                    first_name,
                    last_name
                )
            except BadRequest as e:
                print(e.MESSAGE)
            else:
                break

        if isinstance(signed_in, TermsOfService):
            print("\n" + signed_in.text + "\n")
            await self.accept_terms_of_service(signed_in.id)

        return signed_up
