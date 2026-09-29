# ============================================================
# PicoTetris.py
# A simple Tetris game
# for the Raspberry Pi Pico Retro Gaming Console
#
# Updated:
# - Pico 2 compatible
# - EASY / MEDIUM / HARD level input
# - Updated game UI
# - A = Rotate
# - B = Back / Exit
# - START = Pause / Resume
# - SELECT = Quick Save placeholder
# ============================================================

from PicoGame import PicoGame
from TetrisGame.Resources import Resources
from TetrisGame.Logic import Logic
import time


# ============================================================
# INIT GAME
# ============================================================

game = PicoGame()
l = Logic()

sprites = []

sprites.append(
    game.add_sprite(
        Resources.BLOCK_0,
        Resources.BLOCK_0_W,
        Resources.BLOCK_0_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.BLOCK_1,
        Resources.BLOCK_1_W,
        Resources.BLOCK_1_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.BLOCK_2,
        Resources.BLOCK_2_W,
        Resources.BLOCK_2_H
    )
)

sprites.append(
    game.add_sprite(
        Resources.BLOCK_3,
        Resources.BLOCK_3_W,
        Resources.BLOCK_3_H
    )
)


key_down = True


# ============================================================
# RESET
# ============================================================

def reset():
    l.reset()


# ============================================================
# RENDER
# ============================================================

def render(level_name):

    # --------------------------------------------------------
    # BOARD POSITION
    # --------------------------------------------------------

    top_left = 1

    board_width = int(
        Resources.BLOCK_0_W * l.BOARD_WIDTH + 2
    )

    board_height = int(
        Resources.BLOCK_0_H * (l.BOARD_HEIGHT - 1)
    )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score_text = str(l.score)

    while len(score_text) < 5:
        score_text = "0" + score_text


    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    level_text = level_name


    # --------------------------------------------------------
    # DRAW BACKGROUND
    # --------------------------------------------------------

    game.fill(0)


    # --------------------------------------------------------
    # TETRIS TITLE
    # --------------------------------------------------------

    game.text(
        "TETRIS",
        board_width + 5,
        0,
        1
    )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    game.text(
        "S:" + score_text,
        board_width + 5,
        Resources.BLOCK_0_H + 1,
        1
    )


    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    game.text(
        level_text,
        board_width + 5,
        Resources.BLOCK_0_H * 3,
        1
    )


    # --------------------------------------------------------
    # NEXT BLOCK
    # --------------------------------------------------------

    game.text(
        "NEXT",
        board_width + 5,
        Resources.BLOCK_0_H * 5,
        1
    )


    # --------------------------------------------------------
    # MUTE
    # --------------------------------------------------------

    if game.__mute:

        game.text(
            "MUTE",
            board_width + 5,
            board_height - 5 * Resources.BLOCK_0_H,
            1
        )


    # --------------------------------------------------------
    # NEXT SHAPE
    # --------------------------------------------------------

    for j in range(
        len(
            l.SHAPES[
                l.next_shape
            ][0]
        )
    ):

        for i in range(
            len(
                l.SHAPES[
                    l.next_shape
                ][0][0]
            )
        ):

            if (
                l.SHAPES[
                    l.next_shape
                ][0][j][i] != 0
            ):

                game.rect(
                    board_width
                    +
                    (
                        len(
                            l.SHAPES[
                                l.next_shape
                            ][0][j]
                        )
                        +
                        i
                    )
                    *
                    Resources.BLOCK_0_W,

                    int(
                        board_height / 2
                        -
                        Resources.BLOCK_0_H * j
                    ),

                    Resources.BLOCK_0_W,

                    Resources.BLOCK_0_H,

                    1
                )


    # --------------------------------------------------------
    # BOARD
    # --------------------------------------------------------

    for j in range(
        len(l.board)
    ):

        for i in range(
            len(l.board[j])
        ):

            if key_down:

                print(
                    l.board[j][i],
                    end=" "
                )

            if l.board[j][i] > 0:

                game.rect(
                    top_left
                    +
                    i
                    *
                    game.sprite_width(
                        l.board[j][i]
                    ),

                    board_height
                    -
                    1
                    -
                    (
                        j + 4
                    )
                    *
                    game.sprite_height(
                        l.board[j][i]
                    ),

                    3,
                    3,
                    1
                )

        if key_down:
            print()


    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    if key_down:

        print(
            l.shape_x,
            l.shape_y,
            l.shape,
            l.shape_frame
        )


    # --------------------------------------------------------
    # BOARD BORDER
    # --------------------------------------------------------

    game.rect(
        top_left - 1,
        -1,
        2 + Resources.BLOCK_0_W * l.BOARD_WIDTH,
        board_height + 2,
        1
    )


    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    if l.game_over:

        game.fill_rect(
            0,
            int(
                Resources.SCREEN_HEIGHT / 2
            )
            -
            Resources.BLOCK_0_W * 3,

            Resources.SCREEN_WIDTH,

            Resources.BLOCK_0_W * 4,

            1
        )

        game.center_text(
            "GAME OVER",
            0
        )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    game.show()


# ============================================================
# HANDLE KEYS
# ============================================================

