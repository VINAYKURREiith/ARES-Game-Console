#include "tetris.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ---------------- GAME SETTINGS ----------------
// Requested board: 20 columns x 20 rows.
// Every logical cell is exactly 10x10 pixels (200x200 total).
static const int COLS = 20;
static const int ROWS = 20;
static const int CELL = 10;
static const int BOARD_X = 8;
static const int BOARD_Y = 20;
static const int BOARD_W = COLS * CELL;   // 200 pixels
static const int BOARD_H = ROWS * CELL;   // 200 pixels
static const int PANEL_X = 216; // Starts to the right of the 200px board

static int grid[ROWS][COLS];
static int px, py, piece, next_piece, rot, score, tick;
static bool over;
static int difficulty; // 0 = Easy, 1 = Medium, 2 = Hard
static const int difficulty_multiplier[3] = {1, 2, 4};

// ---------------- COLORS ----------------
static const uint16_t piece_colors[7] = {
    0x07FF, // I - cyan
    0x001F, // J - blue
    0xFD20, // L - orange
    0xFFE0, // O - yellow
    0x07E0, // S - green
    0xF81F, // T - purple
    0xF800  // Z - red
};

// Each piece is a 4x4 matrix.
static const uint8_t shapes[7][4][4] = {
    {{0,0,0,0},{1,1,1,1},{0,0,0,0},{0,0,0,0}},
    {{1,0,0,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
    {{0,0,1,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
    {{0,1,1,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}},
    {{0,1,1,0},{1,1,0,0},{0,0,0,0},{0,0,0,0}},
    {{0,1,0,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
    {{1,1,0,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}}
};

// ---------------- PIECE ROTATION ----------------
static bool on(int x, int y, int r)
{
    int sx = x;
    int sy = y;

    for (int i = 0; i < (r & 3); i++)
    {
        int temp = sx;
        sx = sy;
        sy = 3 - temp;
    }

    return shapes[piece][sy][sx] != 0;
}

// ---------------- COLLISION ----------------
static bool fits(int nx, int ny, int nr)
{
    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (!on(x, y, nr))
                continue;

            int gx = nx + x;
            int gy = ny + y;

            if (gx < 0 || gx >= COLS || gy >= ROWS)
                return false;

            if (gy >= 0 && grid[gy][gx])
                return false;
        }
    }

    return true;
}

// ---------------- SPAWN ----------------
static void spawn()
{
    piece = next_piece;
    next_piece = rand() % 7;

    rot = 0;
    px = (COLS - 4) / 2;
    py = 0;

    if (!fits(px, py, rot))
        over = true;
}

// ---------------- LOCK AND CLEAR LINES ----------------
static void lock_piece()
{
    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (on(x, y, rot))
            {
                int gx = px + x;
                int gy = py + y;

                if (gx >= 0 && gx < COLS && gy >= 0 && gy < ROWS)
                    grid[gy][gx] = piece + 1;
            }
        }
    }

    int lines = 0;

    for (int y = ROWS - 1; y >= 0; y--)
    {
        bool full = true;

        for (int x = 0; x < COLS; x++)
        {
            if (!grid[y][x])
            {
                full = false;
                break;
            }
        }

        if (full)
        {
            lines++;

            for (int yy = y; yy > 0; yy--)
                for (int x = 0; x < COLS; x++)
                    grid[yy][x] = grid[yy - 1][x];

            for (int x = 0; x < COLS; x++)
                grid[0][x] = 0;

            y++;
        }
    }

    if (lines == 1) { score += 1; audio_play_sfx(SFX_LINE_CLEAR); }
    if (lines == 2) { score += 3; audio_play_sfx(SFX_LINE_CLEAR); }
    if (lines == 3) { score += 5; audio_play_sfx(SFX_LINE_CLEAR); }
    if (lines >= 4) { score += 8; audio_play_sfx(SFX_VICTORY); }

    spawn();
}

// ---------------- INITIALIZE ----------------
void tetris_init()
{
    memset(grid, 0, sizeof(grid));

    score = 0;
    tick = 0;
    over = false;
    difficulty = console_difficulty;
    if (difficulty < 0) difficulty = 0;
    if (difficulty > 2) difficulty = 2;

    next_piece = rand() % 7;
    spawn();
}

// ---------------- UPDATE ----------------
void tetris_update(bool up, bool down, bool left,
                   bool right, bool a_edge)
{
    (void)up;

    if (over)
        return;

    if (left && fits(px - 1, py, rot))
        px--;

    if (right && fits(px + 1, py, rot))
        px++;

    if (a_edge)
    {
        int new_rot = (rot + 1) & 3;

        if (fits(px, py, new_rot))
            rot = new_rot;
    }

    // Gravity rate: Easy = 1x, Medium = 2x, Hard = 4x.
    // Adding the multiplier to the accumulator gives exact average
    // 1:2:4 drop rates without integer interval-rounding errors.
    int base_interval = 20 + score / 5;
    if (base_interval < 4)
        base_interval = 4;

    tick += difficulty_multiplier[difficulty];

    if (down || tick >= base_interval)
    {
        if (down)
            tick = 0;
        else
            tick -= base_interval;

        if (fits(px, py + 1, rot))
            py++;
        else
        {
            tick = 0;
            lock_piece();
        }
    }
}

// ---------------- DRAW BLOCK ----------------
static void draw_block(int x, int y, uint16_t color)
{
    // Draw inside a 10x10 cell, leaving a 1px dark gap.
    rect(x + 1, y + 1, CELL - 2, CELL - 2, color);
    rect(x + 2, y + 1, CELL - 4, 1, C_WHITE);
    rect(x + 1, y + 2, 1, CELL - 4, C_WHITE);
}

// ---------------- DRAW NEXT PIECE ----------------
static void draw_next_piece()
{
    draw_text(PANEL_X, 55, "NEXT", C_CYAN, 1);
    border_rect(PANEL_X, 70, 75, 60, C_DARK);

    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (shapes[next_piece][y][x])
            {
                int dx = PANEL_X + 17 + x * 10;
                int dy = 77 + y * 10;
                rect(dx, dy, 9, 9, piece_colors[next_piece]);
            }
        }
    }
}

