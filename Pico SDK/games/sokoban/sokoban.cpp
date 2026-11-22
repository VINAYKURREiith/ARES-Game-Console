#include "sokoban.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdint.h>

// ARES Sokoban: 300 deterministic levels. The board is generated so every
// level remains solvable: each box has a clear horizontal push lane to its goal.
// Obstacles and mines are placed only outside active box lanes.
namespace {
constexpr int W = 10;
constexpr int H = 8;
constexpr int MAX_BOXES = 6;
constexpr int MAX_LEVEL = 300;
constexpr char WALL = '#';
constexpr char FLOOR = ' ';
constexpr char BOX = '$';
constexpr char MINE = '^';

char map[H][W];
bool goals[H][W];
bool mine[H][W];
int player_x = 1, player_y = 1;
int box_count = 1, placed = 0;
int level = 1, score = 0, level_moves = 0, level_pushes = 0;
bool level_complete = false;
bool game_complete = false;

static uint32_t rng_state;
uint32_t next_rand() {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 17;
    rng_state ^= rng_state << 5;
    return rng_state;
}

bool inside(int x, int y) { return x >= 0 && x < W && y >= 0 && y < H; }
bool is_goal(int x, int y) { return inside(x, y) && goals[y][x]; }
bool box_at(int x, int y) { return inside(x, y) && map[y][x] == BOX; }

void count_placed() {
    placed = 0;
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x)
            if (box_at(x, y) && goals[y][x]) ++placed;
}

void build_level() {
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            map[y][x] = (x == 0 || x == W - 1 || y == 0 || y == H - 1) ? WALL : FLOOR;
            goals[y][x] = false;
            mine[y][x] = false;
        }
    }

    // Keep level 1 as the gentle tutorial, then advance the layout difficulty
    // to the former level-13 pattern at displayed level 2. This prevents the
    // first eleven levels from feeling almost identical while preserving the
    // displayed stage number and automatic progression.
    const int difficulty_level = (level == 1) ? 1 : level + 11;
    // Difficulty rises gradually: additional box lanes, obstacles and hazards.
    box_count = 1 + (difficulty_level - 1) / 12;
    if (box_count > MAX_BOXES) box_count = MAX_BOXES;
    rng_state = 0xA53C9E1Du ^ (static_cast<uint32_t>(difficulty_level) * 0x9E3779B9u);
    if (rng_state == 0) rng_state = 1;

    // Six independent lanes. Every active lane has an unobstructed box-to-goal
    // route, and the left access column stays clear so the player can line up.
    for (int i = 0; i < box_count; ++i) {
        const int y = 1 + i;
        map[y][2] = BOX;
        goals[y][7] = true;
    }

    // Extra obstacles and mines appear as the level increases, but never in a
    // box lane, on the access column, or on a goal. Mines reset the current
    // level when stepped on; they never make the required push path impossible.
    const int obstacle_count = (difficulty_level < 10) ? 0 : (difficulty_level / 12 > 18 ? 18 : difficulty_level / 12);
    const int mine_count = (difficulty_level < 25) ? 0 : (difficulty_level / 25 > 6 ? 6 : difficulty_level / 25);
    for (int n = 0, tries = 0; n < obstacle_count && tries < 200; ++tries) {
        int x = 2 + static_cast<int>(next_rand() % 6u); // x=2..7
        int y = 1 + static_cast<int>(next_rand() % 6u); // y=1..6
        if (y <= box_count || x == 7 || goals[y][x] || map[y][x] != FLOOR) continue;
        map[y][x] = WALL;
        ++n;
    }
    for (int n = 0, tries = 0; n < mine_count && tries < 200; ++tries) {
        int x = 2 + static_cast<int>(next_rand() % 5u); // x=2..6
        int y = 1 + static_cast<int>(next_rand() % 6u);
        if (y <= box_count || goals[y][x] || map[y][x] != FLOOR) continue;
        mine[y][x] = true;
        ++n;
    }

    // Start in the clear access column. Each box can be pushed right to its goal.
    player_x = 1;
    player_y = H - 2;
    level_moves = 0;
    level_pushes = 0;
    level_complete = false;
    game_complete = false;
    count_placed();
}

void restart_level() { build_level(); }
}

void sokoban_init() {
    level = 1;
    score = 0;
    build_level();
}

void sokoban_start_level(int start_level) {
    if (start_level < 1) start_level = 1;
    if (start_level > MAX_LEVEL) start_level = MAX_LEVEL;
    level = start_level; score = 0; build_level();
}

