#include "invaders.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdlib.h>
#include <string.h>
#include <hardware/timer.h>

// ============================================================
// ARES SPACE INVADERS - 320x240
// Six levels, static alien sprites, random single-alien descent,
// multi-projectile firing and hit explosions.
// ============================================================

static const int MAX_ENEMIES = 24;
static const int MAX_PLAYER_BULLETS = 64; // bounded Pico RAM pool
static const int MAX_EXPLOSIONS = 12;
static const int MAX_LEVELS = 6;

struct PlayerBullet {
    int x;
    int y;
    bool active;
};

struct Explosion {
    int x;
    int y;
    int frame;
    bool active;
};

static int px;
static int score;
static int lives;

static int enemy_x[MAX_ENEMIES];
static int enemy_y[MAX_ENEMIES];
static bool enemy_fast[MAX_ENEMIES];

static int enemy_count;
static int normal_count;
static int fast_count;
static int remaining;

static int enemy_dir;
static int enemy_step_tick;
static int enemy_step_period;
static int current_level;

static PlayerBullet bullets[MAX_PLAYER_BULLETS];
static Explosion explosions[MAX_EXPLOSIONS];

static uint32_t last_shot_us;
static uint32_t next_random_drop_us;
static int last_dropped_enemy;
static bool over;
static bool won;

// ---------------- LEVEL TABLE ----------------
// Level 1:  8 normal
// Level 2: 16 normal
// Level 3: 10 normal + 6 super/fast dropping
// Level 4:  8 normal + 8 fast dropping
// Level 5: 16 normal + 8 fast dropping
// Level 6: 12 normal + 12 fast dropping

static void get_level_counts(int level, int &normal, int &fast)
{
    switch (level)
    {
        case 1: normal = 8;  fast = 0;  break;
        case 2: normal = 16; fast = 0;  break;
        case 3: normal = 10; fast = 6;  break;
        case 4: normal = 8;  fast = 8;  break;
        case 5: normal = 16; fast = 8;  break;
        default: normal = 12; fast = 12; break;
    }
}

static int level_period(int level)
{
    // Formation movement gets quicker with each level.
    const int periods[MAX_LEVELS] = {14, 12, 10, 8, 6, 5};
    return periods[level - 1];
}


// One alien descends per event. Levels 1-2 are Easy, 3-4 Medium,
// and 5-6 Hard. Hard drops occur 4x as frequently as Easy.
static uint32_t random_drop_interval_us()
{
    if (current_level <= 2) return 1200000u; // Easy
    if (current_level <= 4) return 600000u;  // Medium
    return 300000u;                          // Hard
}

static void drop_one_random_alien()
{
    int active_count = 0;
    for (int i = 0; i < enemy_count; ++i)
        if (enemy_x[i] >= 0)
            ++active_count;

    if (active_count == 0)
        return;

    // Select exactly one living alien; avoid selecting the same alien
    // twice in a row whenever another living alien is available.
    int selected = -1;
    for (int attempt = 0; attempt < 32; ++attempt)
    {
        int candidate = rand() % enemy_count;
        if (enemy_x[candidate] >= 0 &&
            (active_count == 1 || candidate != last_dropped_enemy))
        {
            selected = candidate;
            break;
        }
    }

    if (selected < 0)
    {
        for (int i = 0; i < enemy_count; ++i)
        {
            if (enemy_x[i] >= 0 && (active_count == 1 || i != last_dropped_enemy))
            {
                selected = i;
                break;
            }
        }
    }

    if (selected >= 0)
    {
        enemy_y[selected] += 5;
        last_dropped_enemy = selected;
    }
}

// ---------------- EXPLOSIONS ----------------
static void add_explosion(int x, int y)
{
    for (int i = 0; i < MAX_EXPLOSIONS; i++)
    {
        if (!explosions[i].active)
        {
            explosions[i].x = x;
            explosions[i].y = y;
            explosions[i].frame = 0;
            explosions[i].active = true;
            return;
        }
    }
}

static void update_explosions()
{
    for (int i = 0; i < MAX_EXPLOSIONS; i++)
    {
        if (!explosions[i].active)
            continue;

        explosions[i].frame++;
        if (explosions[i].frame >= 8)
            explosions[i].active = false;
    }
}

