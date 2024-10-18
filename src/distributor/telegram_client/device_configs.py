from dataclasses import dataclass


@dataclass
class DeviceInfo:
    app_version: str
    device_model: str
    system_version: str


# Экземпляры для разных моделей
iPhoneX = DeviceInfo(app_version="1.0.0", device_model="iPhone X", system_version="iOS 13.3")
iPhone11 = DeviceInfo(app_version="1.1.0", device_model="iPhone 11", system_version="iOS 14.0")
iPhone12Pro = DeviceInfo(app_version="1.2.0", device_model="iPhone 12 Pro", system_version="iOS 14.7")
iPhoneSE2ndGen = DeviceInfo(app_version="1.3.0", device_model="iPhone SE (2nd generation)", system_version="iOS 13.6")
iPhone13 = DeviceInfo(app_version="1.4.0", device_model="iPhone 13", system_version="iOS 15.1")
SamsungGalaxyS21 = DeviceInfo(app_version="2.0.0", device_model="Samsung Galaxy S21", system_version="Android 11")
SamsungGalaxyNote20 = DeviceInfo(app_version="2.1.0", device_model="Samsung Galaxy Note 20",
                                 system_version="Android 10")
GooglePixel5 = DeviceInfo(app_version="2.2.0", device_model="Google Pixel 5", system_version="Android 12")
OnePlus9 = DeviceInfo(app_version="2.3.0", device_model="OnePlus 9", system_version="Android 11")
HuaweiP40Pro = DeviceInfo(app_version="2.4.0", device_model="Huawei P40 Pro", system_version="Android 10")
XiaomiMi11 = DeviceInfo(app_version="3.0.0", device_model="Xiaomi Mi 11", system_version="Android 11")
OppoFindX3Pro = DeviceInfo(app_version="3.1.0", device_model="Oppo Find X3 Pro", system_version="Android 12")
SonyXperia1III = DeviceInfo(app_version="3.2.0", device_model="Sony Xperia 1 III", system_version="Android 11")
iPhone8 = DeviceInfo(app_version="3.3.0", device_model="iPhone 8", system_version="iOS 12.5")
iPhone7 = DeviceInfo(app_version="3.4.0", device_model="iPhone 7", system_version="iOS 13.6")

# Список устройств для удобного доступа
devices = [
    iPhoneX, iPhone11, iPhone12Pro, iPhoneSE2ndGen, iPhone13,
    SamsungGalaxyS21, SamsungGalaxyNote20, GooglePixel5, OnePlus9,
    HuaweiP40Pro, XiaomiMi11, OppoFindX3Pro, SonyXperia1III, iPhone8, iPhone7
]

if __name__ == '__main__':

    # Пример доступа к данным
    for device in devices:
        print(device)
