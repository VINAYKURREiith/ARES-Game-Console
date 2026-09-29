# ============================================================
# PICO GAME CONSOLE - MAIN CONTROLLER
#
# 8 BUTTON VERSION
#
# UP       GP2
# DOWN     GP3
# LEFT     GP4
# RIGHT    GP5
# A        GP6
# B        GP7
# START    GP8
# SELECT   GP9
#
# OLED:
# SDA      GP0
# SCL      GP1
#
# ============================================================

from machine import Pin, SoftI2C

import ssd1306
import time
import boot_animation
import save_manager


# ============================================================
# OLED
# ============================================================

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

i2c = SoftI2C(
    scl=Pin(1),
    sda=Pin(0),
    freq=100000
)

oled = ssd1306.SSD1306_I2C(
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    i2c,
    addr=0x3C
)


# ============================================================
# BUTTONS
# ============================================================

UP = Pin(2, Pin.IN, Pin.PULL_UP)
DOWN = Pin(3, Pin.IN, Pin.PULL_UP)

LEFT = Pin(4, Pin.IN, Pin.PULL_UP)
RIGHT = Pin(5, Pin.IN, Pin.PULL_UP)

A = Pin(6, Pin.IN, Pin.PULL_UP)
B = Pin(7, Pin.IN, Pin.PULL_UP)

START = Pin(8, Pin.IN, Pin.PULL_UP)
SELECT = Pin(9, Pin.IN, Pin.PULL_UP)


# ============================================================
# GAMES
# ============================================================

GAMES = [
    "Pong",
    "Snake",
    "Space Invaders",
    "Dino",
    "2048",
    "Tetris",
    "Full Speed",
    "Lunar Module"
]


# ============================================================
# LEVELS
# ============================================================

LEVELS = [
    "EASY",
    "MEDIUM",
    "HARD"
]


# ============================================================
# VARIABLES
# ============================================================

VISIBLE_GAMES = 4

current_game = 0


# ============================================================
# CURRENT LEVEL FOR EACH GAME
#
# Loaded from save_manager.
#
# This is NOT used by RESUME.
# RESUME uses the level stored with the save.
# ============================================================

game_levels = {}

for game in GAMES:

    game_levels[game] = save_manager.get_level(game)


# ============================================================
# BUTTON RELEASE
# ============================================================

def wait_release():

    while (
        UP.value() == 0 or
        DOWN.value() == 0 or
        LEFT.value() == 0 or
        RIGHT.value() == 0 or
        A.value() == 0 or
        B.value() == 0 or
        START.value() == 0 or
        SELECT.value() == 0
    ):

        time.sleep_ms(20)


# ============================================================
# CENTER TEXT
# ============================================================

def center_text(text, y):

    x = 64 - len(text) * 4

    if x < 0:
        x = 0

    oled.text(
        text,
        x,
        y
    )


# ============================================================
# MAIN GAME LIST
# ============================================================

def draw_game_menu():

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
        "PICO GAME",
        2,
        1,
        0
    )

    oled.text(
        str(current_game + 1) + "/8",
        108,
        1,
        0
    )


    # Determine first visible game

    if current_game < VISIBLE_GAMES:

        first_game = 0

    else:

        first_game = (
            current_game -
            VISIBLE_GAMES +
            1
        )


    # Draw games

    for i in range(VISIBLE_GAMES):

        index = first_game + i

        if index >= len(GAMES):
            break

        y = 14 + i * 12

        if index == current_game:

            oled.fill_rect(
                0,
                y - 2,
                128,
                10,
                1
            )

            oled.text(
                "> " + GAMES[index],
                4,
                y,
                0
            )

        else:

            oled.text(
                "  " + GAMES[index],
                4,
                y,
                1
            )


    # Scroll indicators

    if first_game > 0:

        oled.text(
            "^",
            120,
            13,
            1
        )

    if first_game + VISIBLE_GAMES < len(GAMES):

        oled.text(
            "v",
            120,
            55,
            1
        )


    oled.show()


# ============================================================
# GAME MANAGEMENT MENU
# ============================================================

