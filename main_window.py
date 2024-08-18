import asyncio
import io
import math
import sys
import pyray as pr
from gpiozero import Button, RotaryEncoder
import hub_constants

from i2c_controller import I2cController
import pin_control_panel
from spotipy_controller import SpotifyController


def is_raspberrypi():
    try:
        with io.open("/sys/firmware/devicetree/base/model", "r", encoding="utf-8") as m:
            if "raspberry pi" in m.read().lower():
                return True
    except Exception:
        pass
    return False


class PiDeskHub:
    def __init__(self):
        self.debug = not is_raspberrypi()
        if self.debug:
            # draw horizontal on PC screen
            pr.init_window(
                hub_constants.SCREEN_WIDTH,
                hub_constants.SCREEN_HEIGHT,
                "pi-desk-hub debug window",
            )
        else:  # pi screen is rotated 90deg so we flip
            pr.init_window(
                hub_constants.SCREEN_HEIGHT,
                hub_constants.SCREEN_WIDTH,
                "pi-desk-hub main window",
            )
        pr.set_target_fps(30)

        self.screen_texture = pr.load_render_texture(
            hub_constants.SCREEN_WIDTH, hub_constants.SCREEN_HEIGHT
        )
        self.rat_render = pr.load_render_texture(
            hub_constants.SCREEN_WIDTH, hub_constants.SCREEN_HEIGHT
        )
        self.source = pr.Rectangle(
            0.0, 0.0, hub_constants.SCREEN_WIDTH, -hub_constants.SCREEN_HEIGHT
        )
        self.destination = pr.Rectangle(
            0,
            hub_constants.SCREEN_WIDTH,
            hub_constants.SCREEN_WIDTH,
            hub_constants.SCREEN_HEIGHT,
        )
        self.spotipy = None
        self.camera = pr.Camera3D()
        self.camera.position = pr.Vector3(5.0, 5.0, 5.0)  # Camera position
        self.camera.target = pr.Vector3(0.0, 2.5, 0.0)  # Camera looking at point
        self.camera.up = pr.Vector3(
            0.0, 1.0, 0.0
        )  # Camera up vector (rotation towards target)
        self.camera.fovy = 45.0  # Camera field-of-view Y
        self.camera.projection = pr.CAMERA_PERSPECTIVE  # Camera mode type
        self.rat_model = pr.load_model("./resources/rat.obj")
        self.rat_position = pr.Vector3(0, 1, 0)
        self.rat_rotation = -90
        self.rat_alpha = 0
        # handle mock pins and i2c connection

        if self.debug:
            self.test_window = pin_control_panel.PinControlPanel()
            self.on_air = Button(26, pull_up=False)
            self.push_button1 = Button(2)
            self.i2c_controller = None
        else:
            try:
                self.i2c_controller = I2cController()
            except TimeoutError as e:
                print(e)
                sys.exit()
            self.on_air = self.i2c_controller.devices["on_air_button"]
            self.push_button1 = self.i2c_controller.devices["push_button1"]

        # initialize inputs
        # 26: xiao rp2040 sda - handles encoderA,B,button + radio transmitter/receiver?
        # 19: xiao rp2040 scl
        # 11: Encoder Button
        # 10: Encoder B
        # 27: Encoder A
        self.encoder = RotaryEncoder(27, 10)
        self.encoder_button = Button(11)
        self.encoder_val_prev = -1

    def __del__(self):
        pr.unload_render_texture(self.screen_texture)
        pr.unload_render_texture(self.rat_render)
        pr.unload_model(self.rat_model)
        pr.close_window()

    async def start_game_loop(self):
        await self.initialize_spotipy()
        if self.spotipy:
            self.spotipy.is_updating = True
            if hub_constants.PAUSE_ON_AIR:
                self.on_air.when_activated = self.spotipy.pause_playback
                if hub_constants.RESUME_OFF_AIR:
                    self.on_air.when_deactivated = self.spotipy.start_playback
            asyncio.create_task(self.spotipy.update_loop())
        while not pr.window_should_close():  # Detect window close button or ESC key
            # Update
            await asyncio.sleep(0)  # let async stuff run
            if self.encoder_button.is_active:
                pr.draw_text("Encoder button active!", 45, 200, 4, pr.BLACK)
                self.encoder_val_prev = self.encoder.value
            self.encoder.value = self.encoder_val_prev
            self.rat_alpha = (
                int(255 * (self.encoder.value + 1) / 2) if hub_constants.DRAW_RAT else 0
            )
            self.render_rat()

            # Draw to texture
            pr.begin_texture_mode(self.screen_texture)
            pr.clear_background(pr.SKYBLUE)
            self.handle_i2c()
            self.show_on_air()
            if self.spotipy:
                self.spotipy.display_track()
            if self.rat_alpha:
                pr.draw_texture_rec(
                    self.rat_render.texture,
                    self.source,
                    pr.Vector2(0, 0),
                    pr.Color(255, 255, 255, self.rat_alpha),
                )

            pr.end_texture_mode()

            # Draw texture to screen
            pr.begin_drawing()
            pr.clear_background(pr.BEIGE)
            if self.debug:  # draw horizontal
                pr.draw_texture_rec(
                    self.screen_texture.texture, self.source, pr.Vector2(0, 0), pr.WHITE
                )
            else:  # rotate 90 degrees on pi
                pr.draw_texture_pro(
                    self.screen_texture.texture,
                    self.source,
                    self.destination,
                    pr.Vector2(0, 0),
                    -90,
                    pr.WHITE,
                )
            if self.debug:
                self.test_window.mainloop(self.encoder.value)
                self.encoder.value = self.test_window.encoder_value
            pr.end_drawing()
        if self.spotipy:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If the loop is running, create a task for the cleanup
                loop.create_task(self.spotipy.cleanup())
            else:
                # If the loop is not running, run the cleanup task directly
                loop.run_until_complete(self.spotipy.cleanup())

    def handle_i2c(self):
        if self.i2c_controller:
            self.i2c_controller.update_i2c_pins()
            y = 10
            # TODO remove this debug display
            for label, device in self.i2c_controller.devices.items():
                if label != "on_air_button" and device.is_active:
                    pr.draw_text(f"{label} active", 45, y, 3, pr.DARKGRAY)
                    y += 10
        elif self.debug:
            pr.draw_text("Input peripheral not found", 40, 2, 12, pr.RED)

    def render_rat(self):
        if self.rat_alpha:
            pr.begin_texture_mode(self.rat_render)
            pr.clear_background(pr.Color(255, 255, 255, 0))
            pr.begin_mode_3d(self.camera)
            pr.draw_model_ex(
                self.rat_model,
                self.rat_position,
                pr.Vector3(0.0, 1.0, 0.0),
                self.rat_rotation,
                pr.Vector3(0.1, 0.1, 0.1),
                pr.Color(255, 255, 255, 255),
            )
            self.rat_rotation += 1.5
            pr.end_mode_3d()
            pr.end_texture_mode()

    def show_on_air(self):
        if self.on_air.is_active:
            color = pr.RED
        else:
            color = pr.GRAY
        pr.draw_rectangle(200, 10, 115, 28, pr.LIGHTGRAY)
        pr.draw_text("ON AIR", 205, 10, 30, color)
        # TODO manage radio transmitter (send to xiao or just do it in arduino)

    async def initialize_spotipy(self):
        if hub_constants.SPOTIFY_ENABLED:
            try:
                self.spotipy = SpotifyController(self)
                await self.spotipy.async_init()
                if self.spotipy:
                    self.push_button1.when_activated = self.spotipy.toggle_playback
            except PermissionError as e:
                print(e)
                self.spotipy = None
        else:
            self.spotipy = None


def main():
    hub = PiDeskHub()
    asyncio.run(hub.start_game_loop())


if __name__ == "__main__":
    main()