static void draw_explosions()
{
    for (int i = 0; i < MAX_EXPLOSIONS; i++)
    {
        if (!explosions[i].active)
            continue;

        int x = explosions[i].x;
        int y = explosions[i].y;
        int f = explosions[i].frame;
        int r = 2 + f * 2;

        rect(x - 1, y - 1, 3, 3, C_WHITE);

        if (f < 5)
        {
            rect(x - r, y, 3, 2, C_ORANGE);
            rect(x + r - 2, y, 3, 2, C_ORANGE);
            rect(x, y - r, 2, 3, C_YELLOW);
            rect(x, y + r - 2, 2, 3, C_YELLOW);
        }

        if (f < 3)
        {
            rect(x - r, y - r, 2, 2, C_RED);
            rect(x + r - 1, y - r, 2, 2, C_RED);
            rect(x - r, y + r - 1, 2, 2, C_RED);
            rect(x + r - 1, y + r - 1, 2, 2, C_RED);
        }
    }
}

// ---------------- ALIEN GRAPHICS ----------------
static void draw_alien(int x, int y, bool fast)
{
    static const uint8_t sprite[8] = {
        0b00011000, 0b00111100, 0b01111110, 0b11011011,
        0b11111111, 0b00100100, 0b01011010, 0b10100101
    };

    uint16_t color = fast ? 0xA81F : C_GREEN;

    for (int sy = 0; sy < 8; sy++)
    {
        for (int sx = 0; sx < 8; sx++)
        {
            if (sprite[sy] & (1u << (7 - sx)))
                rect(x + sx * 2, y + sy * 2, 2, 2, color);
        }
    }

    // Fixed eyes and legs: no frame animation.
    rect(x + 5, y + 7, 3, 3, C_WHITE);
    rect(x + 16, y + 7, 3, 3, C_WHITE);
    rect(x + 3, y + 14, 4, 2, color);
    rect(x + 17, y + 14, 4, 2, color);

    if (fast)
        rect(x + 10, y - 3, 4, 2, 0xA81F);
}

// ---------------- PLAYER SHIP ----------------
static void draw_player()
{
    int y = SCREEN_H - 34;

    rect(px + 7, y, 6, 4, C_WHITE);
    rect(px + 4, y + 4, 12, 4, C_CYAN);
    rect(px, y + 8, 20, 5, C_CYAN);
    rect(px + 3, y + 13, 5, 3, C_BLUE);
    rect(px + 12, y + 13, 5, 3, C_BLUE);

    rect(px + 5, y + 16, 3, 3, C_ORANGE);
    rect(px + 13, y + 16, 3, 3, C_YELLOW);
}

// ---------------- PLAYER BULLETS ----------------
static void fire_bullet()
{
    // The update API supplies an A-button edge. Each edge creates
    // another shot; no previous shot needs to hit or disappear first.
    // 1 ms is the minimum software shot spacing.
    uint32_t now = time_us_32();
    if ((uint32_t)(now - last_shot_us) < 1000)
        return;

    for (int i = 0; i < MAX_PLAYER_BULLETS; i++)
    {
        if (!bullets[i].active)
        {
            bullets[i].x = px + 9;
            bullets[i].y = SCREEN_H - 39;
            bullets[i].active = true;
            last_shot_us = now;
            audio_play_sfx(SFX_LASER);
            return;
        }
    }
}

static void update_bullets()
{
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++)
    {
        if (!bullets[i].active)
            continue;

        bullets[i].y -= 8;

        if (bullets[i].y < 35)
            bullets[i].active = false;
    }
}

static void draw_bullets()
{
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++)
    {
        if (!bullets[i].active)
            continue;

        int x = bullets[i].x;
        int y = bullets[i].y;

        // Energy bolt and glowing trail.
        rect(x, y - 5, 2, 10, C_YELLOW);
        rect(x - 1, y - 2, 4, 4, C_WHITE);
        rect(x, y + 5, 2, 5, C_ORANGE);
    }
}

