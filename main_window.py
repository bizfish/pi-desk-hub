import os
import pyray as pr
from gpiozero import Button, Device
import pin_control_panel
import hub_constants

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

# handle mock pins
debug = "TERM_PROGRAM" in os.environ.keys() and os.environ["TERM_PROGRAM"] == "vscode"
if debug:
    test_window = pin_control_panel.PinControlPanel()

# initialize inputs
# 26: encoder A
# 19: encoder B
# 11: encoder Button
# 10: radio transmitter
# 27: on-air limit switch/toggle? or arduino for expanded gpio?
on_air = Button(27)


def show_on_air():
    if on_air.is_active == hub_constants.ON_AIR_PRESSED:
        color = pr.RED
    else:
        color = pr.GRAY
    pr.draw_rectangle(200, 10, 115, 28, pr.LIGHTGRAY)
    pr.draw_text("ON AIR", 205, 10, 30, color)
    # TODO manage radio transmitter


# Main game loop
while not pr.window_should_close():  # Detect window close button or ESC key
    # Update
    # TODO: Update your variables here

    # Draw to texture
    pr.begin_texture_mode(screen_texture)
    pr.clear_background(pr.SKYBLUE)
    show_on_air()
    pr.draw_fps(10, 10)
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
