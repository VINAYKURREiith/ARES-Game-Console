# ============================================================
# Pico2048.py
#
# Updated 2048 for Raspberry Pi Pico 2 Retro Gaming Console
#
# Controls
# ------------------------------------------------------------
# UP       GP2
# DOWN     GP3
# LEFT     GP4
# RIGHT    GP5
# A        GP6  -> Start / Select
# B        GP7  -> Back
# START    GP8  -> Pause / Resume
# SELECT   GP9  -> Quick Save
#
# Existing game resources:
#   P2048.Logic
#   P2048.Resources
#
# ============================================================

from PicoGame import PicoGame
from P2048.Logic import Logic
from P2048.Resources import Resources

from machine import Pin

import time
import save_manager


# ============================================================
# GAME
# ============================================================

game = PicoGame()

l = Logic()


# ============================================================
# BUTTONS
# ============================================================

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
# LEVELS
# ============================================================

LEVEL_NAMES = [
    "EASY",
    "MEDIUM",
    "HARD"
]


# 2048 itself does not have a natural movement speed.
# Difficulty therefore controls the animation delay.

LEVEL_DELAY = {
    0: 35,      # EASY
    1: 15,      # MEDIUM
    2: 5        # HARD
}


# ============================================================
# DISPLAY
# ============================================================

X_SHIFT = 32


# ============================================================
# SPRITES
# ============================================================

sprites = []

sprites.append(
    game.add_sprite(
        Resources.A_0,
        Resources.A_0_W,
        Resources.A_0_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_2,
        Resources.A_2_W,
        Resources.A_2_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_4,
        Resources.A_4_W,
        Resources.A_4_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_8,
        Resources.A_8_W,
        Resources.A_8_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_16,
        Resources.A_16_W,
        Resources.A_16_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_32,
        Resources.A_32_W,
        Resources.A_32_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_64,
        Resources.A_64_W,
        Resources.A_64_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_128,
        Resources.A_128_W,
        Resources.A_128_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_256,
        Resources.A_256_W,
        Resources.A_256_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_512,
        Resources.A_512_W,
        Resources.A_512_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_1024,
        Resources.A_1024_W,
        Resources.A_1024_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.A_2048,
        Resources.A_2048_W,
        Resources.A_2048_H
    )
)


# ============================================================
# GLOBALS
# ============================================================

current_level = 1

current_score = 0

game_paused = False


# ============================================================
# UTILITY
# ============================================================

def wait_release():

    while (
        game.any_button()
        or START.value() == 0
        or SELECT.value() == 0
    ):

        time.sleep_ms(20)


# ============================================================
# DRAW BOARD
# ============================================================

def draw_matrix(
    mat,
    show_score=True
):

    game.fill(0)


    # --------------------------------------------------------
    # Draw board
    # --------------------------------------------------------

    for i in range(4):

        for j in range(4):

            value = mat[i][j]

            if value == 0:

                sprite_index = 0

            else:

                sprite_index = -1

                for s_i in range(12):

                    if value == 2 ** s_i:

                        sprite_index = s_i

                        break


            if sprite_index >= 0:

                sprite = sprites[
                    sprite_index
                ]

                game.sprite(
                    sprite,
                    X_SHIFT +
                    i *
                    game.sprite_width(sprite),

                    j *
                    game.sprite_height(sprite)
                )


    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    if show_score:

        game.top_right_corner_text(
            str(current_score)
        )


# ============================================================
# ANIMATE MOVES
# ============================================================

def animate_moves(
    moves
):

    for mat in moves:

        draw_matrix(
            mat
        )

        game.show()

        time.sleep_ms(
            LEVEL_DELAY[current_level]
        )


# ============================================================
# SOUND
# ============================================================

def play_tune(
    tune
):

    for element in tune:

        try:

            game.sound(
                element[0]
            )

            delay = int(
                800 / element[1]
            ) - 50

            if delay < 1:

                delay = 1

            time.sleep_ms(
                delay
            )

            game.sound(0)

            time.sleep_ms(50)

        except:

            game.sound(0)


# ============================================================
# SIMPLE BEEP
# ============================================================

def beep(
    frequency,
    duration
):

    try:

        game.sound(
            frequency
        )

        time.sleep_ms(
            duration
        )

        game.sound(0)

    except:

        pass


# ============================================================
# SAVE STATE
# ============================================================

