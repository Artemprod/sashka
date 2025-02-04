from faststream.nats import NatsMessage
from loguru import logger
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.errors.rpcerrorlist import UserDeactivatedBanError

from src.distributor.app.schemas.message import MessageContext
from src.distributor.app.schemas.message import MessageToSendData
from src.distributor.app.schemas.message import UserDTOBase
from src.services.exceptions.telegram_clients import AllClientsBannedError


async def process_message(
        data: MessageToSendData,
        msg: NatsMessage,
        context: MessageContext,
        is_first_message: bool = False
) -> bool:
    await msg.ack()
    logger.info("Sending message...")

    if not data.message:
        logger.warning("There is no message to send, I will not send anything")
        return False

    if is_first_message and await context.client_ban_checker.check_is_account_banned(client=context.client):

        await context.client_ban_checker.start_check_ban(
            client=context.client,
            research_id=context.research_id
        )

        try:
            context.client = await context.telethon_container.get_telethon_client_by_research_id(
                research_id=context.research_id
            )

        except AllClientsBannedError:
            logger.warning(f"All clients banned for research_id: {context.research_id}. Publishing ban on research.")
            await context.client_ban_checker.publisher.publish_ban_on_research(
                research_id=context.research_id
            )
            return False

    msg_data = await send_message(
        user=data.user,
        message=data.message,
        context=context
    )

    if msg_data is None:
        logger.warning("Ошибка в отправке сообщения")
        return False

    logger.info(f"Message sent: {msg_data}")
    return True


async def send_message(
        user: UserDTOBase,
        message: str,
        context: MessageContext
):
    try:
        user_entity = await context.client.get_input_entity(user.tg_user_id)
        return await context.client.send_message(
            entity=user_entity,
            message=message
        )

    except (UserDeactivatedBanError, ChatWriteForbiddenError, PeerFloodError) as e:
        logger.error(f"Аккаунт, скорее всего, заблокирован! Ошибка: {e} ")
        if await context.client_ban_checker.check_is_account_banned(client=context.client):
            logger.info(f"Проверил через бан чекера. Клиент {context.client} имеет бан.")
            await context.client_ban_checker.start_check_ban(
                client=context.client,
                research_id=context.research_id
            )
            return
        logger.warning(f"Проверил через бан чекера. Клиент {context.client} не имеет бан. ")


    except ValueError as e:
        logger.warning(f"Cant send vy ID Trying to send by name. {e}")
        if not user.name:
            logger.warning(f"No username {e}")
        user_entity = await context.client.get_input_entity(user.name)
        return await context.client.send_message(
            entity=user_entity,
            message=message
        )
    except Exception as e:
        logger.warning(f" Faild to send. {e}")
