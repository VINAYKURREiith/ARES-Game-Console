# ============================================================
# PicoInvaders.py
#
# Updated for:
# Raspberry Pi Pico 2
# SSD1306 128x64 OLED
# Updated PicoGame.py
# save_manager.py
#
# FIXED CONTROLS:
#
# GP2  = UP
# GP3  = DOWN
# GP4  = LEFT
# GP5  = RIGHT
# GP6  = A
# GP7  = B       -> BACK / EXIT
# GP8  = START   -> PAUSE / RESUME
# GP9  = SELECT  -> QUICK SAVE
#
# SPACE INVADERS:
#
# LEFT / RIGHT -> Move player
# A            -> Shoot
# B            -> Back / Exit
# START        -> Pause / Resume
# SELECT       -> Quick Save
#
# ============================================================

from PicoGame import PicoGame
import save_manager
import time
import random


# ============================================================
# RECTANGLE COLLISION
# ============================================================

def intersect(
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


# ============================================================
# ALIEN CLASS
# ============================================================

class Alien:

    DEAD = 0
    DISAPPEARING = 1
    EXPLODING = 2
    ALIVE = 3

    def __init__(
        self,
        x,
        y,
        sprite
    ):

        self.x = x
        self.y = y
        self.sprite = sprite
        self.state = Alien.ALIVE

    def switch_sprite(self):

        if self.sprite < 3:

            self.sprite += 3

        else:

            self.sprite -= 3


# ============================================================
# LASER CLASS
# ============================================================

class Laser:

    def __init__(
        self,
        width,
        height
    ):

        self.width = width
        self.height = height

        self.x = -1
        self.y = -1

        self.x0 = -1
        self.y0 = -1

        self.active = False
        self.released = False


    def fire(
        self,
        x0,
        y0
    ):

        if not self.active:

            self.x0 = x0
            self.y0 = y0

            self.x = x0 + 5
            self.y = y0

            self.active = True


    def move(
        self,
        vy
    ):

        if self.active:

            self.y += vy

            if self.y < 0:

                self.active = False


    def draw(
        self,
        game
    ):

        if self.active:

            game.fill_rect(
                int(self.x),
                int(self.y),
                self.width,
                self.height,
                1
            )


# ============================================================
# UFO CLASS
# ============================================================

class Ufo:

    DEAD = 0
    DISAPPEARING = 1
    EXPLODING = 2
    ALIVE = 3

    def __init__(self):

        self.x = -1
        self.y = -1

        self.state = Ufo.DEAD


    def move(
        self,
        vx
    ):

        self.x += vx

        if self.x > 128:

            self.state = Ufo.DEAD


# ============================================================
# INITIALIZE ALIENS
# ============================================================

def init_aliens(
    ALIENS_ROWS,
    ALIENS_COLS,
    ALIENS_INIT_X,
    ALIENS_INIT_Y,
    ALIENS_SPACING_X,
    ALIENS_SPACING_Y
):

    aliens = []

    for i in range(
        ALIENS_ROWS
    ):

        for j in range(
            ALIENS_COLS
        ):

            x = (
                ALIENS_INIT_X
                +
                j * ALIENS_SPACING_X
            )

            y = (
                ALIENS_INIT_Y
                +
                i * ALIENS_SPACING_Y
            )

            alien = Alien(
                x,
                y,
                min(i, 2)
            )

            aliens.append(
                alien
            )

    return aliens


# ============================================================
# PAUSE MENU
# ============================================================

def pause_menu(
    game,
    game_name,
    level,
    score,
    get_state
):

    items = [
        "RESUME",
        "SAVE GAME",
        "EXIT"
    ]

    selected = 0

    game.wait_for_release()

    while True:

        # ----------------------------------------------------
        # DRAW PAUSE SCREEN
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # UP
        # ----------------------------------------------------

        if game.button_up():

            selected = (
                selected - 1
            ) % len(items)

            game.wait_for_release()


        # ----------------------------------------------------
        # DOWN
        # ----------------------------------------------------

        elif game.button_down():

            selected = (
                selected + 1
            ) % len(items)

            game.wait_for_release()


        # ----------------------------------------------------
        # A = SELECT
        # ----------------------------------------------------

        elif game.button_A():

            game.wait_for_release()


            # RESUME

            if selected == 0:

                return "RESUME"


            # SAVE GAME

            if selected == 1:

                state = get_state()

                save_manager.save_game(
                    "Space Invaders",
                    level,
                    score,
                    state
                )

                game.sound(1200)

                time.sleep_ms(80)

                game.sound(0)


            # EXIT

            elif selected == 2:

                return "EXIT"


        # ----------------------------------------------------
        # B = BACK TO GAME
        # ----------------------------------------------------

        elif game.button_B():

            game.wait_for_release()

            return "RESUME"


        # ----------------------------------------------------
        # START = RESUME
        # ----------------------------------------------------

        elif game.button_START():

            game.wait_for_release()

            return "RESUME"


# ============================================================
# LEVEL SELECTION
# ============================================================

def level_selection(game, current_level=1):

    levels = ["EASY", "MEDIUM", "HARD"]
    selected = current_level

    if selected < 0 or selected > 2:
        selected = 1

    game.wait_for_release()

    while True:
        game.fill(0)

        game.text("Space Invaders", 34, 2, 1)
        game.text("SELECT LEVEL", 25, 12, 1)

        for i in range(3):
            y = 25 + i * 10
            prefix = ">" if i == selected else " "
            game.text(prefix + " " + levels[i], 35, y, 1)

        game.text("A SELECT", 2, 55, 1)
        game.text("B BACK", 82, 55, 1)
        game.show()

        if game.button_up():
            selected = (selected - 1) % 3
            game.wait_for_release()

        elif game.button_down():
            selected = (selected + 1) % 3
            game.wait_for_release()

        elif game.button_A():
            game.wait_for_release()
            game.sound(1000)
            time.sleep_ms(60)
            game.sound(0)
            return selected

        elif game.button_B():
            game.wait_for_release()
            return current_level

        elif game.button_START():
            game.wait_for_release()
            return selected

        time.sleep_ms(20)


# ============================================================
# MAIN GAME
# ============================================================

def pico_invaders_main(
    level=None,
    saved_score=0,
    saved_state=None
):

    # ========================================================
    # INITIALIZE GAME
    # ========================================================

    game = PicoGame()

    # If no level is supplied (for example when main.py calls
    # pico_invaders_main()), show the level selector here.
    if level is None:
        level = level_selection(game, 1)


    # ========================================================
    # ALIEN 1
    # ========================================================

    ALIEN1A_W = 8
    ALIEN1A_H = 8

    ALIEN1A = bytearray([
        0b00011000,
        0b00111100,
        0b01111110,
        0b11011011,
        0b11111111,
        0b00100100,
        0b01011010,
        0b10100101
    ])


    ALIEN1B_W = 8
    ALIEN1B_H = 8

    ALIEN1B = bytearray([
        0b00011000,
        0b00111100,
        0b01111110,
        0b11011011,
        0b11111111,
        0b01011010,
        0b10000001,
        0b01000010
    ])


    # ========================================================
    # ALIEN 2
    # ========================================================

    ALIEN2A_W = 11
    ALIEN2A_H = 8

    ALIEN2A = bytearray([
        0b00100000, 0b10000000,
        0b00010001, 0b00000000,
        0b00111111, 0b10000000,
        0b01101110, 0b11000000,
        0b11111111, 0b11100000,
        0b10111111, 0b10100000,
        0b10100000, 0b10100000,
        0b00011011, 0b00000000
    ])


    ALIEN2B_W = 11
    ALIEN2B_H = 8

    ALIEN2B = bytearray([
        0b00100000, 0b10000000,
        0b10010001, 0b00100000,
        0b10111111, 0b10100000,
        0b11101110, 0b11100000,
        0b11111111, 0b11100000,
        0b00111111, 0b10000000,
        0b00100000, 0b10000000,
        0b01000000, 0b01000000
    ])


    # ========================================================
    # ALIEN 3
    # ========================================================

    ALIEN3A_W = 12
    ALIEN3A_H = 8

    ALIEN3A = bytearray([
        0b00001111, 0b00000000,
        0b01111111, 0b11100000,
        0b11111111, 0b11110000,
        0b11100110, 0b01110000,
        0b11111111, 0b11110000,
        0b00011001, 0b10000000,
        0b00110110, 0b11000000,
        0b11000000, 0b00110000
    ])


    ALIEN3B_W = 12
    ALIEN3B_H = 8

    ALIEN3B = bytearray([
        0b00001111, 0b00000000,
        0b01111111, 0b11100000,
        0b11111111, 0b11110000,
        0b11100110, 0b01110000,
        0b11111111, 0b11110000,
        0b00011001, 0b10000000,
        0b00110110, 0b11000000,
        0b00011001, 0b10000000
    ])


    # ========================================================
    # PLAYER
    # ========================================================

    PLAYER_W = 11
    PLAYER_H = 8

    PLAYER = bytearray([
        0b00000100, 0b00000000,
        0b00001110, 0b00000000,
        0b00001110, 0b00000000,
        0b01111111, 0b11000000,
        0b11111111, 0b11100000,
        0b11111111, 0b11100000,
        0b11111111, 0b11100000,
        0b11111111, 0b11100000
    ])


    # ========================================================
    # LASER
    # ========================================================

    LASER_W = 1
    LASER_H = 8

    LASER = bytearray([
        0b00000100,
        0b00000100,
        0b00000100,
        0b00000100,
        0b00000100,
        0b00000100,
        0b00000100,
        0b00000100
    ])


    # ========================================================
    # EXPLOSION
    # ========================================================

    EXPLOSION_W = 12
    EXPLOSION_H = 7

    EXPLOSION = bytearray([
        0b00001000, 0b10000000,
        0b01000101, 0b00010000,
        0b00100000, 0b00100000,
        0b00010000, 0b01000000,
        0b11000000, 0b00011000,
        0b00010000, 0b01000000,
        0b00100101, 0b00100000,
        0b01001000, 0b10010000
    ])


    # ========================================================
    # UFO
    # ========================================================

    UFO_W = 16
    UFO_H = 7

    UFO = bytearray([
        0b00000111, 0b11100000,
        0b00011111, 0b11111000,
        0b00111111, 0b11111100,
        0b01101101, 0b10110110,
        0b11111111, 0b11111111,
        0b00111001, 0b10111000,
        0b00010000, 0b00010000,
        0b00000000, 0b00000000
    ])


    # ========================================================
    # GAME SETTINGS
    # ========================================================

    SCREEN_WIDTH = game.SCREEN_WIDTH
    SCREEN_HEIGHT = game.SCREEN_HEIGHT

    ALIENS_ROWS = 3
    ALIENS_COLS = 5

    ALIENS_SPACING_X = 20
    ALIENS_SPACING_Y = 10

    ALIENS_INIT_X = int(
        SCREEN_WIDTH / 2
        -
        (
            (ALIENS_COLS + 1)
            *
            ALIENS_SPACING_X
        )
        / 2
    )

    ALIENS_INIT_Y = 8

    ALIENS_VX = 1.0
    ALIENS_VY = 2.0

    PLAYER_Y = (
        SCREEN_HEIGHT
        -
        PLAYER_H
    )

    PLAYER_SPEED = 3.0

    LASER_WIDTH = 1
    LASER_HEIGHT = 4
    LASER_SPEED = 4.0

    UFO_X = 0
    UFO_Y = 0
    UFO_SPEED = 2.0


    # ========================================================
    # INITIALIZE GAME OBJECTS
    # ========================================================

    aliens = init_aliens(
        ALIENS_ROWS,
        ALIENS_COLS,
        ALIENS_INIT_X,
        ALIENS_INIT_Y,
        ALIENS_SPACING_X,
        ALIENS_SPACING_Y
    )


    laser = Laser(
        LASER_WIDTH,
        LASER_HEIGHT
    )


    ufo = Ufo()


    aliens_vx = ALIENS_VX


    player_x = (
        SCREEN_WIDTH / 2
        -
        PLAYER_W / 2
    )


    loop_counter = 0

    sound_freq = 180


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    if saved_state is not None:

        score = saved_score

    else:

        score = 0


    # ========================================================
    # DIFFICULTY
    # ========================================================

    if level == 0:

        level_name = "EASY"

        speed_mult = 0.75


    elif level == 2:

        level_name = "HARD"

        speed_mult = 1.35


    else:

        level_name = "MEDIUM"

        speed_mult = 1.0


    aliens_vx *= speed_mult

    LASER_SPEED_LEVEL = (
        LASER_SPEED
        *
        speed_mult
    )

    UFO_SPEED_LEVEL = (
        UFO_SPEED
        *
        speed_mult
    )


    # ========================================================
    # ADD SPRITES
    # ========================================================

    game.add_sprite(
        ALIEN1A,
        ALIEN1A_W,
        ALIEN1A_H
    )

    game.add_sprite(
        ALIEN2A,
        ALIEN2A_W,
        ALIEN2A_H
    )

    game.add_sprite(
        ALIEN3A,
        ALIEN3A_W,
        ALIEN3A_H
    )

    game.add_sprite(
        ALIEN1B,
        ALIEN1B_W,
        ALIEN1B_H
    )

    game.add_sprite(
        ALIEN2B,
        ALIEN2B_W,
        ALIEN2B_H
    )

    game.add_sprite(
        ALIEN3B,
        ALIEN3B_W,
        ALIEN3B_H
    )

    game.add_sprite(
        PLAYER,
        PLAYER_W,
        PLAYER_H
    )

    game.add_sprite(
        LASER,
        LASER_W,
        LASER_H
    )

    game.add_sprite(
        EXPLOSION,
        EXPLOSION_W,
        EXPLOSION_H
    )

    game.add_sprite(
        UFO,
        UFO_W,
        UFO_H
    )


    # ========================================================
    # RESTORE SAVED GAME
    # ========================================================

    if saved_state:

        try:

            player_x = saved_state.get(
                "player_x",
                player_x
            )

            aliens_vx = saved_state.get(
                "aliens_vx",
                aliens_vx
            )

            loop_counter = saved_state.get(
                "loop_counter",
                0
            )

            sound_freq = saved_state.get(
                "sound_freq",
                180
            )


            # ------------------------------------------------
            # RESTORE ALIENS
            # ------------------------------------------------

            alien_data = saved_state.get(
                "aliens",
                []
            )

            if len(alien_data) == len(aliens):

                for alien, data in zip(
                    aliens,
                    alien_data
                ):

                    alien.x = data.get(
                        "x",
                        alien.x
                    )

                    alien.y = data.get(
                        "y",
                        alien.y
                    )

                    alien.sprite = data.get(
                        "sprite",
                        alien.sprite
                    )

                    alien.state = data.get(
                        "state",
                        alien.state
                    )


            # ------------------------------------------------
            # RESTORE LASER
            # ------------------------------------------------

            laser_data = saved_state.get(
                "laser",
                {}
            )

            laser.x = laser_data.get(
                "x",
                laser.x
            )

            laser.y = laser_data.get(
                "y",
                laser.y
            )

            laser.x0 = laser_data.get(
                "x0",
                laser.x0
            )

            laser.y0 = laser_data.get(
                "y0",
                laser.y0
            )

            laser.active = laser_data.get(
                "active",
                laser.active
            )

            laser.released = laser_data.get(
                "released",
                laser.released
            )


            # ------------------------------------------------
            # RESTORE UFO
            # ------------------------------------------------

            ufo_data = saved_state.get(
                "ufo",
                {}
            )

            ufo.x = ufo_data.get(
                "x",
                ufo.x
            )

            ufo.y = ufo_data.get(
                "y",
                ufo.y
            )

            ufo.state = ufo_data.get(
                "state",
                ufo.state
            )


        except Exception:

            # In case an incompatible save exists,
            # start a normal game.

            pass


    # ========================================================
    # GET GAME STATE
    # ========================================================

    def get_state():

        return {

            "player_x":
                player_x,

            "aliens_vx":
                aliens_vx,

            "loop_counter":
                loop_counter,

            "sound_freq":
                sound_freq,

            "aliens": [

                {
                    "x":
                        alien.x,

                    "y":
                        alien.y,

                    "sprite":
                        alien.sprite,

                    "state":
                        alien.state
                }

                for alien in aliens
            ],

            "laser": {

                "x":
                    laser.x,

                "y":
                    laser.y,

                "x0":
                    laser.x0,

                "y0":
                    laser.y0,

                "active":
                    laser.active,

                "released":
                    laser.released
            },

            "ufo": {

                "x":
                    ufo.x,

                "y":
                    ufo.y,

                "state":
                    ufo.state
            }
        }


    # ========================================================
    # QUICK SAVE
    # ========================================================

    def quick_save():

        save_manager.save_game(
            "Space Invaders",
            level,
            score,
            get_state()
        )

        game.sound(1200)

        time.sleep_ms(80)

        game.sound(0)


    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:


        # ====================================================
        # START = PAUSE / RESUME
        # ====================================================

        if game.button_START():

            game.wait_for_release()

            result = pause_menu(
                game,
                "Space Invaders",
                level,
                score,
                get_state
            )

            if result == "EXIT":

                game.stop_sound()

                return


        # ====================================================
        # SELECT = QUICK SAVE
        # ====================================================

        if game.button_SELECT():

            game.wait_for_release()

            quick_save()


        # ====================================================
        # LEFT = MOVE PLAYER LEFT
        # ====================================================

        if game.button_left():

            player_x -= PLAYER_SPEED

            if player_x < 0:

                player_x = 0


        # ====================================================
        # RIGHT = MOVE PLAYER RIGHT
        # ====================================================

        elif game.button_right():

            player_x += PLAYER_SPEED

            if (
                player_x + PLAYER_W
                >
                SCREEN_WIDTH
            ):

                player_x = (
                    SCREEN_WIDTH
                    -
                    PLAYER_W
                )


        # ====================================================
        # A = SHOOT
        # ====================================================

        if game.button_A():

            laser_active_prev = (
                laser.active
            )

            laser.fire(
                player_x,
                PLAYER_Y
            )

            if (
                not laser_active_prev
                and
                laser.active
            ):

                game.sound(1000)


        # ====================================================
        # B = BACK TO MAIN MENU
        # ====================================================

        if game.button_B():

            game.sound(0)

            while game.button_B():

                time.sleep_ms(10)

            return


        # ====================================================
        # MOVE LASER
        # ====================================================

        laser.move(
            -LASER_SPEED_LEVEL
        )


        # ====================================================
        # UFO
        # ====================================================

        if ufo.state != Ufo.ALIVE:

            if random.randint(
                0,
                500
            ) == 50:

                ufo.x = UFO_X
                ufo.y = UFO_Y
                ufo.state = Ufo.ALIVE


        else:

            ufo.move(
                UFO_SPEED_LEVEL
            )

            if sound_freq == 1100:

                sound_freq = 2000

            else:

                sound_freq = 1100

            game.sound(
                sound_freq
            )


        # ====================================================
        # ALIEN EDGE COLLISION
        # ====================================================

        collision = False


        for alien in aliens:

            if (
                alien.state
                ==
                Alien.ALIVE
            ):

                width = game.sprite_width(
                    alien.sprite
                )

                height = game.sprite_height(
                    alien.sprite
                )


                if (
                    aliens_vx > 0
                    and
                    alien.x
                    +
                    aliens_vx
                    +
                    width
                    >
                    SCREEN_WIDTH
                ):

                    collision = True

                    break


                elif (
                    aliens_vx < 0
                    and
                    alien.x
                    +
                    aliens_vx
                    <
                    0
                ):

                    collision = True

                    break


        if collision:

            aliens_vx = -aliens_vx

            aliens_vy = (
                ALIENS_VY
                *
                speed_mult
            )


        else:

            aliens_vy = 0.0


        # ====================================================
        # MOVE ALIENS
        # ====================================================

        game_over = False


        for alien in aliens:

            alien.x += aliens_vx

            alien.y += aliens_vy


            if (
                alien.state
                ==
                Alien.ALIVE
                and
                alien.y
                >
                SCREEN_HEIGHT
            ):

                game_over = True


        # ====================================================
        # COLLISION DETECTION
        # ====================================================

        for alien in aliens:

            if (
                alien.state
                ==
                Alien.ALIVE
            ):

                width = game.sprite_width(
                    alien.sprite
                )

                height = game.sprite_height(
                    alien.sprite
                )


                # ------------------------------------------------
                # PLAYER VS ALIEN
                # ------------------------------------------------

                if not game_over:

                    if intersect(
                        player_x,
                        PLAYER_Y,
                        PLAYER_W,
                        PLAYER_H,
                        alien.x,
                        alien.y,
                        width,
                        height
                    ):

                        game_over = True


                # ------------------------------------------------
                # LASER VS ALIEN
                # ------------------------------------------------

                if (
                    laser.active
                    and
                    intersect(
                        laser.x,
                        laser.y,
                        laser.width,
                        laser.height,
                        alien.x,
                        alien.y,
                        width,
                        height
                    )
                ):

                    alien.state = (
                        Alien.EXPLODING
                    )

                    laser.active = False

                    # +1 successful hit

                    score += 1

                    game.sound(800)


        # ====================================================
        # LASER VS UFO
        # ====================================================

        if (
            laser.active
            and
            ufo.state
            ==
            Ufo.ALIVE
        ):

            if intersect(
                laser.x,
                laser.y,
                laser.width,
                laser.height,
                ufo.x,
                ufo.y,
                UFO_W,
                UFO_H
            ):

                ufo.state = (
                    Ufo.EXPLODING
                )

                laser.active = False

                score += 10

                game.sound(1000)


        # ====================================================
        # ALIEN ANIMATION
        # ====================================================

        loop_counter += 1


        if loop_counter % 16 == 0:

            loop_counter = 0


            for alien in aliens:

                alien.switch_sprite()


            if ufo.state == Ufo.DEAD:

                if sound_freq == 180:

                    sound_freq = 160

                elif sound_freq == 160:

                    sound_freq = 140

                elif sound_freq == 140:

                    sound_freq = 120

                else:

                    sound_freq = 180

                game.sound(
                    sound_freq
                )


        # ====================================================
        # DRAW SCREEN
        # ====================================================

        game.fill(0)


        # ----------------------------------------------------
        # TOP HUD
        # ----------------------------------------------------

        game.top_right_corner_text(
            str(score)
        )


        # ----------------------------------------------------
        # DRAW ALIENS
        # ----------------------------------------------------

        for alien in aliens:


            if (
                alien.state
                ==
                Alien.ALIVE
            ):

                game.sprite(
                    alien.sprite,
                    int(alien.x),
                    int(alien.y)
                )


            elif (
                alien.state
                ==
                Alien.EXPLODING
            ):

                game.sprite(
                    8,
                    int(alien.x),
                    int(alien.y)
                )

                alien.state = (
                    Alien.DISAPPEARING
                )

                game.sound(800)


            elif (
                alien.state
                ==
                Alien.DISAPPEARING
            ):

                game.sprite(
                    8,
                    int(alien.x) + 2,
                    int(alien.y) + 2
                )

                alien.state = (
                    Alien.DEAD
                )


        # ====================================================
        # DRAW PLAYER
        # ====================================================

        game.sprite(
            6,
            int(player_x),
            int(PLAYER_Y)
        )


        # ====================================================
        # DRAW LASER
        # ====================================================

        laser.draw(
            game
        )


        # ====================================================
        # DRAW UFO
        # ====================================================

        if (
            ufo.state
            !=
            Ufo.DEAD
        ):


            if (
                ufo.state
                ==
                Ufo.ALIVE
            ):

                game.sprite(
                    9,
                    int(ufo.x),
                    int(ufo.y)
                )


            elif (
                ufo.state
                ==
                Ufo.EXPLODING
            ):

                game.sprite(
                    8,
                    int(ufo.x),
                    int(ufo.y)
                )

                game.sound(500)

                ufo.state = (
                    Ufo.DISAPPEARING
                )


            elif (
                ufo.state
                ==
                Ufo.DISAPPEARING
            ):

                game.sprite(
                    8,
                    int(ufo.x) + 2,
                    int(ufo.y) + 2
                )

                ufo.state = (
                    Ufo.DEAD
                )


        # ====================================================
        # DISPLAY
        # ====================================================

        game.show()


        # Stop sound

        game.sound(0)


        # ====================================================
        # CHECK IF ALL ALIENS ARE DEAD
        # ====================================================

        at_least_one_alien_alive = False


        for alien in aliens:

            if (
                alien.state
                ==
                Alien.ALIVE
            ):

                at_least_one_alien_alive = True

                break


        # ----------------------------------------------------
        # START NEW WAVE
        # ----------------------------------------------------

        if not at_least_one_alien_alive:

            aliens = init_aliens(
                ALIENS_ROWS,
                ALIENS_COLS,
                ALIENS_INIT_X,
                ALIENS_INIT_Y,
                ALIENS_SPACING_X,
                ALIENS_SPACING_Y
            )

            aliens_vx = (
                aliens_vx
                *
                1.2
            )


        # ====================================================
        # GAME OVER
        # ====================================================

        if game_over:

            game.sound(200)

            time.sleep_ms(500)

            game.sound(0)


            # ------------------------------------------------
            # UPDATE HIGH SCORE
            # ------------------------------------------------

            save_manager.update_high_score(
                "Space Invaders",
                level,
                score
            )


            # ------------------------------------------------
            # GAME OVER SCREEN
            # ------------------------------------------------

            game.fill(0)


            game.text(
                "GAME OVER",
                28,
                8,
                1
            )


            game.text(
                "SCORE: " + str(score),
                24,
                23,
                1
            )


            game.text(
                level_name,
                48,
                35,
                1
            )


            game.text(
                "A AGAIN",
                5,
                53,
                1
            )


            game.text(
                "B BACK",
                82,
                53,
                1
            )


            game.show()


            # ------------------------------------------------
            # WAIT FOR BUTTON RELEASE
            # ------------------------------------------------

            game.wait_for_release()


            # ------------------------------------------------
            # GAME OVER INPUT
            # ------------------------------------------------

            while True:


                # --------------------------------------------
                # A = NEW GAME
                # --------------------------------------------

                if game.button_A():

                    game.wait_for_release()

                    return pico_invaders_main(
                        level=level,
                        saved_score=0,
                        saved_state=None
                    )


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

                    return pico_invaders_main(
                        level=level,
                        saved_score=0,
                        saved_state=None
                    )


                time.sleep_ms(20)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    pico_invaders_main( level=1,
        saved_score=0,
        saved_state=None)
