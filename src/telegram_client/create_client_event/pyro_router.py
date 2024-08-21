from typing import Callable
from logging import getLogger
import inspect
from functools import wraps
from pyrogram import handlers, Client
from pyrogram.types import Update


class Router:
    def __init__(self, name):
        self.__name = name
        self.__logger = getLogger(name)
        self.__handlers = []
        self.__dp_kwargs = {}
        self.__router_filters = None

    def __check_filters(self, filters):
        match self.__router_filters:
            case None:
                return filters
            case _:
                match filters:
                    case None:
                        return self.__router_filters
                    case _:
                        return self.__router_filters & filters

    @property
    def logger(self):
        return self.__logger

    @property
    def name(self):
        return self.__name

    @property
    def dp_kwargs(self):
        return self.__dp_kwargs

    @dp_kwargs.setter
    def dp_kwargs(self, kwargs: dict):
        self.__dp_kwargs = kwargs

    def set_filter(self, user_filter):
        self.__router_filters = user_filter

    @staticmethod
    def prepare_kwargs(func: Callable, kwargs: dict) -> dict:
        spec = inspect.getfullargspec(func)

        if spec.varkw:
            return kwargs

        return {
            k: v
            for k, v in kwargs.items()
            if k in spec.args or k in spec.kwonlyargs
        }

    def inject(self, fn) -> Callable:
        @wraps(fn)
        async def wrapper(client: Client, update: Update):
            kwargs = self.dp_kwargs
            kwargs.update({'client': client, 'logger': self.logger})

            return await fn(update, **self.prepare_kwargs(fn, kwargs))

        return wrapper

    def message(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.MessageHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def edited_message(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.EditedMessageHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def deleted_messages(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.DeletedMessagesHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def callback_query(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.CallbackQueryHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )
            return func

        return decorator

    def inline_query(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.InlineQueryHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def chosen_inline_result(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.ChosenInlineResultHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def chat_member_updated(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.ChatMemberUpdatedHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def user_status(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.UserStatusHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def poll(self, filters=None, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (
                    handlers.PollHandler(
                        func, self.__check_filters(filters)
                    ),
                    group,
                )
            )

            return func

        return decorator

    def disconnect(self):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(handlers.DisconnectHandler(func))

            return func

        return decorator

    def raw_update(self, group=0):
        def decorator(func: Callable) -> Callable:
            func = self.inject(func)
            self.__handlers.append(
                (handlers.RawUpdateHandler(func), group)
            )

            return func

        return decorator

    def get_handlers(self, exclude_handlers: set = None):
        if exclude_handlers is None:
            return self.__handlers
        else:
            return [
                handler
                for handler in self.__handlers
                if handler[0].callback.__name__
                not in exclude_handlers
            ]