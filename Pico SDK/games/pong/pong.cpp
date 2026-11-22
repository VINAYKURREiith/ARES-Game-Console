
#include "pong.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdlib.h>
#include <math.h>

// ---------------- SINGLE-PLAYER PONG ----------------
static const int PONG_PADDLE_W = 46;
static const int PONG_PADDLE_H = 6;
static const int PONG_BALL_SIZE = 7;

static const int PONG_TOP = 42;
#define PONG_BOTTOM (SCREEN_H - 20)
static const int PONG_LEFT = 12;
#define PONG_RIGHT (SCREEN_W - 12)

static int pong_win_score() { return 10 + (game_level - 1) / 20; }

static int pong_player_x = 0;
static float pong_ball_x = 0.0f;
static float pong_ball_y = 0.0f;
static float pong_ball_vx = 0.0f;
static float pong_ball_vy = 0.0f;

static int pong_player_score = 0;
static int pong_lives = 3;

static bool pong_game_over = false;
static bool pong_won = false;
static uint32_t pong_last_frame = 0;

// ---------------- SERVE BALL ----------------
static void pong_serve_ball()
{
    pong_ball_x = (SCREEN_W - PONG_BALL_SIZE) / 2.0f;
    pong_ball_y = (SCREEN_H - PONG_BALL_SIZE) / 2.0f;

    float speed = 2.2f + (float)(game_level - 1) * 0.006f;
    if (speed > 4.6f) speed = 4.6f;

    pong_ball_vx = (rand() % 2 == 0) ? -speed * 0.75f : speed * 0.75f;
    pong_ball_vy = speed;

    pong_last_frame = to_ms_since_boot(get_absolute_time());
}

// ---------------- INITIALIZE ----------------
void pong_init()
{
    pong_player_x = (SCREEN_W - PONG_PADDLE_W) / 2;

    pong_player_score = 0;
    pong_lives = 3;
    pong_game_over = false;
    pong_won = false;

    pong_serve_ball();
}

// ---------------- DRAW ----------------
void pong_draw()
{
    clear_screen(C_BLACK);

    draw_text(10, 7, "ARES PONG", C_CYAN, 2);

    draw_text(10, 27, "SCORE", C_WHITE, 1);
    draw_number(52, 27, pong_player_score, C_GREEN, 1);

    draw_text(105, 27, "LV", C_CYAN, 1); draw_number(124, 27, game_level, C_YELLOW, 1);
    draw_text(175, 27, "LIVES", C_WHITE, 1);
    draw_number(190, 27, pong_lives, C_YELLOW, 1);

    // Playfield.
    border_rect(PONG_LEFT, PONG_TOP,
                PONG_RIGHT - PONG_LEFT,
                PONG_BOTTOM - PONG_TOP, C_CYAN);

    // Decorative center line.
    for (int y = PONG_TOP + 8; y < PONG_BOTTOM - 8; y += 16)
        rect(SCREEN_W / 2 - 1, y, 2, 7, C_DARK);

    // Player paddle only. No CPU paddle.
    rect(pong_player_x, PONG_BOTTOM - 12,
         PONG_PADDLE_W, PONG_PADDLE_H, C_CYAN);

    // Ball.
    rect((int)pong_ball_x, (int)pong_ball_y,
         PONG_BALL_SIZE, PONG_BALL_SIZE, C_YELLOW);

    if (pong_game_over)
    {
        rect(25, SCREEN_H / 2 - 35, SCREEN_W - 50, 72, C_DARK);
        border_rect(25, SCREEN_H / 2 - 35,
                    SCREEN_W - 50, 72, pong_won ? C_GREEN : C_RED);

        draw_text(65, SCREEN_H / 2 - 23, "GAME OVER", C_RED, 2);
        draw_text(48, SCREEN_H / 2 + 3, pong_won ? "A NEXT LEVEL" : "A RETRY", C_WHITE, 1);
        if (pong_won) draw_text(72, SCREEN_H / 2 + 20, "STAGE CLEAR", C_GREEN, 1);
    }

    render_display();
}