// ---------------- DRAW GAME - 320x240 ----------------
void tetris_draw()
{
    clear_screen(C_BLACK);



    // LEFT: exact 200x200 board. 20 columns x 20 rows,
    // with every cell measuring 10x10 pixels.
    border_rect(BOARD_X - 1, BOARD_Y - 1,
                BOARD_W + 2, BOARD_H + 2, C_CYAN);
    rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H, C_DARK);

    // Vertical grid lines: 19 internal column boundaries.
    for (int x = 1; x < COLS; x++)
        rect(BOARD_X + x * CELL, BOARD_Y, 1, BOARD_H, C_BLACK);

    // Horizontal grid lines: 19 internal row boundaries.
    for (int y = 1; y < ROWS; y++)
        rect(BOARD_X, BOARD_Y + y * CELL, BOARD_W, 1, C_BLACK);

    // Locked blocks, including the complete bottom row.
    for (int y = 0; y < ROWS; y++)
    {
        for (int x = 0; x < COLS; x++)
        {
            if (grid[y][x])
            {
                draw_block(BOARD_X + x * CELL, BOARD_Y + y * CELL,
                           piece_colors[grid[y][x] - 1]);
            }
        }
    }

    // Active falling piece.
    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (on(x, y, rot) && py + y >= 0 && py + y < ROWS)
            {
                draw_block(BOARD_X + (px + x) * CELL,
                           BOARD_Y + (py + y) * CELL,
                           piece_colors[piece]);
            }
        }
    }

    // RIGHT: information panel.
    draw_text(PANEL_X, 12, "TETRIS", C_CYAN, 1);
    draw_text(PANEL_X, 35, "SCORE", C_WHITE, 1);
    draw_number(PANEL_X, 47, score, C_YELLOW, 1);

    const char *difficulty_names[3] = {"EASY", "MED", "HARD"};
    const uint16_t difficulty_colors[3] = {C_GREEN, C_YELLOW, C_RED};
    draw_text(PANEL_X, 137, difficulty_names[difficulty],
              difficulty_colors[difficulty], 1);

    draw_next_piece();

    draw_text(PANEL_X, 145, "A ROTATE", C_GREEN, 1);
    draw_text(PANEL_X, 162, "L/R MOVE", C_WHITE, 1);
    draw_text(PANEL_X, 179, "DOWN FAST", C_WHITE, 1);
    draw_text(PANEL_X, 196, "B MENU", C_CYAN, 1);

    if (over)
    {
        rect(25, 95, 165, 50, C_BLACK);
        border_rect(25, 95, 165, 50, C_RED);
        draw_text(48, 105, "GAME OVER", C_RED, 2);
        draw_text(58, 127, "A RESTART", C_WHITE, 1);
    }

    render_display();
}

// ---------------- STATUS ----------------
bool tetris_is_over()
{
    return over;
}

int tetris_score()
{
    return score;
}
