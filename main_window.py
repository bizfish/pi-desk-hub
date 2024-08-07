import io
import math
import pyray as pr
from gpiozero import Button, RotaryEncoder
import hub_constants

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
rat_render = pr.load_render_texture(
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

camera = pr.Camera3D()
camera.position = pr.Vector3(5.0, 5.0, 5.0)  # Camera position
camera.target = pr.Vector3(0.0, 2.5, 0.0)  # Camera looking at point
camera.up = pr.Vector3(0.0, 1.0, 0.0)  # Camera up vector (rotation towards target)
camera.fovy = 45.0  # Camera field-of-view Y
camera.projection = pr.CAMERA_PERSPECTIVE  # Camera mode type
camera_angle = 0
rat_model = pr.load_model("./resources/rat.obj")
rat_position = pr.Vector3(0, 1, 0)


def is_raspberrypi():
    try:
        with io.open("/sys/firmware/devicetree/base/model", "r") as m:
            if "raspberry pi" in m.read().lower():
                return True
    except Exception:
        pass
    return False


# handle mock pins and i2c connection
debug = not is_raspberrypi()
if debug:
    test_window = pin_control_panel.PinControlPanel()
    on_air = Button(26)
    i2c_controller = None
else:
    try:
        i2c_controller = I2cController()
    except TimeoutError as e:
        print(e)
        quit()
    on_air = i2c_controller.devices["on_air_button"]

# initialize inputs
# 26: xiao rp2040 sda - handles encoderA,B,button + radio transmitter/receiver?
# 19: xiao rp2040 scl
# 11: Encoder Button
# 10: Encoder B
# 27: Encoder A
encoder = RotaryEncoder(27, 10)
encoder_button = Button(11)
encoder_val_prev = -1


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
        i2c_controller.update_i2c_pins()
        y = 10
        for label, device in i2c_controller.devices.items():
            if label != "on_air_button" and device.is_active:
                pr.draw_text(f"{label} active", 45, y, 3, pr.DARKGRAY)
                y += 10
        pr.draw_text(str(encoder.value), 160, 20, 3, pr.BLACK)
    else:
        pr.draw_text("i2c_controller not found", 45, 2, 3, pr.RED)


def update_camera_position(radius, angle):
    # Calculate x and z coordinates based on the angle and radius
    x = radius * math.cos(angle)
    z = radius * math.sin(angle)

    # Return the updated camera position
    return pr.Vector3(x, 5, z)


def render_rat():
    global camera_angle
    if draw_rat:
        camera_angle += 0.05
        camera.position = update_camera_position(10, camera_angle)
        pr.begin_texture_mode(rat_render)
        pr.clear_background(pr.Color(255, 255, 255, 0))
        pr.begin_mode_3d(camera)
        pr.draw_model_ex(
            rat_model,
            rat_position,
            pr.Vector3(0.0, 1.0, 0.0),
            -90,
            pr.Vector3(0.1, 0.1, 0.1),
            pr.Color(255, 255, 255, 255),
        )
        pr.end_mode_3d()
        pr.end_texture_mode()


# Main game loop
while not pr.window_should_close():  # Detect window close button or ESC key
    # Update

    if encoder_button.is_active:
        pr.draw_text("Encoder button active!", 45, 200, 4, pr.BLACK)
        encoder_val_prev = encoder.value
    else:
        encoder.value = encoder_val_prev
    rat_alpha = int(255 * (encoder.value + 1) / 2)
    draw_rat = rat_alpha > 0 and hub_constants.DRAW_RAT
    render_rat()

    # Draw to texture
    pr.begin_texture_mode(screen_texture)
    pr.clear_background(pr.SKYBLUE)
    handle_i2c()
    show_on_air()
    if draw_rat:
        pr.draw_texture_rec(
            rat_render.texture,
            source,
            pr.Vector2(0, 0),
            pr.Color(255, 255, 255, rat_alpha),
        )
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
        test_window.mainloop(encoder.value)
        encoder.value = test_window.encoder_value
    pr.end_drawing()


# De-Initialization
pr.unload_render_texture(screen_texture)
pr.unload_render_texture(rat_render)
pr.unload_model(rat_model)
pr.close_window()  # Close window and OpenGL context
