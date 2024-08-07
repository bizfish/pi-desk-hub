from raylib import ffi

SCREEN_WIDTH = 240
SCREEN_HEIGHT = 320
C_TRUE = ffi.new("bool *", True)
INVERT_ON_AIR_ACTIVE = True
I2C_BUS = 3
I2C_ADDRESS = 0x40
I2C_TIMEOUT = 60  # 1 minute
DRAW_RAT = True
