# ============================================================
# PicoPong.py
# Upgraded Pong for Raspberry Pi Pico 2
#
# Controls:
#
# LEFT    GP4  -> Move paddle left
# RIGHT   GP5  -> Move paddle right
# A       GP6  -> Start / Select
# B       GP7  -> Back
# START   GP8  -> Pause / Resume
# SELECT  GP9  -> Quick Save
#
# OLED:
# SDA     GP0
# SCL     GP1
#
# BUZZER:
# GP15
#
# Levels:
#   0 = EASY
#   1 = MEDIUM
#   2 = HARD
#
# Score:
#   +1 for every successful paddle hit
#
# ============================================================

from machine import Pin, PWM, SoftI2C
from ssd1306 import SSD1306_I2C

import time
import random
import save_manager


# ============================================================
# MAIN GAME
# ============================================================

def pico_pong_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    # ========================================================
    # DISPLAY
    # ========================================================

    SCREEN_WIDTH = 128
    SCREEN_HEIGHT = 64


    # ========================================================
    # GAME OBJECT SIZE
    # ========================================================

    BALL_SIZE = 3

    PADDLE_WIDTH = 20

    PADDLE_HEIGHT = 4

    PADDLE_Y = 56


    # ========================================================
    # BUTTONS
    # ========================================================

    UP = Pin(
        2,
        Pin.IN,
        Pin.PULL_UP
    )

    DOWN = Pin(
        3,
        Pin.IN,
        Pin.PULL_UP
    )

    LEFT = Pin(
        4,
        Pin.IN,
        Pin.PULL_UP
    )

    RIGHT = Pin(
        5,
        Pin.IN,
        Pin.PULL_UP
    )

    A = Pin(
        6,
        Pin.IN,
        Pin.PULL_UP
    )

    B = Pin(
        7,
        Pin.IN,
        Pin.PULL_UP
    )

    START = Pin(
        8,
        Pin.IN,
        Pin.PULL_UP
    )

    SELECT = Pin(
        9,
        Pin.IN,
        Pin.PULL_UP
    )


    # ========================================================
    # BUZZER
    # ========================================================

    buzzer = PWM(
        Pin(15)
    )

    buzzer.duty_u16(0)


    # ========================================================
    # OLED
    # ========================================================

    i2c = SoftI2C(
        scl=Pin(1),
        sda=Pin(0),
        freq=100000
    )

    oled = SSD1306_I2C(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        i2c,
        addr=0x3C
    )


    # ========================================================
    # LEVEL SETTINGS
    # ========================================================

    if level == 0:

        level_name = "EASY"

        initial_speed = 1.15

        max_speed = 2.40

        paddle_speed = 2.5

        acceleration = 0.035

    elif level == 1:

        level_name = "MEDIUM"

        initial_speed = 1.50

        max_speed = 3.20

        paddle_speed = 3.0

        acceleration = 0.055

    else:

        level_name = "HARD"

        initial_speed = 1.90

        max_speed = 4.20

        paddle_speed = 3.5

        acceleration = 0.080


    # ========================================================
    # SOUND
    # ========================================================

    def beep(
        frequency,
        duration,
        volume=1800
    ):

        buzzer.freq(
            frequency
        )

        buzzer.duty_u16(
            volume
        )

        time.sleep_ms(
            duration
        )

        buzzer.duty_u16(0)


    def paddle_sound():

        beep(
            750,
            20
        )


    def wall_sound():

        beep(
            450,
            15
        )


    def save_sound():

        beep(
            900,
            40
        )

        beep(
            1200,
            50
        )


    def error_sound():

        beep(
            180,
            150
        )


    def gameover_sound():

        beep(
            300,
            100
        )

        beep(
            200,
            180
        )


    # ========================================================
    # TEXT HELPER
    # ========================================================

    def center_text(
        text,
        y
    ):

        x = 64 - (
            len(text) * 4
        )

        if x < 0:
            x = 0

        oled.text(
            text,
            x,
            y
        )


    # ========================================================
    # WAIT RELEASE
    # ========================================================

    def wait_release():

        while (
            A.value() == 0 or
            B.value() == 0 or
            START.value() == 0 or
            SELECT.value() == 0 or
            LEFT.value() == 0 or
            RIGHT.value() == 0
        ):

            time.sleep_ms(20)


    # ========================================================
    # SAVE CURRENT GAME
    # ========================================================

    def save_current_game():

        state = {

            "ballX": int(ballX),

            "ballY": int(ballY),

            "ballVX": float(ballVX),

            "ballVY": float(ballVY),

            "paddleX": int(paddleX)
        }


        save_manager.save_game(
            "Pong",
            level,
            score,
            state
        )

        save_sound()


        # ----------------------------------------------------
        # SAVE SCREEN
        # ----------------------------------------------------

        oled.fill(0)

        center_text(
            "GAME SAVED",
            20
        )

        center_text(
            level_name,
            34
        )

        oled.show()

        time.sleep_ms(700)


    # ========================================================
    # RESTORE SAVED GAME
    # ========================================================

    resumed_game = False


    if (
        saved_state is not None
        and
        len(saved_state) > 0
    ):

        try:

            ballX = float(
                saved_state["ballX"]
            )

            ballY = float(
                saved_state["ballY"]
            )

            ballVX = float(
                saved_state["ballVX"]
            )

            ballVY = float(
                saved_state["ballVY"]
            )

            paddleX = float(
                saved_state["paddleX"]
            )

            score = int(
                saved_score
            )

            resumed_game = True

        except:

            resumed_game = False


    # ========================================================
    # NEW GAME INITIAL STATE
    # ========================================================

    if not resumed_game:

        ballX = 64

        ballY = 30

        paddleX = 54

        score = 0

        ballVX = initial_speed

        ballVY = initial_speed


        # Random horizontal direction

        if random.randint(
            0,
            1
        ) == 0:

            ballVX = -initial_speed


    # ========================================================
    # CURRENT SPEED
    # ========================================================

    speed = abs(ballVY)


    if speed < initial_speed:

        speed = initial_speed


    # ========================================================
    # START SCREEN
    # ========================================================

    if not resumed_game:

        oled.fill(0)

        center_text(
            "PONG",
            8
        )

        center_text(
            level_name,
            22
        )

        oled.text(
            "A = START",
            25,
            40
        )

        oled.text(
            "B = BACK",
            25,
            53
        )

        oled.show()


        while True:

            # ----------------------------------------------
            # B = BACK
            # ----------------------------------------------

            if B.value() == 0:

                wait_release()

                buzzer.duty_u16(0)

                return


            # ----------------------------------------------
            # A = START
            # ----------------------------------------------

            if A.value() == 0:

                wait_release()

                break


            time.sleep_ms(20)


    else:

        # ----------------------------------------------------
        # Resume screen
        # ----------------------------------------------------

        oled.fill(0)

        center_text(
            "RESUMING",
            12
        )

        center_text(
            level_name,
            28
        )

        center_text(
            "SCORE " + str(score),
            42
        )

        oled.show()

        time.sleep_ms(800)


    # ========================================================
    # MAIN GAME LOOP
    # ========================================================

    while True:


        # ====================================================
        # START = PAUSE
        # ====================================================

        if START.value() == 0:

            wait_release()

            result = pause_menu()


            if result == "EXIT":

                buzzer.duty_u16(0)

                return


            if result == "SAVE":

                save_current_game()


            # Continue game

            continue


        # ====================================================
        # SELECT = QUICK SAVE
        # ====================================================

        if SELECT.value() == 0:

            wait_release()

            save_current_game()

            continue


        # ====================================================
        # B = BACK
        # ====================================================

        if B.value() == 0:

            wait_release()

            buzzer.duty_u16(0)

            return


        # ====================================================
        # MOVE PADDLE
        # ====================================================

        if RIGHT.value() == 0:

            paddleX += paddle_speed


        elif LEFT.value() == 0:

            paddleX -= paddle_speed


        # Keep paddle inside screen

        if paddleX < 0:

            paddleX = 0


        if (
            paddleX +
            PADDLE_WIDTH >
            SCREEN_WIDTH
        ):

            paddleX = (
                SCREEN_WIDTH -
                PADDLE_WIDTH
            )


        # ====================================================
        # MOVE BALL
        # ====================================================

        ballX += ballVX

        ballY += ballVY


        collision = False


        # ====================================================
        # LEFT WALL
        # ====================================================

        if ballX <= 0:

            ballX = 0

            ballVX = abs(
                ballVX
            )

            collision = True

            wall_sound()


        # ====================================================
        # RIGHT WALL
        # ====================================================

        if (
            ballX +
            BALL_SIZE >=
            SCREEN_WIDTH
        ):

            ballX = (
                SCREEN_WIDTH -
                BALL_SIZE
            )

            ballVX = -abs(
                ballVX
            )

            collision = True

            wall_sound()


        # ====================================================
        # TOP WALL
        # ====================================================

        if ballY <= 11:

            ballY = 11

            ballVY = abs(
                ballVY
            )

            collision = True

            wall_sound()


        # ====================================================
        # PADDLE COLLISION
        # ====================================================

        if (
            ballY + BALL_SIZE >= PADDLE_Y
            and
            ballY <= PADDLE_Y + PADDLE_HEIGHT
            and
            ballX + BALL_SIZE >= paddleX
            and
            ballX <= paddleX + PADDLE_WIDTH
            and
            ballVY > 0
        ):

            # ------------------------------------------------
            # Move ball above paddle
            # ------------------------------------------------

            ballY = (
                PADDLE_Y -
                BALL_SIZE
            )


            # ------------------------------------------------
            # Reverse Y direction
            # ------------------------------------------------

            ballVY = -abs(
                ballVY
            )


            # ------------------------------------------------
            # Calculate hit position
            # ------------------------------------------------

            paddle_center = (
                paddleX +
                PADDLE_WIDTH / 2
            )

            ball_center = (
                ballX +
                BALL_SIZE / 2
            )

            hit_position = (
                ball_center -
                paddle_center
            ) / (
                PADDLE_WIDTH / 2
            )


            # ------------------------------------------------
            # Change horizontal direction
            # ------------------------------------------------

            ballVX += (
                hit_position * 0.75
            )


            # Prevent vertical trajectory

            if abs(ballVX) < 0.5:

                if ballVX < 0:

                    ballVX = -0.5

                else:

                    ballVX = 0.5


            # ------------------------------------------------
            # SCORE +1
            # ------------------------------------------------

            score += 1


            # ------------------------------------------------
            # Increase difficulty
            # ------------------------------------------------

            speed += acceleration


            if speed > max_speed:

                speed = max_speed


            # ------------------------------------------------
            # Maintain speed
            # ------------------------------------------------

            if ballVY < 0:

                ballVY = -speed

            else:

                ballVY = speed


            # Limit X velocity

            if abs(ballVX) > max_speed:

                if ballVX < 0:

                    ballVX = -max_speed

                else:

                    ballVX = max_speed


            paddle_sound()


        # ====================================================
        # BALL LOST
        # ====================================================

        if ballY + BALL_SIZE >= SCREEN_HEIGHT:


            buzzer.duty_u16(0)


            gameover_sound()


            # ------------------------------------------------
            # Update high score
            # ------------------------------------------------

            new_high_score = (
                save_manager.update_high_score(
                    "Pong",
                    level,
                    score
                )
            )


            # ------------------------------------------------
            # Game over screen
            # ------------------------------------------------

            oled.fill(0)


            center_text(
                "GAME OVER",
                8
            )


            oled.text(
                "SCORE",
                45,
                22
            )

            center_text(
                str(score),
                34
            )


            if new_high_score:

                center_text(
                    "NEW HIGH SCORE!",
                    47
                )

            else:

                oled.text(
                    "A AGAIN",
                    8,
                    54
                )

                oled.text(
                    "B BACK",
                    78,
                    54
                )


            oled.show()


            # ------------------------------------------------
            # Wait
            # ------------------------------------------------

            while True:

                if A.value() == 0:

                    wait_release()

                    break


                if B.value() == 0:

                    wait_release()

                    return


                time.sleep_ms(20)


            # Start fresh game

            ballX = 64

            ballY = 30

            paddleX = 54

            score = 0

            speed = initial_speed

            ballVX = initial_speed

            ballVY = initial_speed


            if random.randint(
                0,
                1
            ) == 0:

                ballVX = -initial_speed


            continue


        # ====================================================
        # DRAW GAME
        # ====================================================

        oled.fill(0)


        # ----------------------------------------------------
        # HUD
        # ----------------------------------------------------

        oled.text(
            "PONG",
            2,
            1
        )

        oled.text(
            level_name,
            46,
            1
        )

        oled.text(
            str(score),
            116 - len(str(score)) * 4,
            1
        )


        # ----------------------------------------------------
        # Top separator
        # ----------------------------------------------------

        oled.hline(
            0,
            10,
            128,
            1
        )


        # ----------------------------------------------------
        # Paddle
        # ----------------------------------------------------

        oled.fill_rect(
            int(paddleX),
            PADDLE_Y,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
            1
        )


        # ----------------------------------------------------
        # Ball
        # ----------------------------------------------------

        oled.fill_rect(
            int(ballX),
            int(ballY),
            BALL_SIZE,
            BALL_SIZE,
            1
        )


        # ----------------------------------------------------
        # Small score marker
        # ----------------------------------------------------

        oled.text(
            "+1",
            2,
            54
        )


        oled.show()


        # ====================================================
        # FRAME RATE
        # ====================================================

        time.sleep_ms(12)

        buzzer.duty_u16(0)


