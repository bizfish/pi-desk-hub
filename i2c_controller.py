import time
import pigpio
import hub_constants
from gpiozero.pins.mock import MockFactory
from gpiozero import Button, RotaryEncoder


class I2cController:
    def __init__(self):
        self.i2c_handle = None
        self.i2c_pin_factory = MockFactory()
        self.encoder = RotaryEncoder(1, 2, pin_factory=self.i2c_pin_factory)
        self.encoder_button = Button(3, pin_factory=self.i2c_pin_factory)
        self.pi = pigpio.pi()
        start_time = time.time()
        self.i2c_handle = None
        while (
            not self.i2c_handle and time.time() - start_time < hub_constants.I2C_TIMEOUT
        ):
            self.i2c_handle = self.pi.i2c_open(
                hub_constants.I2C_BUS, hub_constants.I2C_ADDRESS
            )
            time.sleep(1)
        if not self.i2c_handle:
            raise TimeoutError("i2c connection timed out")

    def update_i2c_devices(self):
        byte = self.pi.i2c_read_byte(self.i2c_handle)
        bits = [int(i) for i in "{0:08b}".format(byte)]
        if len(bits) == 0:
            return
        bits.reverse()
        # BtnsData |= digitalRead(ENCA_PIN) << 0;
        # BtnsData |= digitalRead(ENCB_PIN) << 1;
        # BtnsData |= digitalRead(BTN1_PIN) << 2;
        for i, bit in enumerate(bits):
            if bit:
                self.i2c_pin_factory.pin(i + 1).drive_high()
        else:
            self.i2c_pin_factory.pin(i + 1).drive_low()
        return