def make_save_state():

    state = {}

    try:

        state["mat"] = [
            list(row)
            for row in l.mat
        ]

    except:

        state["mat"] = []


    # Store game status if available

    try:

        state["state"] = int(
            l.get_current_state()
        )

    except:

        state["state"] = 0


    return state


# ============================================================
# SAVE GAME
# ============================================================

def save_current_game():

    global current_level
    global current_score


    state = make_save_state()


    save_manager.save_game(
        "2048",
        current_level,
        current_score,
        state
    )


    beep(
        1000,
        40
    )

    beep(
        1400,
        50
    )


    game.fill(0)

    game.center_text(
        "GAME SAVED"
    )

    game.show()

    time.sleep_ms(700)


# ============================================================
# RESTORE GAME
# ============================================================

def restore_game(
    saved_score,
    saved_state
):

    global current_score


    current_score = int(
        saved_score
    )


    if saved_state is None:

        return False


    if "mat" not in saved_state:

        return False


    saved_mat = saved_state["mat"]


    if not isinstance(
        saved_mat,
        list
    ):

        return False


    if len(saved_mat) != 4:

        return False


    try:

        # Restore board

        l.mat = [
            list(row)
            for row in saved_mat
        ]

    except:

        return False


    # Clear old animation history

    try:

        l.moves = []

    except:

        pass


    return True


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

        game.fill(0)


        # Header

        game.rect(
            0,
            0,
            128,
            12,
            1,
            True
        )

        game.center_text(
            "PAUSED",
            0
        )


        # Menu

        for i in range(3):

            y = 17 + i * 12


            if i == selected:

                game.rect(
                    8,
                    y - 1,
                    112,
                    10,
                    1,
                    True
                )

                # Inverted text is not available
                # in all PicoGame versions,
                # so draw a simple selector.

                game.text(
                    "> " + items[i],
                    18,
                    y,
                    0
                )

            else:

                game.text(
                    "  " + items[i],
                    18,
                    y,
                    1
                )


        game.text(
            "A SELECT",
            4,
            55
        )

        game.show()


        # UP

        if game.button_up():

            if selected > 0:

                selected -= 1

            wait_release()


        # DOWN

        elif game.button_down():

            if selected < 2:

                selected += 1

            wait_release()


        # A

        elif game.button_A():

            wait_release()

            if selected == 0:

                return "RESUME"

            elif selected == 1:

                return "SAVE"

            else:

                return "EXIT"


        # B

        elif game.button_B():

            wait_release()

            return "RESUME"


        time.sleep_ms(30)


# ============================================================
# HIGH SCORE
# ============================================================

def show_high_score():

    scores = save_manager.get_high_scores(
        "2048"
    )


    easy = scores.get(
        "easy",
        0
    )

    medium = scores.get(
        "medium",
        0
    )

    hard = scores.get(
        "hard",
        0
    )


    while True:

        game.fill(0)


        game.center_text(
            "2048 HIGH SCORE",
            0
        )


        game.text(
            "EASY",
            10,
            18
        )

        game.text(
            str(easy),
            85,
            18
        )


        game.text(
            "MEDIUM",
            10,
            30
        )

        game.text(
            str(medium),
            85,
            30
        )


        game.text(
            "HARD",
            10,
            42
        )

        game.text(
            str(hard),
            85,
            42
        )


        game.text(
            "B BACK",
            42,
            55
        )


        game.show()


        if game.button_B():

            wait_release()

            return


        if game.button_A():

            wait_release()

            return


        time.sleep_ms(30)


# ============================================================
# UPDATE HIGH SCORE
# ============================================================

def update_high_score():

    try:

        return save_manager.update_high_score(
            "2048",
            current_level,
            current_score
        )

    except:

        return False


# ============================================================
# GAME OVER
# ============================================================

