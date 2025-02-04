from faststream import Depends
from faststream.nats import NatsBroker
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger

from configs.nats_queues import nats_distributor_settings, nast_base_settings
from src.distributor.app.schemas.parse import Datas
from src.distributor.app.schemas.response import ErrorResponse
from src.distributor.app.schemas.response import ResponseModel
from src.distributor.app.schemas.response import SuccessResponse
from src.distributor.app.utils.parse import derive_data
from src.distributor.app.utils.parse import gather_information
from src.distributor.app.utils.parse import make_request

router = NatsRouter()
broker = NatsBroker(nast_base_settings.nats_server_url)


@router.subscriber(subject=nats_distributor_settings.parser.base_info.subject)
async def parse_user_information(msg: "NatsMessage", data: Datas = Depends(derive_data)):
    logger.info("Подключаюсь к брокеру...")
    await broker.connect()
    logger.info("Подключение установлено")
    try:
        user_data = await make_request(data=data)
        user_info = await gather_information(user_data)
        response_data: ResponseModel = ResponseModel(response=SuccessResponse(data=user_info))

    except Exception as e:
        logger.error("An error occurred:", e)
        response_data: ResponseModel = ResponseModel(response=ErrorResponse(error_message=str(e)))

    if msg.reply_to:
        logger.info(
            f"Вот такая дата {response_data.model_dump_json()}",
        )

        queue_data = response_data.model_dump_json(indent=3, serialize_as_any=True)
        await broker.publish(message=queue_data, subject=msg.reply_to, reply_to=msg.reply_to)
        await broker.close()