// ---------------- UPDATE BALL ----------------
static void pong_update_game()
{
    if (pong_game_over)
        return;

    pong_ball_x += pong_ball_vx;
    pong_ball_y += pong_ball_vy;

    // Left wall bounce.
    if (pong_ball_x <= PONG_LEFT + 1)
    {
        pong_ball_x = PONG_LEFT + 1;
        pong_ball_vx = fabsf(pong_ball_vx);
        audio_play_sfx(SFX_WALL_HIT);
    }

    // Right wall bounce.
    if (pong_ball_x + PONG_BALL_SIZE >= PONG_RIGHT - 1)
    {
        pong_ball_x = PONG_RIGHT - 1 - PONG_BALL_SIZE;
        pong_ball_vx = -fabsf(pong_ball_vx);
        audio_play_sfx(SFX_WALL_HIT);
    }

    // Top wall bounce: no opponent paddle.
    if (pong_ball_y <= PONG_TOP + 1)
    {
        pong_ball_y = PONG_TOP + 1;
        pong_ball_vy = fabsf(pong_ball_vy);
        audio_play_sfx(SFX_WALL_HIT);
    }

    // Player paddle collision.
    const int paddle_y = PONG_BOTTOM - 12;

    bool overlaps_x =
        pong_ball_x + PONG_BALL_SIZE > pong_player_x &&
        pong_ball_x < pong_player_x + PONG_PADDLE_W;

    bool crosses_paddle =
        pong_ball_vy > 0 &&
        pong_ball_y + PONG_BALL_SIZE >= paddle_y &&
        pong_ball_y + PONG_BALL_SIZE <= paddle_y + PONG_PADDLE_H + 4;

    if (overlaps_x && crosses_paddle)
    {
        // Place ball above paddle to avoid repeated collisions.
        pong_ball_y = paddle_y - PONG_BALL_SIZE;
        pong_ball_vy = -fabsf(pong_ball_vy);

        // Paddle hit position controls horizontal direction.
        float hit =
            (pong_ball_x + PONG_BALL_SIZE / 2.0f) -
            (pong_player_x + PONG_PADDLE_W / 2.0f);

        pong_ball_vx = hit / 12.0f;

        if (pong_ball_vx > 3.2f)  pong_ball_vx = 3.2f;
        if (pong_ball_vx < -3.2f) pong_ball_vx = -3.2f;

        if (fabsf(pong_ball_vx) < 0.7f)
            pong_ball_vx = (hit < 0) ? -0.7f : 0.7f;

        pong_player_score++;

        audio_play_sfx(SFX_PADDLE_HIT);

        if (pong_player_score >= pong_win_score()) { pong_game_over = true; pong_won = true; audio_play_sfx(SFX_VICTORY); }
    }

    // Ball missed the paddle.
    if (pong_ball_y + PONG_BALL_SIZE >= PONG_BOTTOM)
    {
        pong_lives--;

        audio_play_sfx(SFX_LIFE_LOST);

        if (pong_lives <= 0)
        {
            pong_game_over = true;
            audio_play_sfx(SFX_GAME_OVER);
        }
        else
        {
            pong_serve_ball();
        }
    }
}

// ---------------- GAME CONTROL ----------------
void pong_update(bool left, bool right)
{
    if (pong_game_over)
        return;

    if (left)
        pong_player_x -= 4;

    if (right)
        pong_player_x += 4;

    if (pong_player_x < PONG_LEFT + 2)
        pong_player_x = PONG_LEFT + 2;

    if (pong_player_x > PONG_RIGHT - PONG_PADDLE_W - 2)
        pong_player_x = PONG_RIGHT - PONG_PADDLE_W - 2;

    uint32_t now = to_ms_since_boot(get_absolute_time());

    if (now - pong_last_frame >= 16)
    {
        pong_update_game();
        pong_last_frame = now;
    }
}

bool pong_is_over()
{
    return pong_game_over;
}
bool pong_is_won() { return pong_won; }

int pong_get_player_score()
{
    return pong_player_score;
}

uint32_t pong_get_last_frame()
{
    return pong_last_frame;
}

void pong_set_last_frame(uint32_t value)
{
    pong_last_frame = value;
}

void pong_frame(bool up, bool down, bool left, bool right, bool a_edge)
{
    (void)up;
    (void)down;

    if (pong_game_over && a_edge)
    {
        pong_init();
        return;
    }

    pong_update(left, right);
}