# ============================================================
# PAUSE MENU
# ============================================================

def pause_menu():

    # Re-create buttons locally

    UP = Pin(
        2,
        Pin.IN,
        Pin.PULL_UP
    )

    DOWN = Pin(
        3,
        Pin.IN,
        Pin.PULL_UP
    )

    A = Pin(
        6,
        Pin.IN,
        Pin.PULL_UP
    )

    B = Pin(
        7,
        Pin.IN,
        Pin.PULL_UP
    )


    items = [
        "RESUME",
        "SAVE GAME",
        "EXIT"
    ]

    selected = 0


    while True:

        oled = SSD1306_I2C(
            128,
            64,
            SoftI2C(
                scl=Pin(1),
                sda=Pin(0),
                freq=100000
            ),
            addr=0x3C
        )


        oled.fill(0)


        # Header

        oled.fill_rect(
            0,
            0,
            128,
            10,
            1
        )

        oled.text(
            "PAUSED",
            43,
            1,
            0
        )


        # Menu

        for i in range(3):

            y = 17 + i * 11


            if i == selected:

                oled.fill_rect(
                    5,
                    y - 1,
                    118,
                    10,
                    1
                )

                oled.text(
                    "> " + items[i],
                    15,
                    y,
                    0
                )

            else:

                oled.text(
                    "  " + items[i],
                    15,
                    y,
                    1
                )


        oled.text(
            "A SELECT",
            4,
            55
        )

        oled.show()


        # ----------------------------------------------------
        # UP
        # ----------------------------------------------------

        if UP.value() == 0:

            if selected > 0:

                selected -= 1

            while UP.value() == 0:

                time.sleep_ms(20)


        # ----------------------------------------------------
        # DOWN
        # ----------------------------------------------------

        elif DOWN.value() == 0:

            if selected < 2:

                selected += 1

            while DOWN.value() == 0:

                time.sleep_ms(20)


        # ----------------------------------------------------
        # A
        # ----------------------------------------------------

        elif A.value() == 0:

            while A.value() == 0:

                time.sleep_ms(20)

            return items[selected]


        # ----------------------------------------------------
        # B
        # ----------------------------------------------------

        elif B.value() == 0:

            while B.value() == 0:

                time.sleep_ms(20)

            return "RESUME"


        time.sleep_ms(30)


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    pico_pong_main(
        level=1,
        saved_score=0,
        saved_state=None
    )