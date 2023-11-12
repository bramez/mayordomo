import threading
import time
import sys

from datetime import datetime
import logging

import schedule

from gpiozero import Button, DigitalOutputDevice

TIME_INTERVAL = 2
CALDERA = 'caldera'
JORDI = 'jordi'
PAPA = 'papa'
NURI = 'nuri'
ACS = 'acs'

UNKNOWN = '??'

logger = logging.getLogger("mayordomo")
hdlr = logging.FileHandler("/var/log/mayordomo.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

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


class MayordomoServices:
    def __init__(self):

        print("Init mayordomo services")

        self.config = dict()

        self.config['config_temperature_min_enable_calefaccion'] = 42
        self.config['config_temperature_min_acs'] = 43
        self.config['config_temperature_max_acs'] = 49
        self.cached_nuri_temperature = 10
        self.cached_papa_temperature = 10
        self.cached_jordi_temperature = 10

        self.cached_acs_temperature = 90.1

        self.acs_soft_status = False
        self.caldera_soft_status = False
        self.calefaccion_jordi_soft_status = False
        self.calefaccion_papa_soft_status = False
        self.calefaccion_nuri_soft_status = False
        self.min_temperature_jordi = 21.5
        self.max_temperature_jordi = 22

        self.min_temperature_nuri = 21
        self.max_temperature_nuri = 22

        self.min_temperature_papa = 21
        self.max_temperature_papa = 22

        self.is_jordi_saving = False
        self.init_saving_timestamp_for_jordi = datetime.now()
        self.end_saving_timestamp_for_jordi = datetime.now()

        self.jordi_button = Button("GPIO12", pull_up=False)
        self.nuri_button = Button("GPIO16", pull_up=False)
        self.papa_button = Button("GPIO20", pull_up=False)
        self.acs_button = Button("GPIO21", pull_up=False)

        self.acs_button.when_activated = self.toggle_acs_state
        self.jordi_button.when_activated = self.toggle_calefaccion_jordi_state
        self.nuri_button.when_activated = self.toggle_calefaccion_nuri_state
        self.papa_button.when_activated = self.toggle_calefaccion_papa_state

        self.counter = 0
        self._led_status = True

        # GPIO caldera_button set up as an input, pu datetime.now()

        self.jordi_rele = DigitalOutputDevice("GPIO23")
        self.nuri_rele = DigitalOutputDevice("GPIO24")
        self.papa_rele = DigitalOutputDevice("GPIO25")
        self.acs_rele = DigitalOutputDevice("GPIO08")
        self.caldera_rele = DigitalOutputDevice("GPIO07")

        schedule.every().day.at("23:00").do(self.switch_off_calefaccion_jordi)
        schedule.every().day.at("23:00").do(self.switch_off_calefaccion_papa)
        schedule.every().day.at("23:00").do(self.switch_off_calefaccion_nuri)
        schedule.every().day.at("23:00").do(self.scheduled_switch_off_caldera)

        # schedule.every().day.at("14:30").do(self.switch_on_calefaccion_papa)
        # schedule.every().day.at("15:30").do(self.switch_off_calefaccion_papa)
        # schedule.every().day.at("18:00").do(self.switch_on_calefaccion_papa)
        # schedule.every().day.at("19:30").do(self.switch_on_calefaccion_jordi)

        schedule.every(30).seconds.do(self.save_temperature)
        schedule.every(10).seconds.do(self.get_acs_temperature)
        schedule.every(30).seconds.do(self.get_jordi_temperature)

        schedule.every(20).seconds.do(self.update_temperatures)

        # self.display = SevenSegment(address=0x70)
        #

        try:
            '''
            On the Raspberry Pi, you will need to add dtoverlay=w1-gpio" (for regular connection)
            or dtoverlay=w1-gpio,pullup="y" (for parasitic connection) to your /boot/config.txt.
            The default data pin is GPIO4 (RaspPi connector pin 7), but that can be changed from 4 
            to x with dtoverlay=w1-gpio,gpiopin=x.
            '''

            self.sensor = W1ThermSensor()
            self.get_acs_temperature()
            self.get_jordi_temperature()
            self.get_nuri_temperature()
        # except KernelModuleLoadError:
        #     logger.error("Kernel Module Load Error")
        #     sys.exit()
        except Exception as e:
            logger.error("No sensor found error. Please, check temperature sensor.")
            self.sensor = W1ThermSensorMock()

            self.sensor.set_temperature(25)
            logger.error(str(e))

        return

    def save_temperature(self):
        print("saving temperature")

    def switch_off_everything_scheduled(self):
        self.switch_off_all_calefaccion()
        self.switch_off_caldera()

    def scheduled_switch_off_caldera(self):
        logger.info("scheduled caldera off ")
        # self.switch_off_all_calefaccion()
        self.switch_off_caldera()

    def switch_off_caldera(self):
        self.caldera_soft_status = False
        self.caldera_rele.off()
        self.acs_rele.off()

    def switch_off_calefaccion_jordi(self):
        self.calefaccion_jordi_soft_status = False
        self.jordi_rele.off()

    def switch_off_calefaccion_nuri(self):
        self.calefaccion_nuri_soft_status = False
        self.nuri_rele.off()

    def switch_off_calefaccion_papa(self):
        self.calefaccion_papa_soft_status = False
        self.papa_rele.off()

    def switch_on_caldera(self):
        self.caldera_soft_status = True
        self.caldera_rele.on()

    def switch_on_acs(self):
        self.acs_soft_status = True
        self.acs_rele.on()

    def switch_off_all_calefaccion(self):
        self.switch_off_calefaccion_jordi()
        self.switch_off_calefaccion_nuri()
        self.switch_off_calefaccion_papa()

    def switch_on_calefaccion_jordi(self):
        self.calefaccion_jordi_soft_status = True

    def switch_on_calefaccion_papa(self):
        self.calefaccion_papa_soft_status = True

    def switch_on_calefaccion_nuri(self):
        self.calefaccion_nuri_soft_status = True

    def switch_off_everything(self):
        self.switch_off_everything_scheduled()

    def get_all_devices(self):
        devices = list()
        devices.append(self.get_device(ACS))
        devices.append(self.get_device(JORDI))
        devices.append(self.get_device(NURI))
        devices.append(self.get_device(PAPA))
        return devices

    def get_device(self, name):
        device = dict()
        device["name"] = name

        device["temperature"] = self.get_cached_temperature_for(name)
        device["status"] = self.get_soft_status_for(name)
        device["min_temperature"] = self.min_temperature_jordi
        device["max_temperature"] = self.max_temperature_jordi
        device["actual_status"] = self.get_relay_status_for(name)

        return device

    def get_papa_temperature(self):
        return self.get_temperature_for(PAPA)

    def get_jordi_temperature(self):
        return self.get_temperature_for(JORDI)

    def get_nuri_temperature(self):
        return self.get_temperature_for(NURI)

    def get_acs_temperature(self):
        temperature_in_celsius = self.sensor.get_temperature()
        temperature_in_celsius = round(temperature_in_celsius, 2)
        self.cached_acs_temperature = temperature_in_celsius
        return temperature_in_celsius

    def get_temperature_for(self, name):
        temperature = 0
        if name == ACS:
            temperature = self.cached_acs_temperature
        elif name == JORDI:
            self.cached_jordi_temperature = temperature
        elif name == NURI:
            self.cached_nuri_temperature = temperature
        elif name == PAPA:
            self.cached_papa_temperature = temperature

        return temperature

    def get_cached_temperature_for(self, name):
        if name == ACS:
            temperature = self.cached_acs_temperature
        elif name == JORDI:
            temperature = self.cached_jordi_temperature
        elif name == NURI:
            temperature = self.cached_nuri_temperature
        elif name == PAPA:
            temperature = self.cached_papa_temperature
        else:
            temperature = 10

        return temperature

    def print_devices_status(self):
        devices = self.get_all_devices()
        for device in devices:
            logger.info(("name=%s | temperature=%s | status=%s | actual_status=%s " % (
                device["name"], device["temperature"], device["status"], device["actual_status"])))

    def get_relay_status_for(self, name):
        if name == CALDERA:
            return self.caldera_rele.value
        elif name == JORDI:
            return self.jordi_rele.value
        elif name == PAPA:
            return self.papa_rele.value
        elif name == NURI:
            return self.nuri_rele.value
        elif name == ACS:
            return self.acs_rele.value

    def get_soft_status_for(self, name):
        if name == CALDERA:
            status = self.get_caldera_state()
        elif name == JORDI:
            status = self.get_calefaccion_jordi_state()
        elif name == PAPA:
            status = self.get_calefaccion_papa_state()
        elif name == NURI:
            status = self.get_calefaccion_nuri_state()
        elif name == ACS:
            status = self.get_acs_state()
        else:
            status = UNKNOWN
        return status

    def get_caldera_state(self):
        return self.caldera_soft_status

    def get_calefaccion_jordi_state(self):
        return self.calefaccion_jordi_soft_status

    def get_calefaccion_papa_state(self):
        return self.calefaccion_papa_soft_status

    def get_calefaccion_nuri_state(self):
        return self.calefaccion_nuri_soft_status

    def get_acs_state(self):
        return self.acs_soft_status

    def update_device(self, device):
        logger.info("Updating device '%s'. old_status=%s | new_status=%s" % (
            device['name'], self.get_soft_status_for(device['name']), device['status']))

        if device['name'] == ACS:
            self.acs_soft_status = device['status']
        if device['name'] == JORDI:
            self.calefaccion_jordi_soft_status = device['status']
        if device['name'] == PAPA:
            self.calefaccion_papa_soft_status = device['status']
        if device['name'] == NURI:
            self.calefaccion_nuri_soft_status = device['status']

        return self.get_device(device['name'])

    def toggle_acs_state(self):
        self.acs_soft_status = not self.acs_soft_status

    def toggle_calefaccion_jordi_state(self):
        time.sleep(0.1)
        self.calefaccion_jordi_soft_status = not self.calefaccion_jordi_soft_status

    def toggle_calefaccion_nuri_state(self):
        time.sleep(0.1)
        self.calefaccion_nuri_soft_status = not self.calefaccion_nuri_soft_status

    def toggle_calefaccion_papa_state(self):
        time.sleep(0.1)
        self.calefaccion_papa_soft_status = not self.calefaccion_papa_soft_status

    def write_display(self, value):
        value_as_string = str(round(value, 2))
        '''logger.debug(("value as string '%s'" % value_as_string))'''
        for position in range(len(value_as_string)):
            if position != 2:
                '''logger.debug(("printing '%s' in position '%d'" % (value_as_string[position], position)))'''
                # self.display.writeDigit(position, int(value_as_string[position]), position == 1)

    def control_temperature_jordi(self):
        self.control_temperature(self.jordi_rele, self.min_temperature_jordi, self.max_temperature_jordi, self.cached_jordi_temperature, self.calefaccion_jordi_soft_status)

    def control_temperature_nuri(self):
        self.control_temperature(self.nuri_rele, self.min_temperature_nuri, self.max_temperature_nuri, self.cached_nuri_temperature, self.calefaccion_nuri_soft_status)

    def control_temperature_papa(self):
        self.control_temperature(self.papa_rele, self.min_temperature_papa, self.max_temperature_papa, self.cached_papa_temperature, self.calefaccion_papa_soft_status)

    def control_temperature(self, rele, min_temperature, max_temperature, cached_temperature, soft_status):
        if soft_status:
            if cached_temperature < min_temperature:
                rele.on()
            elif cached_temperature > max_temperature:
                rele.off()
        else:
            rele.off()

    def update_temperatures(self):
        print("Updating temperatures")
        self.cached_jordi_temperature = self.get_jordi_temperature()
        self.cached_nuri_temperature = self.get_nuri_temperature()
        self.cached_acs_temperature = self.get_acs_temperature()
        logger.info("jordi temperature: '%s'", self.cached_jordi_temperature)
        logger.info("nuri temperature: '%s'", self.cached_nuri_temperature)
        logger.info("acs temperature: '%s'", self.cached_acs_temperature)

    def start(self):
        d = threading.Thread(target=worker, name='Daemon', args=(self,))
        d.setDaemon(True)
        d.start()

    def is_acs_under_min_temperature(self):
        return self.cached_acs_temperature < self.config['config_temperature_min_acs']

    def is_acs_upper_max_temperature(self):
        return self.cached_acs_temperature > self.config['config_temperature_max_acs']

    def is_acs_enabled(self):
        return self.get_soft_status_for(ACS)

    def is_acs_under_min_priority_temperature(self):
        return self.cached_acs_temperature < self.config['config_temperature_min_enable_calefaccion']

    def any_calefaccion_on(self):
        return self.calefaccion_jordi_soft_status or self.calefaccion_nuri_soft_status or self.calefaccion_papa_soft_status


def worker(mayordomo):
    while True:
        try:
            if not mayordomo.any_calefaccion_on() and not mayordomo.acs_soft_status:
                mayordomo.switch_off_everything()
            else:
                if mayordomo.acs_soft_status:
                    mayordomo.switch_on_acs()

                    if mayordomo.is_acs_under_min_priority_temperature():
                        mayordomo.jordi_rele.off()
                        mayordomo.nuri_rele.off()
                        mayordomo.papa_rele.off()

                if mayordomo.is_acs_upper_max_temperature():
                    mayordomo.acs_rele.off()
                    mayordomo.caldera_rele.off()
                elif mayordomo.is_acs_under_min_temperature():
                    mayordomo.acs_rele.on()
                    mayordomo.caldera_rele.on()
                else:
                    mayordomo.caldera_rele.on()

                # No need to control anything, as there is no thermostat
                mayordomo.control_temperature_jordi()
                mayordomo.control_temperature_nuri()
                mayordomo.control_temperature_papa()

            # mayordomo.write_display(mayordomo.cached_acs_temperature)
            # BRAM: I disable all relays in summer! please in Winter enable them!
            mayordomo.jordi_rele.off()
            mayordomo.nuri_rele.off()
            mayordomo.papa_rele.off()
            schedule.run_pending()
        except Exception as err:
            logging.error(err)
