import time
import pigpio
import hub_constants
from gpiozero.pins.mock import MockFactory
from gpiozero import Button, RotaryEncoder


class I2cController:
    def __init__(self):
        self.handle = None
        self.pin_factory = MockFactory()
        self.pins = []
        for i in range(1, 8):
            self.pins.append(self.pin_factory.pin(i))
        self.push_button1 = Button(1, pin_factory=self.pin_factory)
        self.on_air_button = Button(2, pin_factory=self.pin_factory)
        self.pi = pigpio.pi()
        start_time = time.time()
        self.handle = None
        while not self.handle and time.time() - start_time < hub_constants.I2C_TIMEOUT:
            self.handle = self.pi.i2c_open(
                hub_constants.I2C_BUS, hub_constants.I2C_ADDRESS
            )
            time.sleep(1)
        if not self.handle:
            raise TimeoutError("i2c connection timed out")

    def update_i2c_devices(self):
        byte = self.pi.i2c_read_byte(self.handle)
        bits = [int(i) for i in "{0:08b}".format(byte)]
        if len(bits) == 0:
            return
        bits.reverse()
        for i, bit in enumerate(bits):
            if bit:
                self.pin_factory.pin(i + 1).drive_low()
            else:
                self.pin_factory.pin(i + 1).drive_high()
        return
