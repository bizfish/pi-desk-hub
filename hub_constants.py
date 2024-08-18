from raylib import ffi

SCREEN_HEIGHT = 240
SCREEN_WIDTH = 320
C_TRUE = ffi.new("bool *", True)
I2C_BUS = 3
I2C_ADDRESS = 0x40
I2C_TIMEOUT = 60  # 1 minute
DRAW_RAT = True
SPOTIFY_ENABLED = True
SPOTIFY_SCOPES = [
    "user-library-read",
    "user-read-playback-state",
    "user-modify-playback-state",
]
SPOTIFY_CACHE = "./.spotify"
IMAGE_CACHE_DIR = "imagecache"
ALBUM_RESOLUTION = (128, 128)
PLAYING_COOLDOWN = 5  # 12 times per minute sounds fine
LATENCY_TOLERANCE = 1  # 1 second
DISPLAY_TEST_PANEL = True
PAUSE_ON_AIR = True
RESUME_OFF_AIR = True