// ---------------- FORMATION SETUP ----------------
static void setup_level()
{
    get_level_counts(current_level, normal_count, fast_count);
    enemy_count = normal_count + fast_count;
    remaining = enemy_count;

    enemy_dir = 1;
    enemy_step_tick = 0;
    enemy_step_period = level_period(current_level);

    // 8 columns, centred, with up to 3 rows.
    const int columns = 8;
    const int spacing_x = 36;
    const int spacing_y = 24;
    const int formation_width = (columns - 1) * spacing_x + 24;
    const int start_x = (SCREEN_W - formation_width) / 2;
    const int start_y = 48;

    for (int i = 0; i < MAX_ENEMIES; i++)
    {
        enemy_x[i] = -100;
        enemy_y[i] = -100;
        enemy_fast[i] = false;
    }

    // Place normal aliens first, then fast aliens in the lower
    // rows where their rapid descent is easier to see.
    for (int i = 0; i < enemy_count; i++)
    {
        int row = i / columns;
        int col = i % columns;

        enemy_x[i] = start_x + col * spacing_x;
        enemy_y[i] = start_y + row * spacing_y;
        enemy_fast[i] = (i >= normal_count);
    }

    for (int i = 0; i < MAX_PLAYER_BULLETS; i++)
        bullets[i].active = false;

    for (int i = 0; i < MAX_EXPLOSIONS; i++)
        explosions[i].active = false;

    last_shot_us = 0;
    last_dropped_enemy = -1;
    next_random_drop_us = time_us_32() + random_drop_interval_us();
    over = false;
    won = false;
}

// ---------------- INITIALIZE ----------------
void invaders_init()
{
    px = SCREEN_W / 2 - 10;
    score = 0;
    lives = 3;
    current_level = 1;
    srand(time_us_32());

    setup_level();
}

// ---------------- UPDATE ----------------
void invaders_update(bool up, bool down, bool left,
                     bool right, bool a_edge)
{
    (void)up;
    (void)down;

    // A advances after a level clear. After game over, A retries
    // the six-level run from Level 1.
    if (over)
    {
        if (a_edge)
        {
            if (won && current_level < MAX_LEVELS)
            {
                current_level++;
                setup_level();
            }
            else if (won && current_level == MAX_LEVELS)
            {
                score = 0;
                lives = 3;
                current_level = 1;
                setup_level();
            }
            else
            {
                score = 0;
                lives = 3;
                current_level = 1;
                setup_level();
            }
        }
        return;
    }

    // Player movement.
    if (left) px -= 4;
    if (right) px += 4;

    if (px < 3) px = 3;
    if (px > SCREEN_W - 23) px = SCREEN_W - 23;

    // Independent shots: a new A press creates a bullet even if
    // other bullets are still travelling.
    if (a_edge)
        fire_bullet();

    update_bullets();
    update_explosions();

    // Move the formation horizontally. Reaching an edge only reverses
    // direction; vertical drops are handled separately, one random alien
    // at a time, with a cooldown between events.
    if (++enemy_step_tick >= enemy_step_period)
    {
        enemy_step_tick = 0;

        bool hit_edge = false;
        for (int i = 0; i < enemy_count; i++)
        {
            if (enemy_x[i] < 0)
                continue;

            if ((enemy_dir > 0 && enemy_x[i] >= SCREEN_W - 27) ||
                (enemy_dir < 0 && enemy_x[i] <= 3))
            {
                hit_edge = true;
                break;
            }
        }

        if (hit_edge)
            enemy_dir = -enemy_dir;

        for (int i = 0; i < enemy_count; i++)
        {
            if (enemy_x[i] >= 0)
                enemy_x[i] += enemy_dir * (2 + current_level / 3);
        }
    }

    // Random individual descent: never drop two aliens in the same event.
    uint32_t now_us = time_us_32();
    if ((int32_t)(now_us - next_random_drop_us) >= 0)
    {
        drop_one_random_alien();

        // Add a little timing variation so drops do not feel mechanical.
        uint32_t base_interval = random_drop_interval_us();
        uint32_t variation = base_interval / 5u;
        int32_t jitter = (int32_t)(rand() % (variation * 2u + 1u)) -
                         (int32_t)variation;
        next_random_drop_us = now_us + (uint32_t)((int32_t)base_interval + jitter);
    }

    // Formation reaching the player's line costs one life.
    for (int i = 0; i < enemy_count; i++)
    {
        if (enemy_x[i] >= 0 && enemy_y[i] >= SCREEN_H - 58)
        {
            lives--;

            if (lives <= 0)
            {
                over = true;
                won = false;
                audio_play_sfx(SFX_GAME_OVER);
            }
            else
            {
                setup_level();
            }
            return;
        }
    }

    // Every active bullet is tested independently against every alien.
    for (int b = 0; b < MAX_PLAYER_BULLETS; b++)
    {
        if (!bullets[b].active)
            continue;

        for (int i = 0; i < enemy_count; i++)
        {
            if (enemy_x[i] < 0)
                continue;

            int bx = bullets[b].x;
            int by = bullets[b].y;
            int ex = enemy_x[i];
            int ey = enemy_y[i];

            if (bx >= ex && bx <= ex + 23 &&
                by >= ey && by <= ey + 15)
            {
                bullets[b].active = false;
                add_explosion(ex + 12, ey + 8);
                enemy_x[i] = -100;
                remaining--;
                score += 1;
                audio_play_sfx(SFX_EXPLOSION);
                break;
            }
        }
    }

    // Level clear.
    if (remaining <= 0)
    {
        won = true;
        over = true;
        score += (current_level == MAX_LEVELS) ? 100 : 50;
        audio_play_sfx(SFX_VICTORY);
    }
}

