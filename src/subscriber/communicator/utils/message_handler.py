import asyncio

from loguru import logger

from src.distributor.services.s3_manager import s3_manager
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.communicator.request import TranscribeRequestDTO
from src.services.communicator.communicator import TelegramCommunicator


async def handle_incoming_message(
        income_message_data: IncomeUserMessageDTOQueue,
        communicator: TelegramCommunicator
):
    logger.info(f"ЭТО СФОРМИРОВАННОЕ СООБЩЕНИЕ {income_message_data}")
    asyncio.create_task(
        communicator.reply_message(message_object=income_message_data)
    )
    await asyncio.sleep(0.1)


async def process_voice_message(
        income_message_data: IncomeUserMessageDTOQueue,
        communicator: TelegramCommunicator
):
    """Processes incoming audio messages."""
    if income_message_data.s3_object_key is None:
        return

    try:

        s3_file_url, s3_file_data = await s3_manager.get_file_url_and_data(income_message_data.s3_object_key)

        response_data_from_transcribe = await communicator.transcribe_request.get_response(
            datas=TranscribeRequestDTO(
                s3_url=s3_file_url,
                mime_type=s3_file_data.get("ContentType", "..."),
                description="..."
            )
        )

        income_message_data.message += response_data_from_transcribe.text

    except Exception as e:
        logger.warning(f"An error occurred: {e}")

    finally:
        await s3_manager.delete_file(income_message_data.s3_object_key)
