# ============================================================
# PicoLunarModule.py
# Game "Lunar Module" by Kuba & Stepan
# Adapted for Pico 2 + PicoGame controls
# ============================================================

from PicoGame import PicoGame
import save_manager
import time
import random


# ============================================================
# MAIN GAME
# ============================================================

def pico_lunar_module_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    # --------------------------------------------------------
    # INIT GAME
    # --------------------------------------------------------

    game = PicoGame()


    # --------------------------------------------------------
    # LEVEL / DIFFICULTY
    # --------------------------------------------------------

    if level == 0:

        level_name = "EASY"

        fuel_start = 35
        gravity_step = 1
        initial_speed = 1

        landing_left = 88
        landing_right = 112

        max_landing_gravity = 5


    elif level == 2:

        level_name = "HARD"

        fuel_start = 18
        gravity_step = 2
        initial_speed = 2

        landing_left = 96
        landing_right = 106

        max_landing_gravity = 3


    else:

        level_name = "MEDIUM"

        fuel_start = 25
        gravity_step = 1
        initial_speed = 1

        landing_left = 90
        landing_right = 110

        max_landing_gravity = 4


    # --------------------------------------------------------
    # TITLE SCREEN
    # --------------------------------------------------------

    game.fill(0)

    game.text(
        "Lunar Module",
        5,
        6,
        1
    )

    game.text(
        "By Kuba",
        30,
        23,
        1
    )

    game.text(
        "&",
        55,
        35,
        1
    )

    game.text(
        "Stepan",
        35,
        47,
        1
    )

    game.rect(
        0,
        0,
        128,
        20,
        1
    )

    game.show()

    time.sleep(2)


    # --------------------------------------------------------
    # LEVEL SCREEN
    # --------------------------------------------------------

    game.fill(0)

    game.text(
        "LUNAR MODULE",
        18,
        10,
        1
    )

    game.text(
        "LEVEL:",
        35,
        27,
        1
    )

    game.text(
        level_name,
        42,
        40,
        1
    )

    game.show()

    time.sleep_ms(1200)


    # --------------------------------------------------------
    # GAME VARIABLES
    # --------------------------------------------------------

    round_level = 1

    x_pos = 2
    direction = 0

    ran = initial_speed

    direction2 = 1
    direction3 = 1

    x_pos2 = 2
    y_pos2 = 2

    gravity = 1

    fuel = fuel_start

    fire = 0

    shift = 0

    score = 0


    # --------------------------------------------------------
    # RESTORE SAVED GAME
    # --------------------------------------------------------

    if saved_state:

        try:

            round_level = saved_state.get(
                "round_level",
                round_level
            )

            x_pos = saved_state.get(
                "x_pos",
                x_pos
            )

            direction = saved_state.get(
                "direction",
                direction
            )

            ran = saved_state.get(
                "ran",
                ran
            )

            direction2 = saved_state.get(
                "direction2",
                direction2
            )

            direction3 = saved_state.get(
                "direction3",
                direction3
            )

            x_pos2 = saved_state.get(
                "x_pos2",
                x_pos2
            )

            y_pos2 = saved_state.get(
                "y_pos2",
                y_pos2
            )

            gravity = saved_state.get(
                "gravity",
                gravity
            )

            fuel = saved_state.get(
                "fuel",
                fuel
            )

            fire = saved_state.get(
                "fire",
                fire
            )

            shift = saved_state.get(
                "shift",
                shift
            )

            score = saved_score

        except Exception:

            pass


    # ========================================================
    # GAME STATE
    # ========================================================

    def get_state():

        return {

            "round_level":
                round_level,

            "x_pos":
                x_pos,

            "direction":
                direction,

            "ran":
                ran,

            "direction2":
                direction2,

            "direction3":
                direction3,

            "x_pos2":
                x_pos2,

            "y_pos2":
                y_pos2,

            "gravity":
                gravity,

            "fuel":
                fuel,

            "fire":
                fire,

            "shift":
                shift
        }


    # ========================================================
    # WAIT FOR RELEASE
    # ========================================================

    def wait_for_release():

        game.wait_for_release()


    # ========================================================
    # QUICK SAVE
    # ========================================================

    def quick_save():

        save_manager.save_game(
            "Lunar Module",
            level,
            score,
            get_state()
        )

        game.sound(1200)

        time.sleep_ms(80)

        game.sound(0)


    # ========================================================
    # PAUSE MENU
    # ========================================================

    def pause_menu():

        items = [
            "RESUME",
            "SAVE GAME",
            "EXIT"
        ]

        selected = 0

        game.wait_for_release()


        while True:

            # ------------------------------------------------
            # DRAW PAUSE MENU
            # ------------------------------------------------

            game.fill(0)

            game.text(
                "PAUSED",
                42,
                2,
                1
            )


            for i, item in enumerate(items):

                y = 18 + i * 11

                if i == selected:

                    prefix = ">"

                else:

                    prefix = " "


                game.text(
                    prefix + " " + item,
                    22,
                    y,
                    1
                )


            game.text(
                "A SELECT",
                2,
                55,
                1
            )

            game.text(
                "B BACK",
                78,
                55,
                1
            )

            game.show()


            # ------------------------------------------------
            # UP
            # ------------------------------------------------

            if game.button_up():

                selected = (
                    selected - 1
                ) % len(items)

                game.wait_for_release()


            # ------------------------------------------------
            # DOWN
            # ------------------------------------------------

            elif game.button_down():

                selected = (
                    selected + 1
                ) % len(items)

                game.wait_for_release()


            # ------------------------------------------------
            # A = SELECT
            # ------------------------------------------------

            elif game.button_A():

                game.wait_for_release()


                # RESUME

                if selected == 0:

                    return "RESUME"


                # SAVE GAME

                elif selected == 1:

                    quick_save()

                    game.fill(0)

                    game.text(
                        "GAME SAVED",
                        24,
                        27,
                        1
                    )

                    game.show()

                    time.sleep_ms(700)


                # EXIT

                elif selected == 2:

                    return "EXIT"


            # ------------------------------------------------
            # B = BACK
            # ------------------------------------------------

            elif game.button_B():

                game.wait_for_release()

                return "RESUME"


            # ------------------------------------------------
            # START = RESUME
            # ------------------------------------------------

            elif game.button_START():

                game.wait_for_release()

                return "RESUME"


            time.sleep_ms(20)


    # ========================================================
    # RESET ROUND
    # ========================================================

    def reset_round():

        nonlocal x_pos
        nonlocal direction
        nonlocal ran
        nonlocal direction2
        nonlocal direction3
        nonlocal x_pos2
        nonlocal y_pos2
        nonlocal gravity
        nonlocal fuel
        nonlocal fire
        nonlocal round_level


        x_pos = 2

        direction = 0

        direction2 = 1

        direction3 = 1

        x_pos2 = 2

        y_pos2 = 2

        gravity = 1

        fuel = fuel_start

        fire = 0

        round_level += 1


    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:


        # ----------------------------------------------------
        # START = PAUSE / RESUME
        # ----------------------------------------------------

        if game.button_START():

            game.wait_for_release()

            result = pause_menu()

            if result == "EXIT":

                game.stop_sound()

                return


        # ----------------------------------------------------
        # SELECT = QUICK SAVE
        # ----------------------------------------------------

        if game.button_SELECT():

            game.wait_for_release()

            quick_save()


        # ----------------------------------------------------
        # B = BACK TO MAIN MENU
        # ----------------------------------------------------

        if game.button_B():

            game.stop_sound()

            game.wait_for_release()

            return


        # ----------------------------------------------------
        # A = FIRE THRUSTER
        # ----------------------------------------------------

        if game.button_A():

            fire = 1

            gravity = gravity - 5

            if fuel > 0:

                fuel = fuel - 1


        # ----------------------------------------------------
        # DRAW BACKGROUND
        # ----------------------------------------------------

        game.fill(0)


        # ----------------------------------------------------
        # TOP HUD
        # ----------------------------------------------------

        game.text(
            level_name,
            2,
            1,
            1
        )

        game.text(
            "R" + str(round_level),
            52,
            1,
            1
        )

        game.text(
            "V" + str(gravity),
            82,
            1,
            1
        )


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        game.top_right_corner_text(
            str(score)
        )


        # ----------------------------------------------------
        # LUNAR MODULE
        # ----------------------------------------------------

        game.rect(
            6 + x_pos2,
            3 + y_pos2,
            5,
            5,
            1,
            True
        )

        game.vline(
            5 + x_pos2,
            5 + y_pos2,
            5,
            1
        )

        game.vline(
            11 + x_pos2,
            5 + y_pos2,
            5,
            1
        )

        game.rect(
            7 + x_pos2,
            1 + y_pos2,
            3,
            4,
            1,
            True
        )


        # ----------------------------------------------------
        # LANDING AREA
        # ----------------------------------------------------

        landing_width = (
            landing_right
            -
            landing_left
        )

        game.rect(
            landing_left,
            62,
            landing_width,
            2,
            1,
            True
        )


        # ----------------------------------------------------
        # THRUSTER FIRE
        # ----------------------------------------------------

        if fire == 1:

            game.vline(
                8 + x_pos2,
                11 + y_pos2,
                8,
                1
            )

            fire = 0


        # ----------------------------------------------------
        # PHYSICS
        # ----------------------------------------------------

        x_pos2 = (
            x_pos2
            + ran
        )

        y_pos2 = (
            y_pos2
            + direction3
        )

        y_pos2 = (
            y_pos2
            + 1
            + gravity // 10
        )

        gravity = (
            gravity
            + gravity_step
        )


        # ----------------------------------------------------
        # SUCCESSFUL LANDING
        # ----------------------------------------------------

        if (
            x_pos2 > landing_left
            and
            x_pos2 < landing_right
            and
            y_pos2 >= 56
            and
            gravity < max_landing_gravity
        ):


            # +1 successful landing

            score += 1


            # ------------------------------------------------
            # LANDING SCREEN
            # ------------------------------------------------

            game.fill(0)

            game.text(
                "LANDING OK!",
                25,
                18,
                1
            )

            game.text(
                "ROUND " + str(round_level),
                25,
                30,
                1
            )

            game.text(
                "SCORE " + str(score),
                25,
                42,
                1
            )

            game.show()

            time.sleep_ms(1200)


            # ------------------------------------------------
            # NEXT ROUND
            # ------------------------------------------------

            round_level += 1

            x_pos = 2

            direction = 0

            gravity = 1

            direction2 = 1

            direction3 = 1

            x_pos2 = 2

            y_pos2 = 2

            fuel = fuel_start


            # Increase speed each round

            ran = (
                ran
                + 1
            )

            if ran > 5:

                ran = 5


        # ----------------------------------------------------
        # GAME OVER
        # ----------------------------------------------------

        elif (
            y_pos2 >= 56
            or
            fuel < 1
        ):


            game.stop_sound()


            # ------------------------------------------------
            # UPDATE HIGH SCORE
            # ------------------------------------------------

            save_manager.update_high_score(
                "Lunar Module",
                level,
                score
            )


            # ------------------------------------------------
            # GAME OVER SCREEN
            # ------------------------------------------------

            game.fill(0)

            game.text(
                "GAME OVER",
                25,
                12,
                1
            )

            game.text(
                "ROUND " + str(round_level),
                30,
                25,
                1
            )

            game.text(
                "SCORE " + str(score),
                30,
                37,
                1
            )

            game.text(
                "A AGAIN",
                5,
                55,
                1
            )

            game.text(
                "B BACK",
                82,
                55,
                1
            )

            game.show()


            # ------------------------------------------------
            # WAIT FOR BUTTON
            # ------------------------------------------------

            game.wait_for_release()


            while True:


                # --------------------------------------------
                # A = NEW GAME
                # --------------------------------------------

                if game.button_A():

                    game.wait_for_release()

                    round_level = 1

                    x_pos = 2

                    direction = 0

                    ran = initial_speed

                    direction2 = 1

                    direction3 = 1

                    x_pos2 = 2

                    y_pos2 = 2

                    gravity = 1

                    fuel = fuel_start

                    fire = 0

                    score = 0

                    break


                # --------------------------------------------
                # B = BACK
                # --------------------------------------------

                if game.button_B():

                    game.wait_for_release()

                    return


                # --------------------------------------------
                # SELECT = QUICK SAVE
                # --------------------------------------------

                if game.button_SELECT():

                    game.wait_for_release()

                    quick_save()


                # --------------------------------------------
                # START = NEW GAME
                # --------------------------------------------

                if game.button_START():

                    game.wait_for_release()

                    round_level = 1

                    x_pos = 2

                    direction = 0

                    ran = initial_speed

                    direction2 = 1

                    direction3 = 1

                    x_pos2 = 2

                    y_pos2 = 2

                    gravity = 1

                    fuel = fuel_start

                    fire = 0

                    score = 0

                    break


                time.sleep_ms(20)


        # ----------------------------------------------------
        # FUEL
        # ----------------------------------------------------

        game.text(
            "FUEL " + str(fuel),
            0,
            55,
            1
        )


        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        game.show()

        time.sleep_ms(100)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    pico_lunar_module_main(
        level=1,
        saved_score=0,
        saved_state=None
    )