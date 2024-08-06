import pyray as pr
from raylib import ffi
from gpiozero import Device, Button
from gpiozero.pins.mock import MockFactory
import hub_constants, hub_gui

# Initialization


""" 27
10
11
19
26 """


class PinControlPanel:
    def __init__(self):
        Device.pin_factory = MockFactory()
        pr.set_window_size(hub_constants.SCREEN_WIDTH * 2, hub_constants.SCREEN_HEIGHT)
        self.pin10 = Device.pin_factory.pin(10)
        self.pin11 = Device.pin_factory.pin(11)
        self.pin19 = Device.pin_factory.pin(19)
        self.pin26 = Device.pin_factory.pin(26)

        self.pins = {
            27: {
                "header_y": 10,
                "pin": Device.pin_factory.pin(27),
                "toggle": True,
                "type": "Button",
            },
            10: {
                "header_y": 50,
                "pin": Device.pin_factory.pin(10),
                "toggle": False,
                "type": "Output",
            },
            11: {
                "header_y": 90,
                "pin": Device.pin_factory.pin(11),
                "toggle": False,
                "type": "Button",
            },
            19: {
                "header_y": 130,
                "pin": Device.pin_factory.pin(19),
                "toggle": False,
                "type": "EncoderB",
            },
            26: {
                "header_y": 170,
                "pin": Device.pin_factory.pin(26),
                "toggle": False,
                "type": "EncoderA",
            },
        }

    def draw_header(self, pin, y):
        pr.draw_text(str(pin), hub_constants.SCREEN_WIDTH + 10, y, 20, pr.BLACK)
        pr.draw_line(
            hub_constants.SCREEN_WIDTH,
            y + 20,
            hub_constants.SCREEN_WIDTH + 240,
            y + 20,
            pr.GRAY,
        )

    def close(self):
        pr.close_window()

    # TODO: limit to type: Button
    def draw_pin_button(self, pin):
        if not pin["type"] == "Button":
            return
        x = hub_constants.SCREEN_WIDTH + 45
        y = pin["header_y"]
        width = 45
        height = 15
        if pr.is_mouse_button_down(0) and pr.check_collision_point_rec(
            pr.get_mouse_position(), pr.Rectangle(x, y, width, height)
        ):
            # draw dark blue return true
            pr.draw_rectangle(x, y, width, height, pr.DARKBLUE)
            return True
        else:
            # draw  blue return false
            pr.draw_rectangle(x, y, width, height, pr.BLUE)
            return False

    # TODO: implement simulated rotary encoder
    def pin_control(self, pin, data):
        self.draw_header(pin, data["header_y"])
        data["toggle"] = hub_gui.toggle(
            hub_constants.SCREEN_WIDTH + 100,
            data["header_y"],
            10,
            15,
            "",
            data["toggle"],
        )
        pressed = self.draw_pin_button(data) or data["toggle"]
        if pressed:
            data["pin"].drive_low()
        else:
            data["pin"].drive_high()

    def show_mouse_location(self):
        mouse_x, mouse_y = pr.get_mouse_x(), pr.get_mouse_y()
        pr.draw_text(f"{mouse_x}, {mouse_y}", mouse_x + 5, mouse_y - 5, 5, pr.BLACK)

    def mainloop(self):
        # Main game loop
        # Update
        pr.draw_line(
            hub_constants.SCREEN_WIDTH + 1,
            0,
            hub_constants.SCREEN_WIDTH + 1,
            hub_constants.SCREEN_HEIGHT,
            pr.BLACK,
        )
        self.show_mouse_location()
        for pin, data in self.pins.items():
            self.pin_control(pin, data)
