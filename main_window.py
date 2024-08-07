import io
import os
import time
import pyray as pr
from gpiozero import Button, RotaryEncoder
import hub_constants
import pigpio

from i2c_controller import I2cController
import pin_control_panel

# TODO take build pictures
# Initialize screen
pr.init_window(
    hub_constants.SCREEN_WIDTH, hub_constants.SCREEN_HEIGHT, "pi-desk-hub main window"
)
pr.set_target_fps(30)


screen_texture = pr.load_render_texture(
    hub_constants.SCREEN_HEIGHT, hub_constants.SCREEN_WIDTH
)
source = pr.Rectangle(
    0.0, 0.0, hub_constants.SCREEN_HEIGHT, -hub_constants.SCREEN_WIDTH
)
destination = pr.Rectangle(
    0,
    hub_constants.SCREEN_HEIGHT,
    hub_constants.SCREEN_HEIGHT,
    hub_constants.SCREEN_WIDTH,
)


def is_raspberrypi():
    try:
        with io.open("/sys/firmware/devicetree/base/model", "r") as m:
            if "raspberry pi" in m.read().lower():
                return True
    except Exception:
        pass
    return False


# handle mock pins
debug = not is_raspberrypi()
i2c_controller = None
if debug:
    test_window = pin_control_panel.PinControlPanel()


# initialize inputs
# 26: xiao rp2040 sda - handles encoderA,B,button + radio transmitter/receiver?
# 19: xiao rp2040 scl
# 11: nav button?
# 10: nav button?
# 27: on-air limit switch/toggle
on_air = Button(27)
if not debug:
    try:
        i2c_controller = I2cController()
    except TimeoutError as e:
        print(e)
    encoder = i2c_controller.encoder
    encoder_button = i2c_controller.encoder_button


def show_on_air():
    if on_air.is_active != hub_constants.INVERT_ON_AIR_ACTIVE:
        color = pr.RED
    else:
        color = pr.GRAY
    pr.draw_rectangle(200, 10, 115, 28, pr.LIGHTGRAY)
    pr.draw_text("ON AIR", 205, 10, 30, color)
    # TODO manage radio transmitter (send 1 to xiao)


def handle_i2c():
    if i2c_controller:
        i2c_controller.update_i2c_devices()
        if encoder_button.is_active():
            pr.draw_text("encoder button active", 45, 10, 3, pr.GREEN)
        pr.draw_text(str(encoder.value), 45, 20, 3, pr.ORANGE)
    else:
        pr.draw_text("i2c_controller not found", 45, 2, 3, pr.RED)


# Main game loop
while not pr.window_should_close():  # Detect window close button or ESC key
    # Update
    # TODO: Update your variables here

    # Draw to texture
    pr.begin_texture_mode(screen_texture)
    pr.clear_background(pr.SKYBLUE)
    handle_i2c()
    show_on_air()
    pr.draw_fps(5, 220)
    pr.end_texture_mode()

    # Draw texture to screen
    pr.begin_drawing()
    pr.clear_background(pr.BEIGE)
    pr.draw_texture_pro(
        screen_texture.texture,
        source,
        destination,
        pr.Vector2(0, 0),
        -90,
        pr.WHITE,
    )
    if debug:
        test_window.mainloop()
    pr.end_drawing()


# De-Initialization
pr.unload_render_texture(screen_texture)
pr.close_window()  # Close window and OpenGL context
