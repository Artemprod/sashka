#
# from src.dispatcher.communicators.reggestry import CommunicatorRegistryBase
#
#
#
# class Dispatcher:
#
#     def __init__(self, manager: Manager):
#         self.manager = manager
#         self.communicators = CommunicatorRegistryBase.get_registry()
#
#     async def authorize(self, source):
#         communicator = self.communicators[source]
#         await self.manager.authorize(communicator=communicator)
#
#     async def run_app(self, source):
#         communicator = self.communicators[source]
#         await self.manager.run(communicator=communicator)
#






