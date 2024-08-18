import pyray as pr
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
import hub_constants
import hub_gui

# Initialization
WHEEL_SPEED = 0.1


class PinControlPanel:
    def __init__(self):
        Device.pin_factory = MockFactory()
        if hub_constants.DISPLAY_TEST_PANEL:
            pr.set_window_size(
                hub_constants.SCREEN_WIDTH, hub_constants.SCREEN_HEIGHT * 2
            )
        self.pin10 = Device.pin_factory.pin(10)
        self.pin11 = Device.pin_factory.pin(11)
        self.pin19 = Device.pin_factory.pin(19)
        self.pin26 = Device.pin_factory.pin(26)
        self.encoder_value = 0.0

        self.pins = {
            27: {
                "header_y": 10,
                "pin": Device.pin_factory.pin(27),
                "toggle": False,
                "type": "None",
                "label": "EncoderA",
            },
            10: {
                "header_y": 50,
                "pin": Device.pin_factory.pin(10),
                "toggle": False,
                "type": "None",
                "label": "EncoderB",
            },
            11: {
                "header_y": 90,
                "pin": Device.pin_factory.pin(11),
                "toggle": False,
                "type": "Button",
                "label": "Encoder Button",
            },
            19: {
                "header_y": 130,
                "pin": Device.pin_factory.pin(19),
                "toggle": False,
                "type": "None",
                "label": "None",
            },
            1: {
                "header_y": 170,
                "pin": Device.pin_factory.pin(26),
                "toggle": True,
                "type": "Button",
                "label": "On Air",
            },
            2: {
                "header_y": 210,
                "pin": Device.pin_factory.pin(2),
                "toggle": False,
                "type": "Button",
                "label": "Pushbutton1",
            },
        }

    def draw_header(self, pin, data):
        pr.draw_text(
            str(pin), 10, hub_constants.SCREEN_HEIGHT + data["header_y"], 20, pr.BLACK
        )
        pr.draw_text(
            data["label"],
            120,
            hub_constants.SCREEN_HEIGHT + data["header_y"],
            15,
            pr.BLACK,
        )
        pr.draw_line(
            0,
            hub_constants.SCREEN_HEIGHT + data["header_y"] + 20,
            hub_constants.SCREEN_WIDTH,
            hub_constants.SCREEN_HEIGHT + data["header_y"] + 20,
            pr.GRAY,
        )

    def close(self):
        pr.close_window()

    def draw_pin_button(self, pin):
        if not pin["type"] == "Button":
            return
        pin["toggle"] = hub_gui.toggle(
            100,
            hub_constants.SCREEN_HEIGHT + pin["header_y"],
            10,
            15,
            pin["toggle"],
        )
        x = 45
        y = hub_constants.SCREEN_HEIGHT + pin["header_y"]
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

    def pin_control(self, data):
        pressed = self.draw_pin_button(data) or data["toggle"]
        if pressed:
            data["pin"].drive_low()
        else:
            data["pin"].drive_high()

    def show_mouse_location(self):
        mouse_x, mouse_y = pr.get_mouse_x(), pr.get_mouse_y()
        pr.draw_text(f"{mouse_x}, {mouse_y}", mouse_x + 5, mouse_y - 5, 5, pr.BLACK)

    def simulate_encoder(self):
        move = pr.get_mouse_wheel_move()
        pr.draw_text(str(move), 280, 250, 5, pr.BLACK)
        pr.draw_text(str(self.encoder_value), 280, 300, 5, pr.BLACK)
        self.encoder_value = min(1, max(-1, self.encoder_value + move * WHEEL_SPEED))

    def mainloop(self, encoder_value):
        # Main game loop
        # Update
        self.encoder_value = encoder_value
        if hub_constants.DISPLAY_TEST_PANEL:
            pr.draw_fps(5, 220)
            pr.draw_line(
                0,
                hub_constants.SCREEN_HEIGHT,
                hub_constants.SCREEN_WIDTH,
                hub_constants.SCREEN_HEIGHT,
                pr.BLACK,
            )
        self.simulate_encoder()
        self.show_mouse_location()

        for pin, data in self.pins.items():
            if hub_constants.DISPLAY_TEST_PANEL:
                self.draw_header(pin, data)
                self.pin_control(data)
