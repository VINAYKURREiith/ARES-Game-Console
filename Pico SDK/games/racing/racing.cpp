
#include "racing.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdlib.h>
#include <stdint.h>

// =====================================================
// ARES FULL SPEED - PORTRAIT VERSION
// Intended for SCREEN_W = 240, SCREEN_H = 320
// =====================================================

static const int ROAD_W = 180;
#define ROAD_X ((SCREEN_W - ROAD_W) / 2)
static const int ROAD_Y = 45;
#define ROAD_BOTTOM (SCREEN_H)

static const int LANE_W = ROAD_W / 3;
static const int CAR_W = 18;
static const int CAR_H = 27;

#define PLAYER_Y (SCREEN_H - CAR_H - 7)
static const int SPAWN_GAP = 75;

static int player_lane;
static int car_x;
static int score;

static int ob_x[3];
static int ob_y[3];

static bool over;
static bool previous_left;
static bool previous_right;

// =====================================================
// LANE HELPERS
// =====================================================

static int lane_center(int lane)
{
    return ROAD_X + LANE_W * lane + LANE_W / 2;
}

static int lane_car_x(int lane)
{
    return lane_center(lane) - CAR_W / 2;
}

// =====================================================
// SPAWN OPPONENT
// =====================================================

static void spawn_opponent(int i, int start_y)
{
    int lane = rand() % 3;

    // Try to avoid a lane occupied by a nearby car.
    for (int attempt = 0; attempt < 6; attempt++)
    {
        bool lane_busy = false;

        for (int j = 0; j < 3; j++)
        {
            if (i == j)
                continue;

            if (ob_x[j] == lane_car_x(lane) &&
                ob_y[j] < ROAD_Y + CAR_H + 18 &&
                ob_y[j] + CAR_H > start_y - 18)
            {
                lane_busy = true;
                break;
            }
        }

        if (!lane_busy)
            break;

        lane = (lane + 1) % 3;
    }

    ob_x[i] = lane_car_x(lane);
    ob_y[i] = start_y;
}

// =====================================================
// INITIALIZE
// =====================================================

void racing_init()
{
    player_lane = 1;
    car_x = lane_car_x(player_lane);

    score = 0;
    over = false;

    previous_left = false;
    previous_right = false;

    // Queue cars above the road entrance.
    // They are drawn only after entering the road.
    for (int i = 0; i < 3; i++)
    {
        ob_x[i] = lane_car_x(i);
        ob_y[i] = ROAD_Y - CAR_H - i * SPAWN_GAP;
    }
}

// =====================================================
// UPDATE
// =====================================================

void racing_update(bool up, bool down, bool left,
                   bool right, bool a_edge)
{
    (void)up;
    (void)down;

    // Restart on A after a crash.
    if (over)
    {
        if (a_edge)
            racing_init();

        return;
    }

    // Move exactly one lane for each distinct press.
    if (left && !previous_left && player_lane > 0)
        player_lane--;

    if (right && !previous_right && player_lane < 2)
        player_lane++;

    previous_left = left;
    previous_right = right;

    car_x = lane_car_x(player_lane);

    int speed = (game_level == 0) ? 2 :
                (game_level == 2) ? 4 : 3;

    speed += score/ 20;

    for (int i = 0; i < 3; i++)
    {
        ob_y[i] += speed;

        // Respawn after an opponent passes the bottom.
        if (ob_y[i] >= ROAD_BOTTOM)
        {
            int highest_y = ROAD_BOTTOM;

            for (int j = 0; j < 3; j++)
            {
                if (i != j && ob_y[j] < highest_y)
                    highest_y = ob_y[j];
            }

            int spawn_y =
                highest_y - SPAWN_GAP - rand() % 30;

            if (spawn_y > ROAD_Y - CAR_H)
                spawn_y = ROAD_Y - CAR_H;

            spawn_opponent(i, spawn_y);
            score += 1;
        }

        // Check collision only inside the road.
        if (ob_y[i] >= ROAD_Y)
        {
            bool overlap_x =
                car_x < ob_x[i] + CAR_W &&
                car_x + CAR_W > ob_x[i];

            bool overlap_y =
                PLAYER_Y < ob_y[i] + CAR_H &&
                PLAYER_Y + CAR_H > ob_y[i];

            if (overlap_x && overlap_y)
            {
                over = true;
                audio_play_sfx(SFX_EXPLOSION);
                break;
            }
        }
    }
}

// =====================================================
// DRAW CAR
// =====================================================

static void draw_car(int x, int y, uint16_t color)
{
    // Main body
    rect(x + 2, y + 5, CAR_W - 4, CAR_H - 8, color);

    // Bonnet
    rect(x + 4, y, CAR_W - 8, 7, color);

    // Rear
    rect(x + 3, y + CAR_H - 5, CAR_W - 6, 5, color);

    // Windshield
    rect(x + 4, y + 8, CAR_W - 8, 7, C_WHITE);

    // Side windows
    rect(x + 2, y + 17, 3, 5, C_DARK);
    rect(x + CAR_W - 5, y + 17, 3, 5, C_DARK);

    // Wheels
    rect(x - 2, y + 6, 3, 7, C_BLACK);
    rect(x + CAR_W - 1, y + 6, 3, 7, C_BLACK);

    rect(x - 2, y + 19, 3, 7, C_BLACK);
    rect(x + CAR_W - 1, y + 19, 3, 7, C_BLACK);
}

// =====================================================
// DRAW GAME
// =====================================================

void racing_draw()
{
    clear_screen(C_BLACK);

    // Header
    draw_text(8, 7, "FULL SPEED", C_CYAN, 2);
    draw_text(145, 10, "SCORE", C_WHITE, 1);
    draw_number(185, 10, score, C_YELLOW, 1);

    // Centered road
    rect(ROAD_X, ROAD_Y, ROAD_W,
         ROAD_BOTTOM - ROAD_Y, C_DARK);

    // Road boundaries
    rect(ROAD_X, ROAD_Y, 3,
         ROAD_BOTTOM - ROAD_Y, C_YELLOW);

    rect(ROAD_X + ROAD_W - 3, ROAD_Y, 3,
         ROAD_BOTTOM - ROAD_Y, C_YELLOW);

    // Lane dividers
    for (int y = ROAD_Y; y < ROAD_BOTTOM; y += 24)
    {
        rect(ROAD_X + LANE_W, y, 3, 12, C_WHITE);
        rect(ROAD_X + 2 * LANE_W, y, 3, 12, C_WHITE);
    }

    // Draw only opponents that have entered the road.
    for (int i = 0; i < 3; i++)
    {
        if (ob_y[i] >= ROAD_Y)
            draw_car(ob_x[i], ob_y[i], C_RED);
    }

    // Player car
    draw_car(car_x, PLAYER_Y, C_CYAN);

    // Crash overlay: readable text on a solid background.
    if (over)
    {
        const int box_x = 30;
        const int box_y = 120;
        const int box_w = SCREEN_W - 60;
        const int box_h = 70;

        rect(box_x, box_y, box_w, box_h, C_BLACK);
        border_rect(box_x, box_y, box_w, box_h, C_RED);

        draw_text(75, 132, "CRASH!", C_RED, 2);
        draw_text(66, 160, "A RESTART", C_WHITE, 1);
    }

    render_display();
}

// =====================================================
// STATUS
// =====================================================

bool racing_is_over()
{
    return over;
}

int racing_score()
{
    return score;
}
