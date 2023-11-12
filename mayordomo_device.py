from gpiozero import DigitalOutputDevice, LED, Button
import logging
logger = logging.getLogger("mayordomo")

class MyDevice:
    def __init__(self, name, rele_gpio, led_gpio=None, button_gpio=None):
        self.controller = None
        self.name = name
        self.rele = DigitalOutputDevice(rele_gpio)
        self.calculated_status = False
        self.led = LED(led_gpio) if led_gpio else None
        if button_gpio:
            self.button = Button(button_gpio, hold_time=0.5, bounce_time=0.1)
            self.button.when_activated = self.toggle
        self.counter = 0
        self.temperature = 15

        self.soft_status = False

    def toggle(self):
        self.soft_status = not self.soft_status
        if self.controller:
            logger.info("Device [{}] dispatched an event TOGGLE. The soft_status is {}".format(self.name, self.soft_status))
            self.controller.dispatch()
        else:
            self.rele.toggle()

    def on(self):
        self.soft_status = True
        if self.controller:
            logger.info("Device [{}] dispatched an event ON. The soft_status is {}".format(self.name, self.soft_status))
            self.controller.dispatch()
        else:
            self.force_on()

    def off(self):
        self.soft_status = False
        if self.controller:
            logger.info("Device [{}] dispatched an event OFF. The soft_status is {}".format(self.name, self.soft_status))
            self.controller.dispatch()
        else:
            self.force_off()

    def register(self, controller):
        self.controller = controller

    def force_on(self):
        self.rele.on()

    def force_off(self):
        self.rele.off()

    def rele_status(self):
        return bool(self.rele.value)

    def led_status(self):
        return bool(self.led.value)

    def serialize(self):
        device = dict()

        device["rele_status"] = self.rele_status()
        device["soft_status"] = self.soft_status

        if self.led:
            device["led"] = self.led.value

        device["temperature"] = self.temperature

        return self.name, device

    def control(self):
        # if self.temperature_sensor is None:
        #     return self.soft_status
        #
        # if self.temperature < self.min_temperature:
        #     self.rele_status = True
        # elif self.temperature > self.max_temperature:
        #     self.rele_status = False
        return self.soft_status

    def apply(self):
        logger.info("Device [{}] calculated status is {}. Applying it".format(self.name, self.calculated_status))
        self.force_on() if self.calculated_status else self.force_off()

    def print_status(self):
        logger.info("Device [{}] status:\n\tsoft_status:{}\n\trele_status:{}\n\tcalculated_status:{}\n\t".format(self.name, self.soft_status, self.rele_status(), self.calculated_status))