void sokoban_update(bool up, bool down, bool left, bool right, bool a) {
    if (game_complete) {
        if (a) sokoban_init();
        return;
    }
    if (level_complete) {
        if (a) {
            if (level >= MAX_LEVEL) {
                game_complete = true;
            } else {
                ++level;
                build_level();
            }
        }
        return;
    }

    // A restarts this level; directional input moves one tile per input event.
    if (a) { restart_level(); return; }
    int dx = 0, dy = 0;
    if (left) dx = -1;
    else if (right) dx = 1;
    else if (up) dy = -1;
    else if (down) dy = 1;
    if (dx == 0 && dy == 0) return;

    const int nx = player_x + dx;
    const int ny = player_y + dy;
    if (!inside(nx, ny) || map[ny][nx] == WALL) return;

    if (box_at(nx, ny)) {
        const int bx = nx + dx, by = ny + dy;
        if (!inside(bx, by) || map[by][bx] == WALL || box_at(bx, by) || mine[by][bx]) return;
        map[ny][nx] = FLOOR;
        map[by][bx] = BOX;
        ++level_pushes;
        audio_play_sfx(SFX_BOX_PUSH);
    } else {
        audio_play_sfx(SFX_UI_MOVE);
    }

    player_x = nx;
    player_y = ny;
    ++score;
    ++level_moves;

    if (mine[player_y][player_x]) {
        audio_play_sfx(SFX_LIFE_LOST);
        restart_level();
        return;
    }

    count_placed();
    if (placed == box_count) {
        level_complete = true;
        audio_play_sfx(SFX_PUZZLE_SOLVED);
    }
}

void sokoban_draw() {
    clear_screen(C_BLACK);
    draw_text(8, 5, "SOKOBAN", C_CYAN, 2);
    draw_text(132, 8, "LV", C_WHITE, 1);
    draw_number(150, 8, level, C_YELLOW, 1);
    draw_text(190, 8, "BOX", C_WHITE, 1);
    draw_number(222, 8, placed, C_YELLOW, 1);
    draw_text(244, 8, "/", C_WHITE, 1);
    draw_number(254, 8, box_count, C_YELLOW, 1);
    draw_text(8, 29, "MOVES", C_WHITE, 1);
    draw_number(53, 29, level_moves, C_YELLOW, 1);
    draw_text(100, 29, "PUSH", C_WHITE, 1);
    draw_number(136, 29, level_pushes, C_YELLOW, 1);

    const int tile = 22;
    const int x0 = (SCREEN_W - W * tile) / 2;
    const int y0 = 43;
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            const int xx = x0 + x * tile;
            const int yy = y0 + y * tile;
            if (map[y][x] == WALL) {
                rect(xx, yy, tile - 1, tile - 1, C_BLUE);
                border_rect(xx, yy, tile - 1, tile - 1, C_CYAN);
            } else {
                rect(xx, yy, tile - 1, tile - 1, C_DARK);
                border_rect(xx, yy, tile - 1, tile - 1, 0x39E7);
            }
            if (goals[y][x]) {
                rect(xx + 7, yy + 7, 7, 7, C_YELLOW);
                border_rect(xx + 5, yy + 5, 11, 11, C_ORANGE);
            }
            if (mine[y][x]) {
                // Clearly marked hazard tile.
                rect(xx + 5, yy + 5, 11, 11, C_RED);
                draw_text(xx + 7, yy + 6, "!", C_WHITE, 1);
            }
            if (map[y][x] == BOX) {
                rect(xx + 3, yy + 3, tile - 7, tile - 7, C_ORANGE);
                border_rect(xx + 3, yy + 3, tile - 7, tile - 7, C_YELLOW);
                if (goals[y][x]) rect(xx + 8, yy + 8, 5, 5, C_GREEN);
            }
            if (x == player_x && y == player_y) {
                rect(xx + 5, yy + 5, tile - 11, tile - 11, C_CYAN);
                rect(xx + 9, yy + 8, 3, 3, C_WHITE);
            }
        }
    }

    draw_text(8, 220, "ARROWS MOVE/PUSH", C_WHITE, 1);
    draw_text(8, 232, "A RESTART/NEXT  B MENU", C_CYAN, 1);
    if (level_complete && !game_complete) {
        border_rect(45, 95, SCREEN_W - 90, 42, C_GREEN);
        draw_text(65, 104, "LEVEL CLEAR!", C_GREEN, 2);
        draw_text(66, 124, "PRESS A: NEXT", C_WHITE, 1);
    }
    if (game_complete) {
        border_rect(35, 91, SCREEN_W - 70, 54, C_YELLOW);
        draw_text(57, 101, "300 LEVELS!", C_YELLOW, 2);
        draw_text(58, 124, "A: PLAY AGAIN", C_WHITE, 1);
    }
    render_display();
}

bool sokoban_is_over() { return game_complete; }
int sokoban_score() { return score; }

bool sokoban_is_won() { return game_complete; }