// ---------------- HUD ----------------
static void draw_hud()
{
    draw_text(8, 5, "ARES", C_CYAN, 1);
    draw_text(70, 5, "SPACE INVADERS", C_WHITE, 1);

    draw_text(8, 20, "SCORE", C_WHITE, 1);
    draw_number(48, 20, score, C_YELLOW, 1);

    draw_text(145, 20, "LEVEL", C_WHITE, 1);
    draw_number(185, 20, current_level, C_CYAN, 1);

    draw_text(235, 20, "LIFE", C_WHITE, 1);
    for (int i = 0; i < lives; i++)
        rect(270 + i * 12, 21, 8, 7, C_GREEN);

    // Enemy progress bar.
    rect(8, 36, SCREEN_W - 16, 3, C_DARK);
    int bar_width = (SCREEN_W - 16) * remaining /
                    (enemy_count ? enemy_count : 1);
    if (bar_width > 0)
        rect(8, 36, bar_width, 3, C_GREEN);

}

// ---------------- DRAW GAME ----------------
void invaders_draw()
{
    clear_screen(C_BLACK);
    draw_hud();

    static const uint16_t stars[][2] = {
        {18, 55}, {55, 91}, {94, 62}, {132, 108}, {173, 58},
        {211, 94}, {250, 65}, {294, 112}, {35, 150}, {280, 158},
        {116, 174}, {198, 145}, {68, 188}, {242, 184}
    };

    for (int i = 0; i < (int)(sizeof(stars) / sizeof(stars[0])); i++)
        rect(stars[i][0], stars[i][1], 1, 1, 0x7BEF);

    for (int i = 0; i < enemy_count; i++)
    {
        if (enemy_x[i] >= 0)
            draw_alien(enemy_x[i], enemy_y[i], enemy_fast[i]);
    }

    draw_player();
    draw_bullets();
    draw_explosions();

    draw_text(8, SCREEN_H - 12, "L/R MOVE   A FIRE   B MENU", C_WHITE, 1);

    if (over && won)
    {
        rect(48, 75, 224, 100, C_DARK);
        border_rect(48, 75, 224, 100, C_GREEN);

        if (current_level < MAX_LEVELS)
        {
            draw_text(91, 88, "LEVEL CLEAR", C_GREEN, 2);
            draw_text(103, 116, "LEVEL", C_WHITE, 1);
            draw_number(145, 116, current_level, C_YELLOW, 1);
            draw_text(83, 139, "A NEXT LEVEL", C_CYAN, 1);
        }
        else
        {
            draw_text(89, 88, "MISSION DONE", C_YELLOW, 2);
            draw_text(99, 116, "ALL 6 LEVELS", C_WHITE, 1);
            draw_text(104, 139, "A PLAY AGAIN", C_CYAN, 1);
        }
    }
    else if (over)
    {
        rect(58, 78, 204, 94, C_DARK);
        border_rect(58, 78, 204, 94, C_RED);
        draw_text(105, 92, "GAME OVER", C_RED, 2);
        draw_text(102, 119, "SCORE", C_WHITE, 1);
        draw_number(145, 119, score, C_YELLOW, 1);
        draw_text(103, 145, "A RETRY", C_CYAN, 1);
    }

    render_display();
}

// ---------------- STATUS ----------------
bool invaders_is_over()
{
    // A level-clear screen is not a game-over state.
    // Keep the game loop active so A can advance to the next level.
    // Return true only after the player has actually lost all lives.
    return over && !won;
}

bool invaders_is_won()
{
    return won;
}

int invaders_score()
{
    return score;
}