def game_menu():

    game_name = GAMES[current_game]

    menu_items = [
        "NEW GAME",
        "RESUME",
        "LEVEL",
        "HIGH SCORE"
    ]

    selected = 0


    while True:

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
            game_name,
            4,
            1,
            0
        )


        # Current selected level

        current_level = game_levels[game_name]

        oled.text(
            LEVELS[current_level],
            80,
            1,
            0
        )


        # Menu

        for i in range(4):

            y = 16 + i * 10

            if i == selected:

                oled.fill_rect(
                    5,
                    y - 1,
                    118,
                    10,
                    1
                )

                oled.text(
                    "> " + menu_items[i],
                    10,
                    y,
                    0
                )

            else:

                oled.text(
                    "  " + menu_items[i],
                    10,
                    y,
                    1
                )


        # Bottom

        oled.text(
            "A SELECT",
            4,
            56,
            1
        )

        oled.text(
            "B BACK",
            82,
            56,
            1
        )

        oled.show()


        # ====================================================
        # UP
        # ====================================================

        if UP.value() == 0:

            if selected > 0:

                selected -= 1

            wait_release()


        # ====================================================
        # DOWN
        # ====================================================

        elif DOWN.value() == 0:

            if selected < 3:

                selected += 1

            wait_release()


        # ====================================================
        # A = SELECT
        # ====================================================

        elif A.value() == 0:

            wait_release()


            # -----------------------------------------------
            # NEW GAME
            # -----------------------------------------------

            if selected == 0:

                return new_game(game_name)


            # -----------------------------------------------
            # RESUME
            # -----------------------------------------------

            elif selected == 1:

                return resume_game(game_name)


            # -----------------------------------------------
            # LEVEL
            # -----------------------------------------------

            elif selected == 2:

                level_selection(game_name)


            # -----------------------------------------------
            # HIGH SCORE
            # -----------------------------------------------

            elif selected == 3:

                high_score_screen(game_name)


        # ====================================================
        # B = BACK
        # ====================================================

        elif B.value() == 0:

            wait_release()

            return


        time.sleep_ms(30)


# ============================================================
# LEVEL SELECTION
# ============================================================

def level_selection(game_name):

    selected = game_levels[game_name]


    while True:

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
            game_name,
            4,
            1,
            0
        )

        oled.text(
            "LEVEL",
            88,
            1,
            0
        )


        # Levels

        for i in range(3):

            y = 18 + i * 11

            if i == selected:

                oled.fill_rect(
                    12,
                    y - 2,
                    104,
                    10,
                    1
                )

                oled.text(
                    "> " + LEVELS[i],
                    25,
                    y,
                    0
                )

            else:

                oled.text(
                    "  " + LEVELS[i],
                    25,
                    y,
                    1
                )


        oled.text(
            "A SELECT",
            4,
            55,
            1
        )

        oled.text(
            "B BACK",
            80,
            55,
            1
        )

        oled.show()


        # UP

        if UP.value() == 0:

            if selected > 0:

                selected -= 1

            wait_release()


        # DOWN

        elif DOWN.value() == 0:

            if selected < 2:

                selected += 1

            wait_release()


        # A

        elif A.value() == 0:

            wait_release()

            game_levels[game_name] = selected

            save_manager.set_level(
                game_name,
                selected
            )

            confirmation(
                "LEVEL SET",
                LEVELS[selected]
            )

            return


        # B

        elif B.value() == 0:

            wait_release()

            return


        time.sleep_ms(30)


# ============================================================
# HIGH SCORE SCREEN
# ============================================================

def high_score_screen(game_name):

    scores = save_manager.get_high_scores(
        game_name
    )


    while True:

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
            "HIGH SCORE",
            2,
            1,
            0
        )


        # Easy

        oled.text(
            "EASY",
            8,
            17,
            1
        )

        oled.text(
            str(scores[0]),
            92,
            17,
            1
        )


        # Medium

        oled.text(
            "MEDIUM",
            8,
            29,
            1
        )

        oled.text(
            str(scores[1]),
            92,
            29,
            1
        )


        # Hard

        oled.text(
            "HARD",
            8,
            41,
            1
        )

        oled.text(
            str(scores[2]),
            92,
            41,
            1
        )


        oled.text(
            "B BACK",
            43,
            56,
            1
        )

        oled.show()


        if B.value() == 0:

            wait_release()

            return


        time.sleep_ms(30)


# ============================================================
# NEW GAME
# ============================================================

def new_game(game_name):

    level = game_levels[game_name]


    confirmation(
        "NEW GAME",
        LEVELS[level]
    )


    return {
        "action": "NEW",
        "level": level,
        "score": 0,
        "state": {}
    }


# ============================================================
# RESUME GAME
# ============================================================