def game_over_screen():

    high_score = update_high_score()


    if l.get_current_state() == Logic.WON:

        title = "YOU WIN"

    else:

        title = "GAME OVER"


    # --------------------------------------------------------
    # Sound
    # --------------------------------------------------------

    if l.get_current_state() == Logic.WON:

        try:

            play_tune(
                Resources.WIN_TUNE
            )

        except:

            beep(
                1200,
                150
            )

    else:

        try:

            play_tune(
                Resources.GAME_OVER_TUNE
            )

        except:

            beep(
                200,
                250
            )


    # --------------------------------------------------------
    # Screen
    # --------------------------------------------------------

    while True:

        game.fill(0)


        game.center_text(
            title,
            4
        )


        game.text(
            "SCORE",
            20,
            24
        )

        game.text(
            str(current_score),
            82,
            24
        )


        game.text(
            LEVEL_NAMES[current_level],
            45,
            36
        )


        if high_score:

            game.center_text(
                "NEW HIGH SCORE!",
                47
            )

        else:

            game.text(
                "A AGAIN",
                12,
                55
            )

            game.text(
                "B BACK",
                80,
                55
            )


        game.show()


        # A = again

        if game.button_A():

            wait_release()

            return "AGAIN"


        # B = back

        if game.button_B():

            wait_release()

            return "BACK"


        time.sleep_ms(30)


# ============================================================
# NEW GAME
# ============================================================

def new_game():

    global current_score


    current_score = 0


    l.reset_game()


    try:

        l.moves = []

    except:

        pass


# ============================================================
# START SCREEN
# ============================================================

def start_screen():

    while True:

        game.fill(0)


        game.center_text(
            "2048",
            6
        )


        game.center_text(
            LEVEL_NAMES[current_level],
            20
        )


        game.text(
            "A START",
            18,
            40
        )

        game.text(
            "B BACK",
            78,
            40
        )


        game.show()


        if game.button_A():

            wait_release()

            return True


        if game.button_B():

            wait_release()

            return False


        time.sleep_ms(30)


# ============================================================
# MAIN
# ============================================================

def pico_2048_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    global current_level
    global current_score


    current_level = int(level)


    if current_level < 0:

        current_level = 0

    if current_level > 2:

        current_level = 2


    # ========================================================
    # RESUME OR NEW GAME
    # ========================================================

    resumed = False


    if (
        saved_state is not None
        and
        isinstance(
            saved_state,
            dict
        )
    ):

        resumed = restore_game(
            saved_score,
            saved_state
        )


    if not resumed:

        new_game()


        if not start_screen():

            return


    else:

        # ----------------------------------------------------
        # Resume screen
        # ----------------------------------------------------

        game.fill(0)


        game.center_text(
            "RESUME",
            8
        )


        game.center_text(
            LEVEL_NAMES[current_level],
            23
        )


        game.center_text(
            "SCORE " +
            str(current_score),
            38
        )


        game.show()

        time.sleep_ms(800)


    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:

        clicked = False


        # ----------------------------------------------------
        # Draw current board
        # ----------------------------------------------------

        draw_matrix(
            l.mat
        )

        game.show()


        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        if game.button_down():

            clicked = True

            l.move(
                Logic.DOWN
            )


        elif game.button_up():

            clicked = True

            l.move(
                Logic.UP
            )


        elif game.button_right():

            clicked = True

            l.move(
                Logic.RIGHT
            )


        elif game.button_left():

            clicked = True

            l.move(
                Logic.LEFT
            )


        # ----------------------------------------------------
        # START = PAUSE
        # ----------------------------------------------------

        if START.value() == 0:

            wait_release()


            action = pause_menu()


            if action == "SAVE":

                save_current_game()


            elif action == "EXIT":

                game.sound(0)

                game.fill(0)

                game.show()

                return


        # ----------------------------------------------------
        # SELECT = QUICK SAVE
        # ----------------------------------------------------

        if SELECT.value() == 0:

            wait_release()

            save_current_game()


        # ----------------------------------------------------
        # B = BACK
        # ----------------------------------------------------

        if game.button_B():

            wait_release()

            game.fill(0)

            game.show()

            return


        # ----------------------------------------------------
        # Process animation
        # ----------------------------------------------------

        if len(l.moves) > 0:

            animate_moves(
                l.moves
            )

            l.moves = []


        # ----------------------------------------------------
        # Button debounce
        # ----------------------------------------------------

        if clicked:

            while True:

                time.sleep_ms(20)


                if (
                    not game.any_button()
                    and
                    START.value() == 1
                    and
                    SELECT.value() == 1
                ):

                    break


        # ----------------------------------------------------
        # Check game state
        # ----------------------------------------------------

        if (
            l.get_current_state()
            !=
            Logic.GAME_NOT_OVER
        ):

            result = game_over_screen()


            if result == "BACK":

                game.fill(0)

                game.show()

                return


            # ------------------------------------------------
            # AGAIN
            # ------------------------------------------------

            new_game()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    pico_2048_main(
        level=1,
        saved_score=0,
        saved_state=None
    )