
# #TODO Все сообщения из отсюда попадают в очередь и уходят в обработчик сообщений от туда они должны распределятся по рабочим
#
# @answ_router.message(filters.create(in_research))
# async def ai_answer(message: Message, **kwargs):
#     print(message)
#     stop_word = "STOP"
#     client: Client = kwargs['client']
#     response = await comunicator.send_response(text=message.text, assistant=assistant_aggressive)
#     if stop_word in response:
#         await change_user_status(user_id=message.from_user.id)
#         response.replace(stop_word, '')
#     await client.send_message(message.from_user.id, text=response)
#
#
# @answ_router.message(not filters.create(in_research))
# async def send_to_disterbuter(message: Message, **kwargs):
#     print(message)
#     client: Client = kwargs['client']
#     await client.send_message(message.from_user.id, text="Ты не в иследовании")
#


# @answ_router.message(not in_research)
# async def send_to_disterbuter(message: Message, **kwargs):
#     # кладем в очередь для отправки
#     data = {'client': kwargs['client'].name, 'message':str(message)}
#     async with NatsBroker() as broker:
#         await broker.publish(message=data, subject="new_message")

# @answ_router.message(hello_filter)
# async def hello(message: Message, **kwargs):
#     client: Client = kwargs['client']
#     await client.send_message(message.from_user.id, 'и тебе тоже привет')
