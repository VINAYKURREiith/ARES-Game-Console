from machine import Pin, SoftI2C
import ssd1306
import time

# ============================================================
# OLED
# ============================================================

i2c = SoftI2C(
    scl=Pin(1),
    sda=Pin(0),
    freq=100000
)

oled = ssd1306.SSD1306_I2C(
    128,
    64,
    i2c,
    addr=0x3C
)


# ============================================================
# BOOT ANIMATION
# ============================================================

def boot_animation():

    # --------------------------------------------------------
    # FRAME 1 - CLEAR
    # --------------------------------------------------------

    oled.fill(0)
    oled.show()
    time.sleep_ms(300)


    # --------------------------------------------------------
    # FRAME 2 - PICO LOGO
    # --------------------------------------------------------

    oled.fill(0)

    oled.text("PICO", 45, 12)
    oled.text("GAME", 45, 24)

    # simple game-console style box
    oled.rect(35, 8, 58, 30, 1)

    # controller dots
    oled.fill_rect(40, 42, 4, 4, 1)
    oled.fill_rect(47, 39, 4, 4, 1)

    oled.fill_rect(78, 39, 4, 4, 1)
    oled.fill_rect(85, 42, 4, 4, 1)

    oled.show()

    time.sleep_ms(700)


    # --------------------------------------------------------
    # FRAME 3 - LOADING
    # --------------------------------------------------------

    oled.fill(0)

    oled.text("ARES GAME", 32, 10)
    oled.text("CONSOLE", 39, 22)

    oled.rect(15, 40, 98, 10, 1)

    oled.show()

    # Loading bar

    for width in range(0, 94, 6):

        oled.fill_rect(
            17,
            42,
            width,
            6,
            1
        )

        oled.show()

        time.sleep_ms(70)


    # --------------------------------------------------------
    # FRAME 4 - READY
    # --------------------------------------------------------

    oled.fill(0)

    oled.text("ARES GAME", 32, 15)
    oled.text("CONSOLE", 39, 27)

    oled.text("READY!", 46, 45)

    oled.show()

    time.sleep_ms(700)


    # --------------------------------------------------------
    # FADE/TRANSITION EFFECT
    # --------------------------------------------------------

    for _ in range(2):

        oled.fill(0)
        oled.show()
        time.sleep_ms(100)

        oled.text("ARES GAME", 32, 15)
        oled.text("CONSOLE", 39, 27)
        oled.text("READY!", 46, 45)
        oled.show()

        time.sleep_ms(100)