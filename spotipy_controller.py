import asyncio
import io
import json
import os
import time

import requests
import pyray as pr
from PIL import Image
from async_spotify.authentification.authorization_flows import AuthorizationCodeFlow
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify import SpotifyApiClient, TokenRenewClass
from async_spotify.spotify_errors import TokenExpired, SpotifyError, SpotifyAPIError


import hub_constants


class SpotifyController:
    def __init__(self, window):
        self.window = window
        print(print("initializing spotipy..."))
        self.sp_oauth = AuthorizationCodeFlow(
            application_id=os.environ["SPOTIPY_CLIENT_ID"],
            application_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
            redirect_url=os.environ["SPOTIPY_REDIRECT_URI"],
            scopes=hub_constants.SPOTIFY_SCOPES,
        )
        self.playing = None
        self.displayed_track = None
        self.auth_token = None
        self.renew_token = TokenRenewClass()
        self.is_updating = False

    async def cleanup(self):
        await self.api_client.close_client()

    async def async_init(self):
        self.auth_token = await self.get_token()
        self.renew_token = TokenRenewClass()
        self.api_client = SpotifyApiClient(
            self.sp_oauth,
            hold_authentication=True,
            spotify_authorisation_token=self.auth_token,
            token_renew_instance=self.renew_token,
        )
        await self.api_client.create_new_client()
        if self.auth_token.is_expired():
            await self.api_client.refresh_token(self.auth_token)
        await self.check_current_playback()

    async def get_token(self):
        auth_token = self.check_token_cache()
        if not auth_token:
            api = SpotifyApiClient(self.sp_oauth)
            if os.path.exists("./auth.txt"):
                with open("./auth.txt", "r", encoding="utf-8") as f:
                    auth_code = f.readline().strip()
            else:
                raise PermissionError(
                    f"Please visit:\n{api.build_authorization_url(False)} in in a signed-in "
                    "browser and paste the code from the redirect URL in ./auth.txt"
                )
            try:
                auth_token = await self.new_oauth(auth_code, api)
            except SpotifyError as e:
                raise PermissionError("Auth code in ./auth.txt isn't valid. ") from e
        return auth_token

    def check_token_cache(self):
        # check for cache file
        # read cache file in (json)
        # self.activation_time: int = activation_time
        # self.refresh_token: str = refresh_token
        # self.access_token: str = access_token
        # create SpotifyAuthorizationToken object
        # check valid
        # if expired, refresh it
        if os.path.exists(hub_constants.SPOTIFY_CACHE):
            with open(hub_constants.SPOTIFY_CACHE, "r", encoding="utf-8") as f:
                data = f.read()
                if data:
                    data = json.loads(data)
                else:
                    data = None  # not valid
            required_keys = ["access_token", "refresh_token", "activation_time"]
            if all(key in data for key in required_keys):
                return SpotifyAuthorisationToken(
                    data["refresh_token"], data["activation_time"], data["access_token"]
                )
            else:
                # bad cache, delete it
                raise ValueError("Bad cache data")
                # os.remove(hub_constants.SPOTIFY_CACHE)
        return None

    async def new_oauth(self, auth_code, api_client=None):
        if not api_client:
            api_client = self.api_client
        token = await api_client.get_auth_token_with_code(auth_code)
        # cache the token
        with open(hub_constants.SPOTIFY_CACHE, "w", encoding="utf-8") as f:
            f.write(json.dumps(token.__dict__))
        return token

    async def check_current_playback(self):
        data = await self.api_client.player.get_queue()  # get_queue
        self.last_checked = time.time()
        if data:
            track_id = str(data["item"]["id"]).strip()
            if self.playing and self.playing.id == track_id:
                self.playing.update(data)
            else:
                self.playing = SpotifyTrack(controller=self, data=data)
        else:
            self.playing = None
            self.displayed_track = None

    def start_updating(self):
        self.is_updating = True
        asyncio.create_task(self.update_loop())

    def stop_updating(self):
        self.is_updating = False

    async def update_loop(self):
        while self.is_updating:
            await self.check_current_playback()
            if self.playing:
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(10)  # check less often if nothing's playing

    def display_track(self):
        if self.playing:
            self.playing.draw_track_info()
            self.displayed_track = self.playing

    def toggle_playback(self):
        if self.playing:
            if self.playing.is_playing:
                self.pause_playback()
            else:
                self.start_playback()

    def pause_playback(self):
        if self.playing and self.playing.is_playing:
            asyncio.create_task(self.pause())

    async def pause(self):
        try:
            await self.api_client.player.pause()
        except SpotifyAPIError:
            print("Attempted to pause but failed.")
        self.playing.is_playing = False

    def start_playback(self):
        if self.playing and not self.playing.is_playing:
            asyncio.create_task(self.play())

    async def play(self):
        try:
            await self.api_client.player.play()
        except SpotifyAPIError:
            print("Attempted to play but failed.")
        self.playing.is_playing = True


class SpotifyTrack:
    def __init__(self, controller, data):
        self.controller = controller
        self.window = controller.window
        self.item = data["item"]
        self.id = self.item["id"].strip()
        self.artists = ", ".join(
            artist["name"].strip() for artist in self.item["artists"]
        )
        self.title = self.item["name"].strip()
        self.is_playing = data["is_playing"]
        self.duration_s = self.item["duration_ms"] / 1000  # convert to seconds
        self.album = self.item["album"]
        self.album_id = self.album["id"].strip()
        self.album_title = self.album["name"].strip()
        self.progress_s = data["progress_ms"] / 1000  # convert to seconds
        self.timestamp = time.time()  # assume latency is negligible
        self.progress_inferred = self.progress_s
        self.inference_diff = 0
        self.cached_cover = f"./{hub_constants.IMAGE_CACHE_DIR}/{self.album_id}.jpg"
        self.album_texture = None

    def __del__(self):
        if self.album_texture:
            pr.unload_texture(self.album_texture)

    def update(self, data):
        # if we are here then the same track was just playing
        self.progress_s = data["progress_ms"] / 1000  # convert to seconds
        self.timestamp = time.time()
        self.is_playing = data["is_playing"]
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
                asyncio.create_task(self.controller.check_current_playback())

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
