# ============================================================
# PicoSnake.py
# Upgraded Snake for Raspberry Pi Pico 2
#
# CONTROLS
#
# UP       GP2
# DOWN     GP3
# LEFT     GP4
# RIGHT    GP5
# A        GP6 -> Start / Restart
# B        GP7 -> Back
# START    GP8 -> Pause / Resume
# SELECT   GP9 -> Quick Save
#
# OLED
# SDA      GP0
# SCL      GP1
#
# BUZZER
# GP15
#
# LEVELS
# 0 = EASY
# 1 = MEDIUM
# 2 = HARD
#
# SCORE
# +1 for every food eaten
# ============================================================

from machine import Pin, PWM, SoftI2C, Timer
from ssd1306 import SSD1306_I2C

import time
import random
import save_manager


# ============================================================
# SCREEN
# ============================================================

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

SEGMENT_WIDTH = 8
SEGMENT_PIXELS = 8

SEGMENTS_HIGH = SCREEN_HEIGHT // SEGMENT_WIDTH
SEGMENTS_WIDE = SCREEN_WIDTH // SEGMENT_WIDTH


# ============================================================
# VALID FOOD POSITIONS
#
# Reserve row 0 for the HUD.
# ============================================================

VALID_RANGE = [
    [x, y]
    for x in range(SEGMENTS_WIDE)
    for y in range(2, SEGMENTS_HIGH)
]


# ============================================================
# GLOBALS
# ============================================================

game_timer = Timer()

player = None
food = None

game_running = False


# ============================================================
# SCREEN
# ============================================================

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


# ============================================================
# BUZZER
# ============================================================

speaker = PWM(
    Pin(15)
)

speaker.duty_u16(0)


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
# LEVEL SETTINGS
# ============================================================

LEVEL_NAMES = [
    "EASY",
    "MEDIUM",
    "HARD"
]


def get_level_frequency(level):

    if level == 0:

        return 4

    elif level == 1:

        return 6

    else:

        return 9


# ============================================================
# SOUND
# ============================================================

def beep(
    frequency,
    duration,
    volume=1800
):

    speaker.freq(
        frequency
    )

    speaker.duty_u16(
        volume
    )

    time.sleep_ms(
        duration
    )

    speaker.duty_u16(0)


def food_sound():

    beep(
        1000,
        35
    )


def move_sound():

    beep(
        600,
        15
    )


def gameover_sound():

    beep(
        250,
        120
    )

    beep(
        150,
        180
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


# ============================================================
# CENTER TEXT
# ============================================================

def center_text(
    text,
    y
):

    x = 64 - len(text) * 4

    if x < 0:
        x = 0

    oled.text(
        text,
        x,
        y
    )


# ============================================================
# WAIT RELEASE
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
# SNAKE CLASS
# ============================================================

class Snake:

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


    def __init__(
        self,
        x=SEGMENTS_WIDE // 2,
        y=SEGMENTS_HIGH // 2
    ):

        self.segments = [
            [x, y]
        ]

        self.x = x
        self.y = y

        self.dir = Snake.RIGHT

        self.state = True


    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        x=SEGMENTS_WIDE // 2,
        y=SEGMENTS_HIGH // 2
    ):

        self.segments = [
            [x, y]
        ]

        self.x = x
        self.y = y

        self.dir = Snake.RIGHT

        self.state = True


    # ========================================================
    # MOVE
    # ========================================================

    def move(self):

        new_x = self.x
        new_y = self.y


        if self.dir == Snake.UP:

            new_y -= 1

        elif self.dir == Snake.DOWN:

            new_y += 1

        elif self.dir == Snake.LEFT:

            new_x -= 1

        elif self.dir == Snake.RIGHT:

            new_x += 1


        # ----------------------------------------------------
        # Collision
        # ----------------------------------------------------

        if self._check_crash(
            new_x,
            new_y
        ):

            self.state = False

            return


        # ----------------------------------------------------
        # Move body
        # ----------------------------------------------------

        for i in range(
            len(self.segments) - 1
        ):

            self.segments[i][0] = \
                self.segments[i + 1][0]

            self.segments[i][1] = \
                self.segments[i + 1][1]


        self.x = new_x

        self.y = new_y

        self.segments[-1][0] = self.x

        self.segments[-1][1] = self.y


    # ========================================================
    # EAT
    # ========================================================

    def eat(self):

        # Add new segment behind tail

        tail = self.segments[0]

        self.segments.insert(
            0,
            [
                tail[0],
                tail[1]
            ]
        )

        food_sound()


    # ========================================================
    # CHANGE DIRECTION
    # ========================================================

    def change_dir(
        self,
        direction
    ):

        if (
            direction == Snake.DOWN
            and
            self.dir == Snake.UP
        ):

            return

        if (
            direction == Snake.UP
            and
            self.dir == Snake.DOWN
        ):

            return

        if (
            direction == Snake.RIGHT
            and
            self.dir == Snake.LEFT
        ):

            return

        if (
            direction == Snake.LEFT
            and
            self.dir == Snake.RIGHT
        ):

            return

        self.dir = direction


    # ========================================================
    # COLLISION
    # ========================================================

    def _check_crash(
        self,
        new_x,
        new_y
    ):

        if (
            new_y < 2
            or
            new_y >= SEGMENTS_HIGH
            or
            new_x < 0
            or
            new_x >= SEGMENTS_WIDE
        ):

            return True


        # Don't count current tail as collision

        body_to_check = self.segments

        if len(body_to_check) > 1:

            body_to_check = body_to_check[1:]


        if [new_x, new_y] in body_to_check:

            return True


        return False


