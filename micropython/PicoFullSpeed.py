# ============================================================
# PicoFullSpeed.py
# Game "Full Speed" by Kuba & Stepan
#
# Raspberry Pi Pico 2 Retro Gaming Console
#
# FIXED CONTROLS
#
# UP       GP2  -> Reserved
# DOWN     GP3  -> Reserved
# LEFT     GP4  -> Move left
# RIGHT    GP5  -> Move right
# A        GP6  -> Start / Restart
# B        GP7  -> BACK / EXIT
# START    GP8  -> PAUSE / RESUME
# SELECT   GP9  -> QUICK SAVE
#
# OLED
# SDA      GP0
# SCL      GP1
#
# BUZZER
# GP15
# ============================================================

from machine import Pin, SoftI2C, PWM
from ssd1306 import SSD1306_I2C

import time
import random
import save_manager


# ============================================================
# DISPLAY
# ============================================================

WIDTH = 128
HEIGHT = 64


i2c = SoftI2C(
    sda=Pin(0),
    scl=Pin(1),
    freq=100000
)

oled = SSD1306_I2C(
    WIDTH,
    HEIGHT,
    i2c,
    addr=0x3C
)


# ============================================================
# BUTTONS
# ============================================================

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


# ============================================================
# BUZZER
# ============================================================

buzzer = PWM(
    Pin(15)
)

buzzer.duty_u16(0)


def beep(
    frequency,
    duration
):

    if frequency <= 0:

        buzzer.duty_u16(0)

        return

    buzzer.freq(
        frequency
    )

    buzzer.duty_u16(
        2000
    )

    time.sleep_ms(
        duration
    )

    buzzer.duty_u16(0)


# ============================================================
# LEVELS
# ============================================================

LEVEL_NAMES = [
    "EASY",
    "MEDIUM",
    "HARD"
]


# Base delay between frames.
#
# Smaller value = faster game.
#
LEVEL_DELAY = [
    120,
    100,
    75
]


# Speed multiplier for obstacle movement.
LEVEL_SPEED = [
    0.75,
    1.00,
    1.30
]


# ============================================================
# GAME VARIABLES
# ============================================================

current_level = 1
score = 0

x = 1
y = 1

prekazka = 1
ran = 0

direction3 = 1

x_pos = 2
tilt = 0

speed = 1
acceleration = 1

y_rival = 0
crasch = 0


# ============================================================
# BUTTON RELEASE
# ============================================================

def wait_release():

    while (
        UP.value() == 0
        or DOWN.value() == 0
        or LEFT.value() == 0
        or RIGHT.value() == 0
        or A.value() == 0
        or B.value() == 0
        or START.value() == 0
        or SELECT.value() == 0
    ):

        time.sleep_ms(20)


# ============================================================
# RESET GAME
# ============================================================

def reset_game():

    global x
    global y
    global prekazka
    global ran
    global direction3
    global x_pos
    global tilt
    global score
    global speed
    global acceleration
    global y_rival
    global crasch


    x = 1
    y = 1

    prekazka = 1
    ran = 0

    direction3 = 1

    x_pos = 2
    tilt = 0

    score = 1

    speed = 1
    acceleration = 1

    y_rival = 0

    crasch = 0


# ============================================================
# SAVE STATE
# ============================================================

def create_save_state():

    state = {

        "x": x,

        "y": y,

        "prekazka": prekazka,

        "ran": ran,

        "direction3": direction3,

        "x_pos": x_pos,

        "tilt": tilt,

        "speed": speed,

        "acceleration": acceleration,

        "y_rival": y_rival,

        "crasch": crasch
    }

    return state


# ============================================================
# RESTORE STATE
# ============================================================

def restore_state(
    saved_score,
    saved_state
):

    global score

    global x
    global y
    global prekazka
    global ran
    global direction3
    global x_pos
    global tilt
    global speed
    global acceleration
    global y_rival
    global crasch


    if saved_state is None:

        return False


    try:

        x = saved_state["x"]

        y = saved_state["y"]

        prekazka = saved_state["prekazka"]

        ran = saved_state["ran"]

        direction3 = saved_state["direction3"]

        x_pos = saved_state["x_pos"]

        tilt = saved_state["tilt"]

        speed = saved_state["speed"]

        acceleration = saved_state["acceleration"]

        y_rival = saved_state["y_rival"]

        crasch = saved_state["crasch"]

        score = int(
            saved_score
        )

        return True

    except Exception:

        return False


