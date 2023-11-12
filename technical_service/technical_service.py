from gpiozero import DigitalOutputDevice, LED, Button

TIME_INTERVAL = 2
CALDERA = 'caldera'
JORDI = 'jordi'
PAPA = 'papa'
NURI = 'nuri'
ACS = 'acs'

DEVICES = [
    {
        "name": JORDI,
        "rele_gpio": "GPIO23",
        "led_gpio": "GPIO17",
        "button_gpio": ""
    },
    {
        "name": NURI,
        "rele_gpio": "GPIO24",
        "led_gpio": "GPIO27",
        "button_gpio": ""
    },
    {
        "name": PAPA,
        "rele_gpio": "GPIO25",
        "led_gpio": "GPIO22",
        "button_gpio": ""
    },
    {
        "name": ACS,
        "rele_gpio": "GPIO8",
        "led_gpio": "GPIO10",
    },
    {
        "name": CALDERA,
        "rele_gpio": "GPIO7",

    },
]


class MyDevice:
    def __init__(self, name, rele_gpio, led_gpio=None, button_gpio=None):
        self.name = name
        self.rele = DigitalOutputDevice(rele_gpio)

        # if led_gpio:
        #     self.led = LED(led_gpio)
        # else:
        #     self.led = None

        self.led = LED(led_gpio) if led_gpio else None
        self.button = Button(button_gpio) if button_gpio else None

        self.soft_status = False

    def on(self):
        self.rele.on()

    def off(self):
        self.rele.off()

    def rele_status(self):
        return bool(self.rele.value)

    def led_status(self):
        return bool(self.led.value)

    def serialize(self):
        device = dict()
        device["name"] = self.name
        device["rele_status"] = self.rele_status()
        device["soft_status"] = self.soft_status

        if self.led:
            device["led"] = self.led.value

        return device


class TechnicalService:
    def __init__(self):
        self.devices = dict()

        for device in DEVICES:
            name = device['name']
            rele_gpio = device['rele_gpio']
            led_gpio = device.get('led_gpio', None)
            button_gpio = device.get('button_gpio', None)

            self.devices[name] = MyDevice(name, rele_gpio, led_gpio, button_gpio)

    def switch_off_all_devices(self):
        for device_name in self.devices:
            self.devices[device_name].off()

    def switch_on_all_devices(self):
        for device_name in self.devices:
            self.devices[device_name].on()

    def get_serialized_devices(self):
        serialized_devices = list()

        for device in self.devices.values():
            serialized_devices.append(device.serialize())

        return serialized_devices

    def switch_off_rele(self, name):
        self.devices[name].off()

    def switch_on_rele(self, name):
        self.devices[name].on()