# ============================================================
# DRAW GAME
# ============================================================

def draw_game(
    level,
    score
):

    oled.fill(0)


    # --------------------------------------------------------
    # HUD
    # --------------------------------------------------------

    oled.text(
        "SNAKE",
        2,
        0
    )

    oled.text(
        LEVEL_NAMES[level],
        47,
        0
    )

    oled.text(
        str(score),
        116 - len(str(score)) * 4,
        0
    )


    # --------------------------------------------------------
    # Divider
    # --------------------------------------------------------

    oled.hline(
        0,
        9,
        128,
        1
    )


    # --------------------------------------------------------
    # Food
    # --------------------------------------------------------

    if food is not None:

        oled.fill_rect(
            food[0] * SEGMENT_PIXELS,
            food[1] * SEGMENT_PIXELS,
            SEGMENT_PIXELS,
            SEGMENT_PIXELS,
            1
        )


    # --------------------------------------------------------
    # Snake
    # --------------------------------------------------------

    if player is not None:

        for i, segment in enumerate(
            player.segments
        ):

            x = segment[0] * SEGMENT_PIXELS

            y = segment[1] * SEGMENT_PIXELS


            if i == len(
                player.segments
            ) - 1:

                # Head

                oled.fill_rect(
                    x,
                    y,
                    SEGMENT_PIXELS,
                    SEGMENT_PIXELS,
                    1
                )

                # Small eye

                oled.pixel(
                    x + 2,
                    y + 2,
                    0
                )

            else:

                oled.rect(
                    x,
                    y,
                    SEGMENT_PIXELS,
                    SEGMENT_PIXELS,
                    1
                )


    oled.show()


# ============================================================
# CREATE FOOD
# ============================================================

def create_food():

    global food

    available = []

    for coord in VALID_RANGE:

        if coord not in player.segments:

            available.append(coord)


    if len(available) == 0:

        food = None

        return


    food = random.choice(
        available
    )


# ============================================================
# SAVE GAME
# ============================================================

def save_current_game(
    level,
    score
):

    global player
    global food


    state = {

        "segments":
            [
                [
                    int(s[0]),
                    int(s[1])
                ]
                for s in player.segments
            ],

        "x": int(player.x),

        "y": int(player.y),

        "dir": int(player.dir),

        "food":
            [
                int(food[0]),
                int(food[1])
            ]
            if food is not None
            else None
    }


    save_manager.save_game(
        "Snake",
        level,
        score,
        state
    )


    save_sound()


    oled.fill(0)

    center_text(
        "GAME SAVED",
        20
    )

    center_text(
        LEVEL_NAMES[level],
        34
    )

    oled.show()

    time.sleep_ms(700)


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
            55
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

            return items[selected]


        # B

        elif B.value() == 0:

            wait_release()

            return "RESUME"


        time.sleep_ms(30)


# ============================================================
# GAME OVER
# ============================================================

