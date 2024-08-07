import io
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
rat_model = pr.load_model("./resources/rat.obj")
rat_texture = pr.load_texture("./resources/rat.png")
rat_model.materials.maps[pr.MATERIAL_MAP_ALBEDO].texture = rat_texture
rat_position = pr.Vector3(0, 2, 0)


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
encoder_val_prev = 0


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


# Main game loop
while not pr.window_should_close():  # Detect window close button or ESC key
    # Update
    # Draw to texture
    pr.begin_texture_mode(screen_texture)
    pr.clear_background(pr.SKYBLUE)
    pr.begin_mode_3d(camera)
    if encoder_button.is_active:
        pr.draw_text("Encoder button active!", 45, 200, 4, pr.BLACK)
        encoder_val_prev = encoder.value
    else:
        encoder.value = encoder_val_prev
    rat_rotation = 360 * encoder.value
    pr.draw_model_ex(
        rat_model,
        rat_position,
        pr.Vector3(0.0, 1.0, 0.0),
        rat_rotation,
        pr.Vector3(0.1, 0.1, 0.1),
        pr.WHITE,
    )
    pr.end_mode_3d()
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
        encoder.value = test_window.encoder_value
    pr.end_drawing()


# De-Initialization
pr.unload_render_texture(screen_texture)
pr.unload_model(rat_model)
pr.unload_texture(rat_texture)
pr.close_window()  # Close window and OpenGL context