def resume_game(game_name):

    saved = save_manager.get_saved_game(
        game_name
    )


    # --------------------------------------------------------
    # No save
    # --------------------------------------------------------

    if saved is None:

        message_screen(
            "NO SAVE",
            "NO GAME SAVED"
        )

        return None


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Resume uses the SAVED level.
    #
    # It does NOT use game_levels[game_name].
    # --------------------------------------------------------

    saved_level = saved["level"]

    saved_score = saved["score"]

    saved_state = saved["state"]


    confirmation(
        "RESUME",
        LEVELS[saved_level]
    )


    return {
        "action": "RESUME",

        "level": saved_level,

        "score": saved_score,

        "state": saved_state
    }


# ============================================================
# CONFIRMATION SCREEN
# ============================================================

def confirmation(title, subtitle):

    oled.fill(0)

    center_text(
        title,
        18
    )

    center_text(
        subtitle,
        32
    )

    oled.show()

    time.sleep_ms(500)


# ============================================================
# MESSAGE SCREEN
# ============================================================

def message_screen(title, message):

    oled.fill(0)

    center_text(
        title,
        18
    )

    center_text(
        message,
        32
    )

    oled.text(
        "B BACK",
        42,
        54
    )

    oled.show()


    while True:

        if B.value() == 0:

            wait_release()

            return

        time.sleep_ms(20)


# ============================================================
# PAUSE MENU
# ============================================================

def pause_menu():

    items = [
        "RESUME",
        "SAVE GAME",
        "EXIT"
    ]

    selected = 0


    while True:

        oled.fill(0)


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
            55,
            1
        )

        oled.show()


        # UP

        if UP.value() == 0:

            if selected > 0:

                selected -= 1

            wait_release()


        # DOWN

        elif DOWN.value() == 0:

            if selected < 2:

                selected += 1

            wait_release()


        # A

        elif A.value() == 0:

            wait_release()

            if selected == 0:

                return "RESUME"

            elif selected == 1:

                return "SAVE"

            elif selected == 2:

                return "EXIT"


        # B

        elif B.value() == 0:

            wait_release()

            return "RESUME"


        time.sleep_ms(30)


# ============================================================
# START SELECTED GAME
# ============================================================

def start_game(game_number, game_command):

    if game_command is None:

        return


    game_name = GAMES[game_number]

    level = game_command["level"]

    score = game_command["score"]

    state = game_command["state"]


    # ========================================================
    # PONG
    # ========================================================

    if game_number == 0:

        import PicoPong

        PicoPong.pico_pong_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # SNAKE
    # ========================================================

    elif game_number == 1:

        import PicoSnake

        PicoSnake.pico_snake_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # SPACE INVADERS
    # ========================================================

    elif game_number == 2:

        import PicoInvaders

        PicoInvaders.pico_invaders_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # DINO
    # ========================================================

    elif game_number == 3:

        import PicoDino

        PicoDino.pico_dino_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # 2048
    # ========================================================

    elif game_number == 4:

        import Pico2048

        Pico2048.pico_2048_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # TETRIS
    # ========================================================

    elif game_number == 5:

        import PicoTetris

        PicoTetris.pico_tetris_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # FULL SPEED
    # ========================================================

    elif game_number == 6:

        import PicoFullSpeed

        PicoFullSpeed.pico_full_speed_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


    # ========================================================
    # LUNAR MODULE
    # ========================================================

    elif game_number == 7:

        import PicoLunarModule

        PicoLunarModule.pico_lunar_module_main(
            level=level,
            saved_score=score,
            saved_state=state
        )


# ============================================================
# MAIN LOOP
# ============================================================

def main_menu():

    global current_game


    while True:

        draw_game_menu()


        # ----------------------------------------------------
        # UP
        # ----------------------------------------------------

        if UP.value() == 0:

            if current_game > 0:

                current_game -= 1

            wait_release()


        # ----------------------------------------------------
        # DOWN
        # ----------------------------------------------------

        elif DOWN.value() == 0:

            if current_game < len(GAMES) - 1:

                current_game += 1

            wait_release()


        # ----------------------------------------------------
        # A = GAME MENU
        # ----------------------------------------------------

        elif A.value() == 0:

            wait_release()

            command = game_menu()

            if command is not None:

                start_game(
                    current_game,
                    command
                )


        time.sleep_ms(30)


# ============================================================
# BOOT
# ============================================================

boot_animation.boot_animation()

main_menu()