def handle_keys():

    global key_down

    while key_down:

        time.sleep(0.1)

        key_down = game.any_button()


    # --------------------------------------------------------
    # DOWN
    # --------------------------------------------------------

    if game.button_down():

        l.shape_y -= 1

        l.time_between_falls = 10

        key_down = True


    # --------------------------------------------------------
    # LEFT
    # --------------------------------------------------------

    elif game.button_left():

        l.shape_x -= 1

        key_down = True


    # --------------------------------------------------------
    # RIGHT
    # --------------------------------------------------------

    elif game.button_right():

        l.shape_x += 1

        key_down = True


    # --------------------------------------------------------
    # UP
    # --------------------------------------------------------

    elif game.button_up():

        l.set_level(
            l.level
        )

        key_down = True


    # --------------------------------------------------------
    # A = ROTATE
    # --------------------------------------------------------

    elif game.button_A():

        l.shape_frame += 1

        key_down = True


    # --------------------------------------------------------
    # B = MUTE
    # --------------------------------------------------------

    elif game.button_B():

        game.sound(0)

        game.__mute = not game.__mute

        key_down = True


# ============================================================
# TETRIS MUSIC
# ============================================================

def play_tune_notes(
    notes,
    pace,
    beat
):

    if beat >= len(notes):

        return -1

    game.sound(
        notes[beat][0]
    )

    return int(
        pace
        /
        notes[beat][1]
    )


# ============================================================
# MAIN TETRIS GAME
# ============================================================

def pico_tetris_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    # --------------------------------------------------------
    # SELECT LEVEL
    #
    # 0 = EASY
    # 1 = MEDIUM
    # 2 = HARD
    # --------------------------------------------------------

    if level < 0 or level > 2:

        level = 1


    if level == 0:

        level_name = "EASY"

    elif level == 2:

        level_name = "HARD"

    else:

        level_name = "MEDIUM"


    # --------------------------------------------------------
    # RESET GAME
    # --------------------------------------------------------

    reset()


    # --------------------------------------------------------
    # APPLY SELECTED LEVEL
    # --------------------------------------------------------

    l.set_level(
        level
    )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    if saved_state is not None:

        l.score = saved_score


    # --------------------------------------------------------
    # MUSIC
    # --------------------------------------------------------

    beat = 0
    next_beat = 0


    # --------------------------------------------------------
    # GAME LOOP
    # --------------------------------------------------------

    while True:

        # ----------------------------------------------------
        # MUSIC
        # ----------------------------------------------------

        current_time = time.ticks_ms()

        if current_time > next_beat:

            note_delay = play_tune_notes(
                Resources.TETRIS_THEME,
                800,
                beat
            )

            if note_delay >= 0:

                next_beat = (
                    current_time
                    +
                    note_delay
                )

                beat += 1

            else:

                next_beat = 0

                beat = 0


        # ----------------------------------------------------
        # START = PAUSE / RESUME
        # ----------------------------------------------------

        if game.button_START():

            game.wait_for_release()

            game.sound(0)

            while True:

                game.fill(0)

                game.text(
                    "PAUSED",
                    42,
                    8,
                    1
                )

                game.text(
                    "A RESUME",
                    26,
                    28,
                    1
                )

                game.text(
                    "B EXIT",
                    34,
                    42,
                    1
                )

                game.show()


                if game.button_A():

                    game.wait_for_release()

                    break


                if game.button_B():

                    game.wait_for_release()

                    return


                time.sleep_ms(20)


        # ----------------------------------------------------
        # SELECT = QUICK SAVE PLACEHOLDER
        # ----------------------------------------------------

        if game.button_SELECT():

            game.wait_for_release()

            game.sound(1200)

            time.sleep_ms(60)

            game.sound(0)


        # ----------------------------------------------------
        # B = BACK / EXIT
        #
        # Since the original Tetris used B for mute,
        # keep B mute during gameplay.
        # Main-level exit is handled by the pause menu.
        # ----------------------------------------------------


        # ----------------------------------------------------
        # GAME ACTIVE
        # ----------------------------------------------------

        if not l.game_over:

            handle_keys()

            l.update()

            render(
                level_name
            )


        # ----------------------------------------------------
        # GAME OVER
        # ----------------------------------------------------

        else:

            game.sound(0)

            game.fill(0)

            game.text(
                "GAME OVER",
                28,
                12,
                1
            )

            game.text(
                "SCORE",
                38,
                27,
                1
            )

            game.text(
                str(l.score),
                52,
                38,
                1
            )

            game.text(
                "A AGAIN",
                5,
                55,
                1
            )

            game.text(
                "B EXIT",
                82,
                55,
                1
            )

            game.show()


            # ------------------------------------------------
            # WAIT FOR BUTTON
            # ------------------------------------------------

            while True:

                if game.button_A():

                    game.wait_for_release()

                    reset()

                    l.set_level(
                        level
                    )

                    beat = 0

                    next_beat = 0

                    break


                if game.button_B():

                    game.wait_for_release()

                    return


                time.sleep_ms(20)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    pico_tetris_main(
        level=1,
        saved_score=0,
        saved_state=None
    )