from telethon import events


# class CustomFilter(events.NewMessage):
#     def __init__(self, func=None, **kwargs):
#         super().__init__(**kwargs)
#         self.func = func  # Функция-фильтр
#
#     async def filter(self, event):
#         # Применяем кастомную функцию-фильтр
#         if self.func and await self.func(event):
#             return True
#         return False