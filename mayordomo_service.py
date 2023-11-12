import logging
import threading
import time

import schedule

from mayordomo_device import MyDevice

logger = logging.getLogger("mayordomo")

TIME_INTERVAL = 2
CALDERA = 'caldera'
JORDI = 'jordi'
PAPA = 'papa'
NURI = 'nuri'
ACS = 'acs'

from adafruit_ht16k33 import segments
import board
import busio

DEVICES = [
    {
        "name": CALDERA,
        "rele_gpio": "GPIO23",
        "led_gpio": "GPIO17",
        "button_gpio": "GPIO12"
    },
    {
        "name": ACS,
        "rele_gpio": "GPIO24",
        "led_gpio": "GPIO27",
        "button_gpio": "GPIO16"
    },
    {
        "name": PAPA,
        "rele_gpio": "GPIO25",
        "led_gpio": "GPIO22",
        "button_gpio": "GPIO20"
    },
    {
        "name": NURI,
        "rele_gpio": "GPIO8",
        "led_gpio": "GPIO10",
        "button_gpio": "GPIO21"
    },
    {
        "name": JORDI,
        "rele_gpio": "GPIO7",

    },
]

try:
    from w1thermsensor.core import NoSensorFoundError
    from w1thermsensor import W1ThermSensor, KernelModuleLoadError
except Exception as e:
    logger.error(e)


class W1ThermSensorMock:
    def __init__(self):
        self._temperature = None
        logger.info("Using Mock for temperature sensor")

    def get_temperature(self):
        return self._temperature

    def set_temperature(self, temperature):
        self._temperature = temperature


class MayordomoService:
    def __init__(self):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the LED segment class.
        # This creates a 7 segment 4 character display:
        display = segments.Seg7x4(i2c)
        display.brightness = 0.3

        display.print("Guiu")

        self.devices = dict()

        for device in DEVICES:
            name = device['name']
            rele_gpio = device['rele_gpio']
            led_gpio = device.get('led_gpio', None)
            button_gpio = device.get('button_gpio', None)

            self.devices[name] = MyDevice(name, rele_gpio, led_gpio, button_gpio)

            schedule.every().day.at("23:00:00").do(self.devices[name].off)

            self.devices[name].register(self)

        self.config = dict()

        self.config['config_temperature_min_enable_calefaccion'] = 42
        self.config['config_temperature_min_acs'] = 43
        self.config['config_temperature_max_acs'] = 49

        try:
            '''
            On the Raspberry Pi, you will need to add dtoverlay=w1-gpio" (for regular connection)
            or dtoverlay=w1-gpio,pullup="y" (for parasitic connection) to your /boot/config.txt.
            The default data pin is GPIO4 (RaspPi connector pin 7), but that can be changed from 4 
            to x with dtoverlay=w1-gpio,gpiopin=x.
            '''

            self.sensor = W1ThermSensor()
            self.devices[ACS].temperature = round(self.sensor.get_temperature(), 1)

        # except KernelModuleLoadError:
        #     logger.error("Kernel Module Load Error")
        #     sys.exit()
        except Exception as e:
            logger.error("No sensor found error. Please, check temperature sensor.")
            self.sensor = W1ThermSensorMock()

            self.sensor.set_temperature(25)
            logger.error(str(e))

    def switch_off_all_devices(self):
        for device_name in self.devices:
            self.devices[device_name].off()

    def switch_on_all_devices(self):
        for device_name in self.devices:
            self.devices[device_name].on()

    def get_serialized_devices(self):
        serialized_devices = dict()

        for device in self.devices.values():
            name, serialized_device = device.serialize()
            serialized_devices[name] = serialized_device
        logger.info(serialized_devices)
        return serialized_devices

    def switch_off_rele(self, name):
        self.devices[name].off()

    def switch_on_rele(self, name):
        self.devices[name].on()

    def any_calefaccion_on(self):
        return any(self.devices[device].soft_status for device in (JORDI, NURI, PAPA))

    def is_acs_under_min_priority_temperature(self):
        acs_under_min_priority=  self.devices[ACS].temperature < self.config['config_temperature_min_enable_calefaccion']
        logger.debug("ACS is under min priority: " + str(acs_under_min_priority))
        return acs_under_min_priority

    def is_acs_under_min_temperature(self):
        acs_under_min_temperature = self.devices[ACS].temperature < self.config['config_temperature_min_acs']
        logger.debug("ACS is under min temperature: " + str(acs_under_min_temperature))
        return acs_under_min_temperature

    def is_acs_upper_max_temperature(self):
        acs_upper_max_temperature = self.devices[ACS].temperature > self.config['config_temperature_max_acs']
        logger.debug("ACS is over max temperature: " + str(acs_upper_max_temperature))
        return acs_upper_max_temperature

    def start(self):
        d = threading.Thread(target=worker, name='Daemon', args=(self,))
        d.setDaemon(True)
        d.start()

    def dispatch(self):
        # for device in self.devices.values():
        #     device.print_status()

        if self.any_calefaccion_on():
            self.devices[CALDERA].calculated_status = True

            self.devices[JORDI].calculated_status = self.devices[JORDI].control()
            self.devices[NURI].calculated_status = self.devices[NURI].control()
            self.devices[PAPA].calculated_status = self.devices[PAPA].control()

        if not self.any_calefaccion_on() and not self.devices[ACS].soft_status:
            self.devices[JORDI].calculated_status = False
            self.devices[NURI].calculated_status = False
            self.devices[PAPA].calculated_status = False
            self.devices[ACS].calculated_status = False
            self.devices[CALDERA].calculated_status = False

            # Queremos agua caliente
        elif self.devices[ACS].soft_status:
            self.devices[ACS].calculated_status = True
            self.devices[CALDERA].calculated_status = True
            # la Temperatura del ACS es menor que la minima deseada.
            # Debemos apagar los reles de las calefacciones, pero el soft status debe mantenerse
            if self.is_acs_under_min_priority_temperature():
                self.devices[JORDI].calculated_status = False
                self.devices[NURI].calculated_status = False
                self.devices[PAPA].calculated_status = False
            if self.is_acs_upper_max_temperature():
                # Apagamos ACS ya que hemos llegado al máximo de temperatura
                self.devices[ACS].calculated_status = False

                # Apagamos caldera tambien solo en el caso de que no haya alguien solicitando calefaccion
                if not self.any_calefaccion_on():
                    self.devices[CALDERA].calculated_status = False

            if self.is_acs_under_min_temperature():
                self.devices[ACS].calculated_status = True
                self.devices[CALDERA].calculated_status = True





        # apply the calculated result
        for device_name in self.devices:
            self.devices[device_name].apply()


def worker(mayordomo):
    while True:
        try:
            logger.info("Triggering scheduler")
            logger.info("Temperature ACS: {}".format(str(mayordomo.sensor.get_temperature())))
            schedule.run_pending()
            mayordomo.devices[ACS].temperature = round(mayordomo.sensor.get_temperature(), 1)
            # logger.info("Temperature ACS: {}".format(mayordomo.devices[ACS].temperature))
            mayordomo.dispatch()

            time.sleep(10)
        except Exception as e:
            logger.error(e)