def game_over_screen(
    level,
    score
):

    gameover_sound()


    # Update high score

    new_high = save_manager.update_high_score(
        "Snake",
        level,
        score
    )


    oled.fill(0)


    center_text(
        "GAME OVER",
        7
    )


    center_text(
        "SCORE " + str(score),
        23
    )


    center_text(
        LEVEL_NAMES[level],
        35
    )


    if new_high:

        center_text(
            "NEW HIGH SCORE!",
            48
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


    while True:

        if A.value() == 0:

            wait_release()

            return "AGAIN"


        if B.value() == 0:

            wait_release()

            return "BACK"


        time.sleep_ms(20)


# ============================================================
# MAIN GAME
# ============================================================

def pico_snake_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    global player
    global food
    global game_running


    game_running = False


    # ========================================================
    # CHECK RESUME DATA
    # ========================================================

    resumed = False


    if (
        saved_state is not None
        and
        len(saved_state) > 0
    ):

        try:

            player = Snake()

            player.segments = [
                [
                    int(s[0]),
                    int(s[1])
                ]
                for s in saved_state["segments"]
            ]

            player.x = int(
                saved_state["x"]
            )

            player.y = int(
                saved_state["y"]
            )

            player.dir = int(
                saved_state["dir"]
            )

            player.state = True


            saved_food = saved_state[
                "food"
            ]


            if saved_food is not None:

                food = [
                    int(saved_food[0]),
                    int(saved_food[1])
                ]

            else:

                food = None


            score = int(
                saved_score
            )

            resumed = True


        except:

            resumed = False


    # ========================================================
    # NEW GAME
    # ========================================================

    if not resumed:

        player = Snake()

        score = 0

        create_food()


    # ========================================================
    # START SCREEN
    # ========================================================

    if not resumed:

        oled.fill(0)

        center_text(
            "SNAKE",
            8
        )

        center_text(
            LEVEL_NAMES[level],
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

            if B.value() == 0:

                wait_release()

                return


            if A.value() == 0:

                wait_release()

                break


            time.sleep_ms(20)


    else:

        oled.fill(0)

        center_text(
            "RESUMING",
            10
        )

        center_text(
            LEVEL_NAMES[level],
            26
        )

        center_text(
            "SCORE " + str(score),
            42
        )

        oled.show()

        time.sleep_ms(800)


    # ========================================================
    # TIMER SPEED
    # ========================================================

    frequency = get_level_frequency(
        level
    )


    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # Start timer
        # ----------------------------------------------------

        game_timer.init(
            freq=frequency,
            mode=Timer.PERIODIC,
            callback=update_game
        )

        game_running = True


        # ----------------------------------------------------
        # PLAY
        # ----------------------------------------------------

        while player.state:

            # -----------------------------------------------
            # START = PAUSE
            # -----------------------------------------------

            if START.value() == 0:

                wait_release()

                game_timer.deinit()

                game_running = False

                action = pause_menu()


                if action == "SAVE":

                    save_current_game(
                        level,
                        score
                    )


                elif action == "EXIT":

                    speaker.duty_u16(0)

                    oled.fill(0)

                    oled.show()

                    return


                # Resume

                game_timer.init(
                    freq=frequency,
                    mode=Timer.PERIODIC,
                    callback=update_game
                )

                game_running = True


            # -----------------------------------------------
            # SELECT = QUICK SAVE
            # -----------------------------------------------

            if SELECT.value() == 0:

                wait_release()

                game_timer.deinit()

                game_running = False

                save_current_game(
                    level,
                    score
                )

                game_timer.init(
                    freq=frequency,
                    mode=Timer.PERIODIC,
                    callback=update_game
                )

                game_running = True


            # -----------------------------------------------
            # B = BACK
            # -----------------------------------------------

            if B.value() == 0:

                wait_release()

                game_timer.deinit()

                game_running = False

                speaker.duty_u16(0)

                oled.fill(0)

                oled.show()

                return


            # -----------------------------------------------
            # Direction
            # -----------------------------------------------

            if UP.value() == 0:

                player.change_dir(
                    Snake.UP
                )

            elif DOWN.value() == 0:

                player.change_dir(
                    Snake.DOWN
                )

            elif LEFT.value() == 0:

                player.change_dir(
                    Snake.LEFT
                )

            elif RIGHT.value() == 0:

                player.change_dir(
                    Snake.RIGHT
                )


            time.sleep_ms(15)


        # ----------------------------------------------------
        # Stop timer
        # ----------------------------------------------------

        game_timer.deinit()

        game_running = False


        # ----------------------------------------------------
        # Game over
        # ----------------------------------------------------

        result = game_over_screen(
            level,
            score
        )


        if result == "BACK":

            speaker.duty_u16(0)

            oled.fill(0)

            oled.show()

            return


        # ----------------------------------------------------
        # AGAIN
        # ----------------------------------------------------

        player = Snake()

        score = 0

        create_food()


# ============================================================
# TIMER UPDATE
# ============================================================

def update_game(timer):

    global food
    global player
    global game_running


    if not game_running:

        return


    if player is None:

        return


    if not player.state:

        return


    # --------------------------------------------------------
    # Move snake
    # --------------------------------------------------------

    player.move()


    if not player.state:

        oled.fill(0)

        oled.show()

        return


    # --------------------------------------------------------
    # Food collision
    # --------------------------------------------------------

    if (
        food is not None
        and
        food[0] == player.x
        and
        food[1] == player.y
    ):

        player.eat()

        # Score is incremented here.
        #
        # The score variable belongs to the main game,
        # therefore it is handled through a module-level
        # variable below.

        increase_score()

        create_food()


    # --------------------------------------------------------
    # Draw
    # --------------------------------------------------------

    draw_game(
        current_level_for_game,
        current_score_for_game
    )


# ============================================================
# SCORE STATE FOR TIMER CALLBACK
# ============================================================

current_score_for_game = 0
current_level_for_game = 1


def increase_score():

    global current_score_for_game

    current_score_for_game += 1


# ============================================================
# WRAPPER TO KEEP TIMER SCORE SYNCHRONIZED
# ============================================================

_original_pico_snake_main = pico_snake_main


def pico_snake_main(
    level=1,
    saved_score=0,
    saved_state=None
):

    global current_score_for_game
    global current_level_for_game

    current_level_for_game = level

    current_score_for_game = int(
        saved_score
    )

    return _original_pico_snake_main(
        level,
        saved_score,
        saved_state
    )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    pico_snake_main(
        level=1,
        saved_score=0,
        saved_state=None
    )