# ============================================================
# QUICK SAVE
# ============================================================

def quick_save():

    global current_level
    global score


    state = create_save_state()


    save_manager.save_game(
        "Full Speed",
        current_level,
        score,
        state
    )


    beep(
        1000,
        50
    )

    beep(
        1400,
        60
    )


    oled.fill(0)

    oled.text(
        "GAME SAVED",
        25,
        18
    )

    oled.text(
        LEVEL_NAMES[current_level],
        42,
        34
    )

    oled.show()

    time.sleep_ms(700)


# ============================================================
# TITLE SCREEN
# ============================================================

def title_screen():

    while True:

        oled.fill(0)

        oled.text(
            "FULL SPEED",
            28,
            5
        )

        oled.text(
            "BY KUBA",
            35,
            18
        )

        oled.text(
            "& STEPAN",
            32,
            30
        )

        oled.rect(
            0,
            0,
            128,
            44,
            1
        )

        oled.text(
            "A START",
            10,
            51
        )

        oled.text(
            "B BACK",
            78,
            51
        )

        oled.show()


        # ----------------------------------------------------
        # A = START
        # ----------------------------------------------------

        if A.value() == 0:

            wait_release()

            return True


        # ----------------------------------------------------
        # B = BACK
        # ----------------------------------------------------

        if B.value() == 0:

            wait_release()

            return False


        time.sleep_ms(30)


# ============================================================
# PAUSE MENU
# ============================================================

def pause_menu():

    selected = 0


    items = [
        "RESUME",
        "SAVE GAME",
        "EXIT"
    ]


    while True:

        oled.fill(0)


        oled.text(
            "FULL SPEED",
            22,
            0
        )

        oled.text(
            "PAUSED",
            43,
            11
        )


        for i in range(3):

            y_pos = 23 + i * 10


            if i == selected:

                oled.fill_rect(
                    8,
                    y_pos - 1,
                    112,
                    10,
                    1
                )

                oled.text(
                    "> " + items[i],
                    15,
                    y_pos,
                    0
                )

            else:

                oled.text(
                    "  " + items[i],
                    15,
                    y_pos,
                    1
                )


        oled.text(
            "A SELECT",
            4,
            55
        )

        oled.text(
            "B BACK",
            82,
            55
        )

        oled.show()


        # ----------------------------------------------------
        # UP
        # ----------------------------------------------------

        if UP.value() == 0:

            selected -= 1

            if selected < 0:

                selected = 2

            wait_release()


        # ----------------------------------------------------
        # DOWN
        # ----------------------------------------------------

        elif DOWN.value() == 0:

            selected += 1

            if selected > 2:

                selected = 0

            wait_release()


        # ----------------------------------------------------
        # A
        # ----------------------------------------------------

        elif A.value() == 0:

            wait_release()

            return items[selected]


        # ----------------------------------------------------
        # B
        # ----------------------------------------------------

        elif B.value() == 0:

            wait_release()

            return "RESUME"


        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        elif START.value() == 0:

            wait_release()

            return "RESUME"


        time.sleep_ms(30)


# ============================================================
# GAME OVER SCREEN
# ============================================================

