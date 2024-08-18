import time
import pigpio
from gpiozero.pins.mock import MockFactory
from gpiozero import Button
import hub_constants


class I2cController:
    def __init__(self):
        self.handle = None
        self.pin_factory = MockFactory()
        # initialize pins
        self.pins = []
        for i in range(1, 8):
            self.pins.append(self.pin_factory.pin(i))
        # create Devices
        self.devices = {
            "on_air_button": Button(1, pin_factory=self.pin_factory),
            "push_button1": Button(2, pin_factory=self.pin_factory),
            "push_button2": Button(3, pin_factory=self.pin_factory),
            "push_button3": Button(4, pin_factory=self.pin_factory),
            "push_button4": Button(5, pin_factory=self.pin_factory),
            "push_button5": Button(6, pin_factory=self.pin_factory),
            "push_button6": Button(7, pin_factory=self.pin_factory),
            "push_button7": Button(8, pin_factory=self.pin_factory),
        }

        # initialize i2c connection
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
        self.last_read = 0

    def update_i2c_pins(self):
        # the peripheral only updates i2c every 10ms
        if time.time() - self.last_read > 0.01:
            try:
                byte = self.pi.i2c_read_byte(self.handle)
                bits = [int(i) for i in f"{byte:08b}"[::-1]]
                if len(bits) == 0:
                    return
                for i, bit in enumerate(bits):
                    if bit:
                        self.pin_factory.pin(i + 1).drive_low()
                    else:
                        self.pin_factory.pin(i + 1).drive_high()
            except pigpio.error:
                print("i2c read failed! Skipping for this frame..")
                return
            return
