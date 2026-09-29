# ============================================================
# PicoDino.py by Kobi Tyrkel
# A simple dino game
# for the Raspberry Pi Pico RetroGaming Console
# ============================================================

from PicoGame import PicoGame
from DinoGame.Resources import Resources
from DinoGame.Dino import Dino
from DinoGame.Cactus import Cactus
from DinoGame.Bird import Bird
from DinoGame.Dirt import Dirt
import time
import random


# ============================================================
# INIT GAME
# ============================================================

game = PicoGame()


# ============================================================
# COLLISION
# ============================================================

def collide(s1, s2):
    # Return true if two sprites have any pixels collide
    return game.sprites_collision(
        s1.get_sprite(),
        s1.x,
        s1.y,
        s2.get_sprite(),
        s2.x,
        s2.y
    )


# ============================================================
# MAIN DINO GAME
# ============================================================

def pico_dino_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    # ========================================================
    # GAME SETTINGS
    # ========================================================

    SCREEN_WIDTH = game.SCREEN_WIDTH
    SCREEN_HEIGHT = game.SCREEN_HEIGHT

    PLAYER_SPEED = 3

    # ========================================================
    # LEVEL / DIFFICULTY
    # ========================================================

    if level == 0:

        # EASY
        level_name = "EASY"
        obstacle_steps = 1

    elif level == 2:

        # HARD
        level_name = "HARD"
        obstacle_steps = 3

    else:

        # MEDIUM
        level_name = "MEDIUM"
        obstacle_steps = 2

    # ========================================================
    # INITIALIZE GAME
    # ========================================================

    dino = Dino()
    cactus = Cactus()

    dirt1 = Dirt(32, 52, 1)
    dirt2 = Dirt(40, 57, 2)
    dirt3 = Dirt(48, 62, 3)

    bird = Bird()

    sound_freq = 180

    # ========================================================
    # SCORE
    # ========================================================

    if saved_state is not None:
        score = saved_score
    else:
        score = 0


    # ========================================================
    # LOAD DINO SPRITES
    # ========================================================

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_A,
            Resources.DINO_A_W,
            Resources.DINO_A_H
        )
    )

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_B,
            Resources.DINO_B_W,
            Resources.DINO_B_H
        )
    )

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_C,
            Resources.DINO_C_W,
            Resources.DINO_C_H
        )
    )

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_D,
            Resources.DINO_D_W,
            Resources.DINO_D_H
        )
    )

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_E,
            Resources.DINO_E_W,
            Resources.DINO_E_H
        )
    )

    dino.sprites.append(
        game.add_sprite(
            Resources.DINO_F,
            Resources.DINO_F_W,
            Resources.DINO_F_H
        )
    )


    # ========================================================
    # GROUND
    # Sprite 6
    # ========================================================

    game.add_sprite(
        Resources.GROUND_LINE,
        Resources.GROUND_LINE_W,
        Resources.GROUND_LINE_H
    )


    # ========================================================
    # CACTUS
    # Sprite 7
    # ========================================================

    cactus.sprites.append(
        game.add_sprite(
            Resources.CACTUS_A,
            Resources.CACTUS_A_W,
            Resources.CACTUS_A_H
        )
    )


    # ========================================================
    # BIRD
    # Sprite 8, 9
    # ========================================================

    bird.sprites.append(
        game.add_sprite(
            Resources.BIRD_A,
            Resources.BIRD_A_W,
            Resources.BIRD_A_H
        )
    )

    bird.sprites.append(
        game.add_sprite(
            Resources.BIRD_B,
            Resources.BIRD_B_W,
            Resources.BIRD_B_H
        )
    )


    # ========================================================
    # DIRT
    # Sprite 10
    # ========================================================

    dirt1.sprites.append(
        game.add_sprite(
            Resources.DIRT_A,
            Resources.DIRT_A_W,
            Resources.DIRT_A_H
        )
    )


    # ========================================================
    # DIRT
    # Sprite 11
    # ========================================================

    dirt2.sprites.append(
        game.add_sprite(
            Resources.DIRT_B,
            Resources.DIRT_B_W,
            Resources.DIRT_B_H
        )
    )


    # ========================================================
    # DIRT
    # Sprite 12
    # ========================================================

    dirt3.sprites.append(
        game.add_sprite(
            Resources.DIRT_C,
            Resources.DIRT_C_W,
            Resources.DIRT_C_H
        )
    )


    # ========================================================
    # HEART
    # Sprite 13
    # ========================================================

    game.add_sprite(
        Resources.HEART,
        Resources.HEART_W,
        Resources.HEART_H
    )


    # ========================================================
    # DIRT SPRITES
    # ========================================================

    dirt1.sprites.append(
        dirt2.get_sprite()
    )

    dirt1.sprites.append(
        dirt3.get_sprite()
    )

    dirt2.sprites.append(
        dirt3.get_sprite()
    )

    dirt2.sprites.append(
        dirt1.get_sprite()
    )

    dirt3.sprites.append(
        dirt1.get_sprite()
    )

    dirt3.sprites.append(
        dirt2.get_sprite()
    )


    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # B = BACK TO MAIN MENU
        # ----------------------------------------------------

        if game.button_B():

            game.sound(0)

            return


        # ----------------------------------------------------
        # UPDATE PLAYER
        # ----------------------------------------------------

        dino.update()


        # ----------------------------------------------------
        # UPDATE CACTUS
        # LEVEL CONTROLS SPEED
        # ----------------------------------------------------

        for _ in range(obstacle_steps):

            cactus.update()


        # ----------------------------------------------------
        # UPDATE DIRT
        # ----------------------------------------------------

        dirt1.update()
        dirt2.update()
        dirt3.update()


        # ----------------------------------------------------
        # BIRD MOVEMENT
        # LEVEL CONTROLS SPEED
        # ----------------------------------------------------

        for _ in range(obstacle_steps):

            if bird.x < cactus.x:

                bird.update()
                bird.update()


            if bird.x > cactus.x + 95:

                bird.update()


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        if cactus.x < -31:

            score += 100


        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        if game.button_left():

            dino.move(PLAYER_SPEED)


        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        elif game.button_right():

            dino.move(-PLAYER_SPEED)


        # ----------------------------------------------------
        # DOWN = DUCK
        # ----------------------------------------------------

        if game.button_down():

            dino.duck()


        # ----------------------------------------------------
        # UP OR A = JUMP
        # B = BACK
        # ----------------------------------------------------

        if game.button_up() or game.button_A():

            dino.jump()


        # ----------------------------------------------------
        # COLLISION
        # ----------------------------------------------------

        game_over = False


        if collide(dino, cactus) or collide(dino, bird):

            dino.lives -= 1

            dino.state = Dino.DEAD

            if dino.lives <= 0:

                game_over = True

            else:

                dino.state = Dino.DEAD


        # ====================================================
        # REFRESH DISPLAY
        # ====================================================

        # ----------------------------------------------------
        # CLEAR SCREEN
        # ----------------------------------------------------

        game.fill(0)


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        game.top_right_corner_text(
            str(score)
        )


        # ----------------------------------------------------
        # LEVEL
        # ----------------------------------------------------

        game.text(
            level_name,
            2,
            0,
            1
        )


        # ----------------------------------------------------
        # HEARTS
        # ----------------------------------------------------

        if dino.lives > 0:

            game.sprite(
                13,
                0,
                0
            )


        if dino.lives > 1:

            game.sprite(
                13,
                10,
                0
            )


        if dino.lives > 2:

            game.sprite(
                13,
                20,
                0
            )


        # ----------------------------------------------------
        # PLAYER
        # ----------------------------------------------------

        game.sprite(
            dino.get_sprite(),
            dino.x,
            dino.y
        )


        # ----------------------------------------------------
        # GROUND
        # ----------------------------------------------------

        game.sprite(
            6,
            0,
            48
        )


        # ----------------------------------------------------
        # DIRT
        # ----------------------------------------------------

        game.sprite(
            dirt1.get_sprite(),
            dirt1.x,
            dirt1.y
        )

        game.sprite(
            dirt2.get_sprite(),
            dirt2.x,
            dirt2.y
        )

        game.sprite(
            dirt3.get_sprite(),
            dirt3.x,
            dirt3.y
        )


        # ----------------------------------------------------
        # CACTUS
        # ----------------------------------------------------

        game.sprite(
            cactus.get_sprite(),
            cactus.x,
            cactus.y
        )


        # ----------------------------------------------------
        # BIRD
        # ----------------------------------------------------

        game.sprite(
            bird.get_sprite(),
            bird.x,
            bird.y
        )


        # ----------------------------------------------------
        # SHOW
        # ----------------------------------------------------

        game.show()


        # ----------------------------------------------------
        # NO SOUND
        # ----------------------------------------------------

        game.sound(0)


        # ====================================================
        # GAME OVER
        # ====================================================

        if game_over:

            # ------------------------------------------------
            # GAME OVER SOUND
            # ------------------------------------------------

            game.sound(200)

            time.sleep(0.5)

            game.sound(0)


            # ------------------------------------------------
            # GAME OVER SCREEN
            # ------------------------------------------------

            game.rect(
                0,
                22,
                128,
                11,
                1,
                True
            )


            game.center_text(
                "GAME OVER",
                0
            )


            game.top_right_corner_text(
                str(score)
            )


            game.text(
                level_name,
                2,
                0,
                1
            )


            game.show()


            # ------------------------------------------------
            # WAIT FOR BUTTON
            # ------------------------------------------------

            while not game.any_button():

                time.sleep(0.001)


            # ------------------------------------------------
            # B = BACK TO MENU
            # ------------------------------------------------

            if game.button_B():

                return


            # ------------------------------------------------
            # OTHER BUTTON = RESTART
            # ------------------------------------------------

            dino.state = Dino.FALL

            bird.x = 512

            cactus.x = 256

            score = 0


        else:

            # ------------------------------------------------
            # DINO LOST ONE LIFE
            # ------------------------------------------------

            if dino.state == Dino.DEAD:

                game.sound(200)

                time.sleep(0.5)

                game.sound(0)


                # --------------------------------------------
                # WAIT FOR BUTTON
                # --------------------------------------------

                while not game.any_button():

                    time.sleep(0.001)


                # --------------------------------------------
                # B = BACK TO MENU
                # --------------------------------------------

                if game.button_B():

                    return


                # --------------------------------------------
                # OTHER BUTTON = CONTINUE
                # --------------------------------------------

                dino.state = Dino.FALL

                bird.x = 512

                cactus.x = 256


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    pico_dino_main(
        level=1,
        saved_score=0,
        saved_state=None
    )