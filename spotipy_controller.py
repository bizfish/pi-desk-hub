import io
import os
import time

import requests
import spotipy
import pyray as pr
from PIL import Image
from spotipy import SpotifyOauthError
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

import hub_constants


class SpotipyController:
    def __init__(self, window):
        print(print("initializing spotipy..."))
        self.client_id = os.environ["SPOTIPY_CLIENT_ID"]
        self.client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
        self.redirect = os.environ["SPOTIPY_REDIRECT_URI"]
        self.latency_offset = 0
        self.scope = ",".join(hub_constants.SPOTIPY_SCOPES)
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect,
            scope=self.scope,
        )
        self.window = window
        self.sp = None
        self.sp = self.check_token_cache()
        if not self.sp:
            try:
                if os.path.exists("./auth.txt"):
                    with open("./auth.txt", "r", encoding="utf-8") as f:
                        auth_code = f.readline().strip()
                else:
                    raise PermissionError(
                        f"Please visit:\n{self.sp_oauth.get_authorize_url()}\n in a signed-in "
                        "browser and paste the code from the redirect URL in ./auth.txt"
                    )
                self.new_oauth(auth_code)
            except SpotifyOauthError as e:
                os.remove("./auth.txt")
                raise PermissionError(e.args) from e
        if not self.sp:
            raise PermissionError("spotify init failed")
        self.playing = None
        self.displayed_track = None
        self.check_current_playback()
        self.last_checked = time.time()

    def check_token_cache(self):
        try:
            token_info = self.sp_oauth.validate_token(
                self.sp_oauth.cache_handler.get_cached_token()
            )
        except SpotifyOauthError:
            # invalidate cache
            os.remove(self.sp_oauth.cache_handler.cache_path)
            return None
        if token_info is not None:
            if self.sp_oauth.is_token_expired(token_info):
                token_info = self.sp_oauth.refresh_access_token(
                    token_info["refresh_token"]
                )
            return spotipy.Spotify(auth=token_info["access_token"])
        return None

    def new_oauth(self, auth_code):
        token_info = self.sp_oauth.get_access_token(auth_code)
        access_token = token_info["access_token"]
        # Create a Spotify object with the access token
        return spotipy.Spotify(auth=access_token)

    def check_current_playback(self):
        # TODO see if I can async this or something so it doesnt stutter
        json = self.sp.current_playback()
        if json:
            track_id = str(json["item"]["id"]).strip()
            if self.playing and self.playing.id == track_id:
                self.playing.update(json)
            else:
                self.playing = SpotifyTrack(controller=self, json=json)
        else:
            self.playing = None
            self.displayed_track = None

    def update_track(self):
        # TODO increase the cooldown after some period of inactivity/not playing
        if time.time() - self.last_checked > hub_constants.PLAYING_COOLDOWN:
            self.check_current_playback()
            self.last_checked = time.time()
        if self.playing:
            self.display_track(self.playing)

    def display_track(self, track):
        track.draw_track_info()
        self.displayed_track = track

    def toggle_playback(self):
        if self.playing:
            if self.playing.is_playing:
                self.pause_playback()
            else:
                self.start_playback()

    def pause_playback(self):
        if self.playing and self.playing.is_playing:
            try:
                self.sp.pause_playback()
            except SpotifyException:
                print("Attempted to pause but failed. Assuming it's already paused.")
            self.playing.is_playing = False

    def start_playback(self):
        if self.playing and not self.playing.is_playing:
            try:
                self.sp.start_playback()
            except SpotifyException:
                print("Attempted to play but failed. Assuming it's already playing.")
            self.playing.is_playing = True


class SpotifyTrack:
    def __init__(self, controller, json):
        self.controller = controller
        self.window = controller.window
        self.item = json["item"]
        self.id = self.item["id"].strip()
        self.artists = ", ".join(
            artist["name"].strip() for artist in self.item["artists"]
        )
        self.title = self.item["name"].strip()
        self.is_playing = json["is_playing"]
        self.duration_s = self.item["duration_ms"] / 1000  # convert to seconds
        self.album = self.item["album"]
        self.album_id = self.album["id"].strip()
        self.album_title = self.album["name"].strip()
        self.progress_s = json["progress_ms"] / 1000  # convert to seconds
        self.timestamp = time.time()  # assume latency is negligible
        self.progress_inferred = self.progress_s
        self.inference_diff = 0
        self.cached_cover = f"./{hub_constants.IMAGE_CACHE_DIR}/{self.album_id}.jpg"
        self.album_texture = None

    def __del__(self):
        if self.album_texture:
            pr.unload_texture(self.album_texture)

    def update(self, json):
        # if we are here then the same track was just playing
        self.progress_s = json["progress_ms"] / 1000  # convert to seconds
        self.timestamp = time.time()
        self.is_playing = json["is_playing"]
        self.inference_diff = self.progress_inferred - self.progress_s
        self.infer_progress()

    def cache_album_art(self):
        os.makedirs(f"./{hub_constants.IMAGE_CACHE_DIR}/", exist_ok=True)
        cover_url = sorted(self.album["images"], key=lambda x: x["height"])[2]["url"]
        img_data = requests.get(cover_url, timeout=10).content
        with Image.open(io.BytesIO(img_data)) as im:
            im.thumbnail(hub_constants.ALBUM_RESOLUTION)
            im.save(f"./{hub_constants.IMAGE_CACHE_DIR}/{self.album_id}.jpg")

    def infer_progress(self):
        if self.is_playing:
            self.progress_inferred = min(
                self.progress_s + (time.time() - self.timestamp), self.duration_s
            )
            if self.progress_inferred == self.duration_s:
                # check for next song
                self.controller.check_current_playback()

    def draw_time_debug(self):
        pr.draw_text(
            f"Inferred: {self.progress_inferred}",
            10,
            35,
            5,
            pr.BLACK,
        )
        pr.draw_text(
            f"Last True Progress: {self.progress_s}",
            10,
            45,
            5,
            pr.BLACK,
        )
        pr.draw_text(
            f"Inference Diff: {self.inference_diff}",
            10,
            55,
            5,
            pr.BLACK,
        )

    def draw_track_info(self, x=10, x_padding=10, y_padding=25):
        if not self.album_texture:
            self.cache_album_art()
            self.album_texture = pr.load_texture(self.cached_cover)
        y = hub_constants.SCREEN_HEIGHT - y_padding - self.album_texture.height
        pr.draw_texture_rec(
            self.album_texture,
            pr.Rectangle(0, 0, self.album_texture.width, self.album_texture.height),
            pr.Vector2(x, y),
            pr.WHITE,
        )
        text_x = x + self.album_texture.width + x_padding
        pr.draw_text(self.title, text_x, y + 5, 8, pr.BLACK)
        pr.draw_text(self.artists, text_x, y + 15, 7, pr.BLACK)
        pr.draw_text(self.album_title, text_x, y + 30, 6, pr.BLACK)

        if self.window.debug and hub_constants.DISPLAY_TEST_PANEL:
            self.draw_time_debug()

        self.infer_progress()
        bar_length = hub_constants.SCREEN_WIDTH - text_x - x_padding
        bar_y = y + 60
        progress_pixels = int(self.progress_inferred / self.duration_s * bar_length)
        # pr.draw_triangle()
        pr.draw_rectangle(text_x, bar_y, bar_length, 3, pr.BLACK)  # full bar
        pr.draw_rectangle(text_x, bar_y, progress_pixels, 4, pr.DARKBLUE)
        pr.draw_circle(text_x + progress_pixels, bar_y + 2, 5, pr.DARKBLUE)