def game_over_screen():

    global score
    global current_level


    # --------------------------------------------------------
    # Update high score
    # --------------------------------------------------------

    try:

        new_record = save_manager.update_high_score(
            "Full Speed",
            current_level,
            score
        )

    except:

        new_record = False


    beep(
        180,
        150
    )

    time.sleep_ms(100)

    beep(
        120,
        200
    )


    # --------------------------------------------------------
    # Game over loop
    # --------------------------------------------------------

    while True:

        oled.fill(0)


        oled.text(
            "GAME OVER",
            25,
            10
        )


        oled.text(
            "SCORE:",
            20,
            27
        )

        oled.text(
            str(score),
            78,
            27
        )


        oled.text(
            LEVEL_NAMES[current_level],
            44,
            38
        )


        if new_record:

            oled.text(
                "NEW HIGH SCORE!",
                8,
                49
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


        # ----------------------------------------------------
        # A = RESTART
        # ----------------------------------------------------

        if A.value() == 0:

            wait_release()

            return "AGAIN"


        # ----------------------------------------------------
        # B = BACK
        # ----------------------------------------------------

        if B.value() == 0:

            wait_release()

            return "BACK"


        # START also returns to pause/restart flow
        # but does not change the fixed meaning during game.
        #
        # Here we simply ignore it.

        time.sleep_ms(30)


# ============================================================
# DRAW GAME
# ============================================================

def draw_game():

    global x_pos
    global x
    global y
    global prekazka
    global tilt
    global y_rival


    # --------------------------------------------------------
    # CLEAR SCREEN
    # --------------------------------------------------------

    oled.fill(0)

    tilt = 0


    # --------------------------------------------------------
    # PLAYER LEFT
    # --------------------------------------------------------

    if LEFT.value() == 0:

        x_pos -= 2

        tilt = -4


    # --------------------------------------------------------
    # PLAYER RIGHT
    # --------------------------------------------------------

    if RIGHT.value() == 0:

        x_pos += 2

        tilt = 4


    # --------------------------------------------------------
    # PLAYER BOUNDARY
    # --------------------------------------------------------

    if x_pos < -46:

        x_pos = -46


    if x_pos > 46:

        x_pos = 46


    # --------------------------------------------------------
    # RIVAL POSITION
    # --------------------------------------------------------

    y_rival = ran + y


    # --------------------------------------------------------
    # HUD
    # --------------------------------------------------------

    oled.text(
        "Score:" + str(score),
        0,
        0
    )

    speed_display = int(
        score
        *
        5
        *
        LEVEL_SPEED[current_level]
    )

    oled.text(
        str(speed_display) + " km/h",
        70,
        0
    )


    # --------------------------------------------------------
    # GAME MOVEMENT
    # --------------------------------------------------------

    x += 1

    y += direction3


    # --------------------------------------------------------
    # DIFFICULTY MULTIPLIER
    # --------------------------------------------------------

    prekazka += (
        speed
        *
        LEVEL_SPEED[current_level]
    )


    # --------------------------------------------------------
    # HORIZON
    # --------------------------------------------------------

    oled.line(
        20 + y // 5,
        35 + y // 10,
        9 + y // 4,
        39 + y // 10,
        1
    )

    oled.line(
        20 + y // 5,
        35 + y // 10,
        29 + y // 4,
        39 + y // 10,
        1
    )


    # --------------------------------------------------------
    # ROAD
    # --------------------------------------------------------

    oled.rect(
        0,
        40 + y // 10,
        128,
        2,
        1
    )

    oled.line(
        50 + y,
        40 + y // 10,
        30,
        50,
        1
    )

    oled.line(
        70 + y,
        40 + y // 10,
        90,
        50,
        1
    )

    oled.line(
        30,
        50,
        10,
        63,
        1
    )

    oled.line(
        90,
        50,
        118,
        63,
        1
    )


    # --------------------------------------------------------
    # ROAD ANIMATION
    # --------------------------------------------------------

    oled.rect(
        0,
        42 + x // 2,
        128,
        4,
        0
    )

    oled.rect(
        0,
        52 + x,
        128,
        8,
        0
    )


    # --------------------------------------------------------
    # PLAYER MOTORCYCLE
    # --------------------------------------------------------

    oled.rect(
        60 + x_pos,
        58,
        2,
        4,
        1
    )

    oled.rect(
        59 + x_pos + tilt // 2,
        55,
        5,
        4,
        1
    )

    oled.rect(
        60 + x_pos + tilt,
        52,
        2,
        2,
        1
    )


    # --------------------------------------------------------
    # RIVAL
    # --------------------------------------------------------

    if prekazka > 10:

        oled.rect(
            60 + ran + y,
            38 + int(prekazka),
            2,
            4,
            1
        )

        oled.rect(
            59 + y // 20 + ran + y,
            35 + int(prekazka),
            5,
            4,
            1
        )

        oled.rect(
            60 + y // 10 + ran + y,
            32 + int(prekazka),
            2,
            2,
            1
        )

    else:

        oled.rect(
            60 + ran + y,
            38 + int(prekazka),
            2,
            4,
            1
        )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    oled.show()
# ============================================================
# UPDATE GAME
# ============================================================

def update_game():

    global x
    global y
    global prekazka
    global ran
    global direction3
    global x_pos
    global score
    global acceleration
    global speed
    global crasch


    # --------------------------------------------------------
    # FRAME ANIMATION
    # --------------------------------------------------------

    if x >= 4:

        x = 0


    # --------------------------------------------------------
    # NEW OBSTACLE
    # --------------------------------------------------------

    if prekazka >= 30:

        ran = random.randint(
            -5,
            5
        )

        ran *= 2


        prekazka = 0


        # Original scoring:
        # +1 for every successfully passed obstacle.

        score += 1


        # Increase acceleration.

        acceleration += 0.05


        speed = round(
            acceleration
        )


        beep(
            700,
            15
        )


    # --------------------------------------------------------
    # ROAD MOVEMENT
    # --------------------------------------------------------

    if y <= -35 or y >= 25:

        direction3 = -direction3


    if y <= -15:

        x_pos += 2


    if y > 15:

        x_pos -= 2


    # --------------------------------------------------------
    # PLAYER OUT OF ROAD
    # --------------------------------------------------------

    if (
        x_pos >= 46
        or
        x_pos < -46
    ):

        crasch = 1


    # --------------------------------------------------------
    # PLAYER / RIVAL COLLISION
    # --------------------------------------------------------

    if (
        x_pos <= y_rival + 4
        and
        x_pos >= y_rival - 4
        and
        prekazka >= 15
    ):

        crasch = 1


# ============================================================
# MAIN GAME
# ============================================================

def pico_full_speed_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    global current_level
    global score


    # --------------------------------------------------------
    # Set level
    # --------------------------------------------------------

    current_level = int(
        level
    )


    if current_level < 0:

        current_level = 0


    if current_level > 2:

        current_level = 2


    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    resumed = False


    if (
        saved_state is not None
        and
        isinstance(
            saved_state,
            dict
        )
    ):

        resumed = restore_state(
            saved_score,
            saved_state
        )


    # --------------------------------------------------------
    # NEW GAME
    # --------------------------------------------------------

    if not resumed:

        reset_game()


        # ----------------------------------------------------
        # START SCREEN
        # ----------------------------------------------------

        if not title_screen():

            return


    # --------------------------------------------------------
    # RESUME SCREEN
    # --------------------------------------------------------

    else:

        oled.fill(0)

        oled.text(
            "RESUMING",
            35,
            10
        )

        oled.text(
            LEVEL_NAMES[current_level],
            42,
            27
        )

        oled.text(
            "SCORE " + str(score),
            28,
            42
        )

        oled.show()

        time.sleep_ms(800)


    # ========================================================
    # MAIN GAME LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        draw_game()


        # ----------------------------------------------------
        # B
        #
        # FIXED:
        # BACK / EXIT
        # ----------------------------------------------------

        if B.value() == 0:

            wait_release()

            buzzer.duty_u16(0)

            oled.fill(0)

            oled.show()

            return


        # ----------------------------------------------------
        # START
        #
        # FIXED:
        # PAUSE / RESUME
        # ----------------------------------------------------

        if START.value() == 0:

            wait_release()


            action = pause_menu()


            if action == "SAVE GAME":

                quick_save()


            elif action == "EXIT":

                buzzer.duty_u16(0)

                oled.fill(0)

                oled.show()

                return


        # ----------------------------------------------------
        # SELECT
        #
        # FIXED:
        # QUICK SAVE
        # ----------------------------------------------------

        if SELECT.value() == 0:

            wait_release()

            quick_save()


        # ----------------------------------------------------
        # UPDATE GAME
        # ----------------------------------------------------

        update_game()


        # ----------------------------------------------------
        # COLLISION
        # ----------------------------------------------------

        if crasch == 1:

            result = game_over_screen()


            # ------------------------------------------------
            # RESTART
            # ------------------------------------------------

            if result == "AGAIN":

                reset_game()

                continue


            # ------------------------------------------------
            # BACK
            # ------------------------------------------------

            if result == "BACK":

                buzzer.duty_u16(0)

                oled.fill(0)

                oled.show()

                return


        # ----------------------------------------------------
        # FRAME DELAY
        # ----------------------------------------------------

        time.sleep_ms(
            LEVEL_DELAY[current_level]
        )


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    pico_full_speed_main(
        level=1,
        saved_score=0,
        saved_state=None
    )