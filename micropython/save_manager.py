# ============================================================
# SAVE MANAGER
# Raspberry Pi Pico 2 Game Console
#
# Handles:
#   - Saved game state
#   - Saved game level
#   - Current score
#   - High scores for Easy / Medium / Hard
#
# Level:
#   0 = EASY
#   1 = MEDIUM
#   2 = HARD
#
# Save files are stored in Pico flash.
# ============================================================

import json
import os


SAVE_FILE = "game_saves.json"


# ============================================================
# DEFAULT GAME DATA
# ============================================================

def default_game():

    return {
        "saved": False,

        "level": 0,

        "score": 0,

        "state": {},

        "high_scores": [
            0,      # EASY
            0,      # MEDIUM
            0       # HARD
        ]
    }


# ============================================================
# DEFAULT ALL GAMES
# ============================================================

def default_data():

    return {

        "Pong": default_game(),

        "Snake": default_game(),

        "Space Invaders": default_game(),

        "Dino": default_game(),

        "2048": default_game(),

        "Tetris": default_game(),

        "Full Speed": default_game(),

        "Lunar Module": default_game()
    }


# ============================================================
# LOAD ALL SAVE DATA
# ============================================================

def load_data():

    try:

        with open(SAVE_FILE, "r") as f:

            data = json.load(f)

        # Make sure all games exist

        defaults = default_data()

        for game in defaults:

            if game not in data:

                data[game] = defaults[game]

        return data


    except:

        return default_data()


# ============================================================
# SAVE ALL DATA
# ============================================================

def save_data(data):

    try:

        with open(SAVE_FILE, "w") as f:

            json.dump(data, f)

        return True

    except:

        return False


# ============================================================
# GET GAME DATA
# ============================================================

def get_game(game_name):

    data = load_data()

    return data[game_name]


# ============================================================
# SET LEVEL
# ============================================================

def set_level(game_name, level):

    data = load_data()

    data[game_name]["level"] = level

    save_data(data)


# ============================================================
# GET LEVEL
# ============================================================

def get_level(game_name):

    data = load_data()

    return data[game_name]["level"]


# ============================================================
# SAVE GAME
#
# This saves:
#   Level
#   Score
#   Game state
# ============================================================

def save_game(
    game_name,
    level,
    score,
    state
):

    data = load_data()

    data[game_name]["saved"] = True

    data[game_name]["level"] = level

    data[game_name]["score"] = score

    data[game_name]["state"] = state

    save_data(data)


# ============================================================
# CHECK WHETHER SAVE EXISTS
# ============================================================

def has_save(game_name):

    data = load_data()

    return data[game_name]["saved"]


# ============================================================
# GET SAVED GAME
# ============================================================

def get_saved_game(game_name):

    data = load_data()

    if not data[game_name]["saved"]:

        return None

    return data[game_name]


# ============================================================
# DELETE SAVED GAME
# ============================================================

def delete_save(game_name):

    data = load_data()

    data[game_name]["saved"] = False

    data[game_name]["score"] = 0

    data[game_name]["state"] = {}

    save_data(data)


# ============================================================
# UPDATE HIGH SCORE
#
# Returns True if a new high score was created.
# ============================================================

def update_high_score(
    game_name,
    level,
    score
):

    data = load_data()

    old_score = data[game_name]["high_scores"][level]

    if score > old_score:

        data[game_name]["high_scores"][level] = score

        save_data(data)

        return True

    return False


# ============================================================
# GET HIGH SCORES
# ============================================================

def get_high_scores(game_name):

    data = load_data()

    return data[game_name]["high_scores"]