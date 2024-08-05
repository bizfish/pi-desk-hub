import os
import pyray as pr
from gpiozero import Button, Device
from gpiozero.pins.mock import MockFactory
import pin_control_panel
import hub_constants

# Initialize screen
pr.init_window(hub_constants.SCREEN_WIDTH, hub_constants.SCREEN_HEIGHT, "pi-desk-hub main window")
pr.set_target_fps(30)

# handle mock pins
debug = "TERM_PROGRAM" in os.environ.keys() and os.environ["TERM_PROGRAM"] == "vscode"
if debug:
    test_window = pin_control_panel.PinControlPanel()

# initialize inputs
# 26: encoder A
# 19: encoder B
# 11: encoder Button
# 10: pushbutton
# 27: on-air limit switch/toggle
on_air = Button(27)


def show_on_air():
    if on_air.is_active:
        color = pr.RED
    else:
        color = pr.GRAY
    pr.draw_rectangle(115, 5, 120, 35, pr.LIGHTGRAY)
    pr.draw_text('ON AIR', 120, 10, 30, color)


# Main game loop
while not pr.window_should_close():  # Detect window close button or ESC key
    # Update
    # TODO: Update your variables here

    # Draw
    pr.begin_drawing()
    if debug:
        test_window.mainloop()
    pr.clear_background(pr.RAYWHITE)
    show_on_air()
    pr.draw_fps(10, 10)
    pr.end_drawing()


# De-Initialization
pr.close_window()  # Close window and OpenGL context
