from enum import Enum


class DataType(Enum):
    CODE = "code"
    RECOVERY = "recovery"
    PHONE = "phone"
    CLOUD_PASSWORD = "cloud_password"
    CONFIRM = "confirm"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"