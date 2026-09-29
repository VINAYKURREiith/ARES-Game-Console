# ============================================================
# PicoGame.py
# 
# Adapted for:
# Raspberry Pi Pico 2
# SSD1306 128x64 OLED
# SoftI2C GP0 (SDA) / GP1 (SCL)
# Buzzer GP15
#
# FIXED CONTROLS FOR ALL GAMES
#
# GP2  = UP
# GP3  = DOWN
# GP4  = LEFT
# GP5  = RIGHT
# GP6  = A
# GP7  = B / BACK
# GP8  = START / PAUSE
# GP9  = SELECT / QUICK SAVE
#
# POWER SAVING
# 60 seconds with no button activity:
# OLED OFF
# Buzzer OFF
# Pico LIGHTSLEEP
# Any button wakes the Pico
#
# ============================================================

from machine import Pin, PWM, SoftI2C
import machine

from ssd1306 import SSD1306_I2C
from framebuf import FrameBuffer, MONO_HLSB

import time
import random


# ============================================================
# PicoGame
# ============================================================

class PicoGame(SSD1306_I2C):


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        # ----------------------------------------------------
        # OLED
        # ----------------------------------------------------

        self.SCREEN_WIDTH = 128
        self.SCREEN_HEIGHT = 64


        # ----------------------------------------------------
        # BUTTONS
        #
        # GPIO -> button -> GND
        # Internal pull-ups are used.
        # ----------------------------------------------------

        self.__up = Pin(
            2,
            Pin.IN,
            Pin.PULL_UP
        )

        self.__down = Pin(
            3,
            Pin.IN,
            Pin.PULL_UP
        )

        self.__left = Pin(
            4,
            Pin.IN,
            Pin.PULL_UP
        )

        self.__right = Pin(
            5,
            Pin.IN,
            Pin.PULL_UP
        )


        # ----------------------------------------------------
        # A / B
        # ----------------------------------------------------

        self.__button_A = Pin(
            6,
            Pin.IN,
            Pin.PULL_UP
        )

        self.__button_B = Pin(
            7,
            Pin.IN,
            Pin.PULL_UP
        )


        # ----------------------------------------------------
        # START / SELECT
        # ----------------------------------------------------

        self.__button_START = Pin(
            8,
            Pin.IN,
            Pin.PULL_UP
        )

        self.__button_SELECT = Pin(
            9,
            Pin.IN,
            Pin.PULL_UP
        )


        # ----------------------------------------------------
        # BUZZER
        # ----------------------------------------------------

        self.__buzzer = PWM(
            Pin(15)
        )

        # Buzzer OFF

        self.__buzzer.duty_u16(0)


        # ----------------------------------------------------
        # OLED I2C
        #
        # GP0 = SDA
        # GP1 = SCL
        # ----------------------------------------------------

        self.__i2c = SoftI2C(
            sda=Pin(0),
            scl=Pin(1),
            freq=100000
        )


        # ----------------------------------------------------
        # SSD1306
        # ----------------------------------------------------

        super().__init__(
            self.SCREEN_WIDTH,
            self.SCREEN_HEIGHT,
            self.__i2c,
            addr=0x3C
        )


        # ----------------------------------------------------
        # SPRITE STORAGE
        # ----------------------------------------------------

        self.__fb = []

        self.__w = []

        self.__h = []


        # ----------------------------------------------------
        # SOUND
        # ----------------------------------------------------

        self.__mute = False


        # ====================================================
        # POWER SAVING
        # ====================================================

        # 60 seconds
        self.__POWER_SAVE_TIMEOUT = 60000

        # Last user activity time
        self.__last_activity = time.ticks_ms()

        # Prevent repeated sleep entry
        self.__sleeping = False


    # ========================================================
    # TEXT FUNCTIONS
    # ========================================================

    def center_text(
        self,
        s,
        color=1
    ):

        x = (
            int(self.width / 2)
            -
            int(len(s) / 2 * 8)
        )

        y = (
            int(self.height / 2)
            - 8
        )

        self.text(
            s,
            x,
            y,
            color
        )


    # --------------------------------------------------------
    # Center text at custom Y position
    # --------------------------------------------------------

    def center_text_y(
        self,
        s,
        y,
        color=1
    ):

        x = (
            int(self.width / 2)
            -
            int(len(s) / 2 * 8)
        )

        self.text(
            s,
            x,
            y,
            color
        )


    # --------------------------------------------------------
    # Top-right text
    # --------------------------------------------------------

    def top_right_corner_text(
        self,
        s,
        color=1
    ):

        x = (
            self.width
            -
            int(len(s) * 8)
        )

        y = 0

        self.text(
            s,
            x,
            y,
            color
        )


    # ========================================================
    # SPRITE FUNCTIONS
    # ========================================================

    def add_sprite(
        self,
        buffer,
        w,
        h
    ):

        fb = FrameBuffer(
            buffer,
            w,
            h,
            MONO_HLSB
        )

        self.__fb.append(
            fb
        )

        self.__w.append(
            w
        )

        self.__h.append(
            h
        )

        return len(
            self.__fb
        ) - 1


    def sprite(
        self,
        n,
        x,
        y,
        key=0
    ):

        self.blit(
            self.__fb[n],
            x,
            y,
            key
        )


    def sprite_width(
        self,
        n
    ):

        return self.__w[n]


    def sprite_height(
        self,
        n
    ):

        return self.__h[n]


    # ========================================================
    # SPRITE COLLISION
    # ========================================================

    def sprites_intersection(
        self,
        x1,
        y1,
        w1,
        h1,
        x2,
        y2,
        w2,
        h2
    ):

        overlap = True


        if x2 > x1 + w1 - 1:

            overlap = False


        if x2 + w2 - 1 < x1:

            overlap = False


        if y2 > y1 + h1 - 1:

            overlap = False


        if y2 + h2 - 1 < y1:

            overlap = False


        return overlap


    # --------------------------------------------------------
    # Pixel-level sprite collision
    # --------------------------------------------------------

    def sprites_collision(
        self,
        n,
        x1,
        y1,
        m,
        x2,
        y2
    ):

        if self.sprites_intersection(
            x1,
            y1,
            self.sprite_width(n),
            self.sprite_height(n),
            x2,
            y2,
            self.sprite_width(m),
            self.sprite_height(m)
        ):

            dx = max(
                x1,
                x2
            )

            dy = max(
                y1,
                y2
            )


            dw = min(
                x1 + self.sprite_width(n),
                x2 + self.sprite_width(m)
            ) - dx


            dh = min(
                y1 + self.sprite_height(n),
                y2 + self.sprite_height(m)
            ) - dy


            for j in range(
                dy,
                dy + dh
            ):

                for i in range(
                    dx,
                    dx + dw
                ):

                    if (
                        self.__fb[n].pixel(
                            i - x1,
                            j - y1
                        )
                        and
                        self.__fb[m].pixel(
                            i - x2,
                            j - y2
                        )
                    ):

                        return True


        return False


    # ========================================================
    # POWER SAVING
    # ========================================================

    def __reset_activity(self):

        self.__last_activity = time.ticks_ms()


    # --------------------------------------------------------
    # POWER SAVE CHECK
    # --------------------------------------------------------

    def power_save_check(self):

        # ----------------------------------------------------
        # Do not enter sleep while already sleeping
        # ----------------------------------------------------

        if self.__sleeping:

            return


        # ----------------------------------------------------
        # Detect currently pressed button
        # ----------------------------------------------------

        if (
            self.__up.value() == 0
            or
            self.__down.value() == 0
            or
            self.__left.value() == 0
            or
            self.__right.value() == 0
            or
            self.__button_A.value() == 0
            or
            self.__button_B.value() == 0
            or
            self.__button_START.value() == 0
            or
            self.__button_SELECT.value() == 0
        ):

            self.__reset_activity()

            return


        # ----------------------------------------------------
        # Calculate idle time
        # ----------------------------------------------------

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            self.__last_activity
        )


        # ----------------------------------------------------
        # Enter power saving
        # ----------------------------------------------------

        if (
            elapsed >= self.__POWER_SAVE_TIMEOUT
        ):

            self.__enter_power_save()


    # --------------------------------------------------------
    # ENTER POWER SAVE
    # --------------------------------------------------------

    def __enter_power_save(self):

        self.__sleeping = True


        # ----------------------------------------------------
        # BUZZER OFF
        # ----------------------------------------------------

        self.__buzzer.duty_u16(0)


        # ----------------------------------------------------
        # OLED OFF
        # ----------------------------------------------------

        try:

            self.poweroff()

        except Exception:

            pass


        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        wake_pins = [

            self.__up,
            self.__down,
            self.__left,
            self.__right,
            self.__button_A,
            self.__button_B,
            self.__button_START,
            self.__button_SELECT

        ]


        # ----------------------------------------------------
        # Configure GPIO wake
        # ----------------------------------------------------

        for pin in wake_pins:

            try:

                pin.irq(
                    handler=None,
                    trigger=Pin.IRQ_FALLING,
                    wake=machine.SLEEP
                )

            except Exception:

                pass


        # ----------------------------------------------------
        # LIGHT SLEEP
        # ----------------------------------------------------

        try:

            machine.lightsleep()

        except Exception:

            # Fallback
            time.sleep_ms(100)


        # ----------------------------------------------------
        # Remove wake configuration
        # ----------------------------------------------------

        for pin in wake_pins:

            try:

                pin.irq(
                    handler=None
                )

            except Exception:

                pass


        # ----------------------------------------------------
        # OLED ON
        # ----------------------------------------------------

        try:

            self.poweron()

        except Exception:

            pass


        # ----------------------------------------------------
        # Reset timer
        # ----------------------------------------------------

        self.__reset_activity()

        self.__sleeping = False


        # ----------------------------------------------------
        # Wait for wake-up button release
        #
        # Prevents the wake button from also becoming
        # a game command.
        # ----------------------------------------------------

        self.wait_for_release()


    # ========================================================
    # BUTTON FUNCTIONS
    # ========================================================

    def button_up(self):

        self.power_save_check()

        pressed = (
            self.__up.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    def button_down(self):

        self.power_save_check()

        pressed = (
            self.__down.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    def button_left(self):

        self.power_save_check()

        pressed = (
            self.__left.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    def button_right(self):

        self.power_save_check()

        pressed = (
            self.__right.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    def button_A(self):

        self.power_save_check()

        pressed = (
            self.__button_A.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    # --------------------------------------------------------
    # B = BACK / EXIT
    # --------------------------------------------------------

    def button_B(self):

        self.power_save_check()

        pressed = (
            self.__button_B.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    # --------------------------------------------------------
    # START = PAUSE / RESUME
    # --------------------------------------------------------

    def button_START(self):

        self.power_save_check()

        pressed = (
            self.__button_START.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    # --------------------------------------------------------
    # SELECT = QUICK SAVE
    # --------------------------------------------------------

    def button_SELECT(self):

        self.power_save_check()

        pressed = (
            self.__button_SELECT.value() == 0
        )

        if pressed:

            self.__reset_activity()

        return pressed


    # ========================================================
    # ANY BUTTON
    # ========================================================

    def any_button(self):

        if self.button_up():

            return True


        if self.button_down():

            return True


        if self.button_left():

            return True


        if self.button_right():

            return True


        if self.button_A():

            return True


        if self.button_B():

            return True


        if self.button_START():

            return True


        if self.button_SELECT():

            return True


        return False


    # ========================================================
    # WAIT FOR BUTTON RELEASE
    # ========================================================

    def wait_for_release(self):

        while self.any_button():

            time.sleep_ms(20)


    # ========================================================
    # WAIT FOR ANY BUTTON
    # ========================================================

    def wait_for_button(self):

        while not self.any_button():

            time.sleep_ms(10)


        self.wait_for_release()


    # ========================================================
    # SOUND
    # ========================================================

    def sound(
        self,
        freq,
        duty_u16=2000
    ):

        if self.__mute:

            self.__buzzer.duty_u16(0)

            return


        if freq > 0:

            self.__buzzer.freq(
                freq
            )

            self.__buzzer.duty_u16(
                duty_u16
            )

        else:

            self.__buzzer.duty_u16(
                0
            )


    # ========================================================
    # MUTE
    # ========================================================

    def mute(
        self,
        value=True
    ):

        self.__mute = value


        if value:

            self.__buzzer.duty_u16(
                0
            )


    # ========================================================
    # STOP SOUND
    # ========================================================

    def stop_sound(self):

        self.__buzzer.duty_u16(
            0
        )


# ============================================================
# END PicoGame.py
# ============================================================