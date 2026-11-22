#include "game2048.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>

// =====================================================
// GAME STATE
// =====================================================

static int board[4][4];
static int score;
static bool over;
static bool merged_this_move;

// =====================================================
// TILE COLORS
// Every tile value has a distinct background and a
// deliberately selected high-contrast number color.
// =====================================================

static uint16_t tile_color(int value)
{
    // Light, clearly separated tile colours. All values use
    // black numbers so the text remains readable.
    switch (value)
    {
        case 0:     return 0x3186; // Muted slate for empty cells
        case 2:     return 0xFFFF; // White
        case 4:     return 0xFFE0; // Pale yellow
        case 8:     return 0xFD80; // Light orange
        case 16:    return 0xFBB2; // Light pink
        case 32:    return 0xD6DF; // Pale lavender
        case 64:    return 0xFBAA; // Light rose
        case 128:   return 0xBFEF; // Light green
        case 256:   return 0xBFF7; // Light mint
        case 512:   return 0xAEFF; // Light sky blue
        case 1024:  return 0xD5BF; // Light violet
        case 2048:  return 0xF6BF; // Light magenta-pink
        case 4096:  return 0xAFFA; // Pale aqua
        case 8192:  return 0xFFB7; // Pale peach
        case 16384: return 0xE73F; // Pale lilac
        default:    return 0xDEFB; // Very high values: light grey-blue
    }
}

static uint16_t tile_text_color(int value)
{
    (void)value;
    return C_BLACK;
}

// =====================================================
// SPAWN A NEW TILE
// =====================================================

static void add_tile()
{
    int empty = 0;

    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (board[y][x] == 0)
                empty++;
        }
    }

    if (empty == 0)
        return;

    int pick = rand() % empty;

    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (board[y][x] == 0)
            {
                if (pick == 0)
                {
                    board[y][x] = (rand() % 10 == 0) ? 4 : 2;
                    return;
                }

                pick--;
            }
        }
    }
}

// =====================================================
// INITIALIZE GAME
// =====================================================

void game2048_init()
{
    memset(board, 0, sizeof(board));

    score = 0;
    over = false;

    add_tile();
    add_tile();
}

// =====================================================
// MOVE AND MERGE TILES
// Direction:
// 0 = Left, 1 = Right, 2 = Up, 3 = Down
// =====================================================

static bool move_board(int dir)
{
    bool changed = false;
    merged_this_move = false;

    for (int line = 0; line < 4; line++)
    {
        int vals[4] = {0, 0, 0, 0};
        int n = 0;

        for (int k = 0; k < 4; k++)
        {
            int x, y;

            if (dir < 2)
            {
                x = (dir == 0) ? k : 3 - k;
                y = line;
            }
            else
            {
                x = line;
                y = (dir == 2) ? k : 3 - k;
            }

            if (board[y][x] != 0)
                vals[n++] = board[y][x];
        }

        // Merge equal adjacent values once per move.
        for (int k = 0; k < n - 1; k++)
        {
            if (vals[k] == vals[k + 1])
            {
                vals[k] *= 2;
                score += vals[k];
                merged_this_move = true;
                audio_play_merge((uint32_t)vals[k]);

                for (int j = k + 1; j < n - 1; j++)
                    vals[j] = vals[j + 1];

                n--;
                vals[n] = 0;
            }
        }

        for (int k = n; k < 4; k++)
            vals[k] = 0;

        for (int k = 0; k < 4; k++)
        {
            int x, y;

            if (dir < 2)
            {
                x = (dir == 0) ? k : 3 - k;
                y = line;
            }
            else
            {
                x = line;
                y = (dir == 2) ? k : 3 - k;
            }

            if (board[y][x] != vals[k])
                changed = true;

            board[y][x] = vals[k];
        }
    }

    return changed;
}

// =====================================================
// CHECK WHETHER ANY MOVES REMAIN
// =====================================================

static bool has_moves()
{
    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            if (board[y][x] == 0)
                return true;

            if (x < 3 && board[y][x] == board[y][x + 1])
                return true;

            if (y < 3 && board[y][x] == board[y + 1][x])
                return true;
        }
    }

    return false;
}

// =====================================================
// UPDATE GAME
// =====================================================

void game2048_update(bool up, bool down, bool left,
                     bool right, bool a_edge)
{
    if (over)
    {
        if (a_edge)
            game2048_init();

        return;
    }

    int dir = -1;

    if (left) dir = 0;
    else if (right) dir = 1;
    else if (up) dir = 2;
    else if (down) dir = 3;

    if (dir == -1)
        return;

    bool changed = move_board(dir);

    if (changed)
    {
        add_tile();

        if (!merged_this_move)
            audio_play_sfx(SFX_TILE_MOVE);
    }

    over = !has_moves();
}

// =====================================================
// DRAW TILE NUMBER
// =====================================================

static void draw_tile_number(int x, int y, int value)
{
    char text[12];
    snprintf(text, sizeof(text), "%d", value);

    int digits = 1;
    int temp = value;

    if (temp < 0) temp = -temp;
    do
    {
        digits++;
        temp /= 10;
    } while (temp > 0);
    digits--;

    // The tile interior is 44 px wide. Font size 1 uses
    // approximately 6 px per character, so even 6 digits fit.
    int text_width = digits * 6;
    int tx = x + (44 - text_width) / 2;
    int ty = y + 18;

    draw_text(tx, ty, text, tile_text_color(value), 1);
}

// =====================================================
// DRAW GAME
// =====================================================

void game2048_draw()
{
    clear_screen(C_BLACK);

    draw_text(12, 8, "2048", C_CYAN, 2);
    rect(5, 30, SCREEN_W - 10, 2, C_CYAN);

    // LEFT: 4x4 board.
    const int x0 = 10;
    const int y0 = 42;
    const int cell = 48;
    const int tile_size = 44;

    for (int y = 0; y < 4; y++)
    {
        for (int x = 0; x < 4; x++)
        {
            int px = x0 + x * cell;
            int py = y0 + y * cell;
            int value = board[y][x];

            rect(px, py, tile_size, tile_size, tile_color(value));
            border_rect(px, py, tile_size, tile_size, 0x7BEF);

            if (value != 0)
                draw_tile_number(px, py, value);
        }
    }

    // RIGHT: score, tile count and controls. Level display removed.
    border_rect(207, 38, 108, 190, C_CYAN);

    draw_text(216, 52, "SCORE", C_WHITE, 1);
    draw_number(216, 69, score, C_YELLOW, 1);

    draw_text(216, 105, "TILES", C_WHITE, 1);
    int filled = 0;

    for (int y = 0; y < 4; y++)
        for (int x = 0; x < 4; x++)
            if (board[y][x] != 0)
                filled++;

    draw_number(216, 122, filled, C_YELLOW, 1);

    draw_text(216, 163, "ARROWS", C_CYAN, 1);
    draw_text(216, 178, "MOVE", C_WHITE, 1);
    draw_text(216, 198, "A RESTART", C_WHITE, 1);

    if (over)
    {
        border_rect(18, 112, 180, 48, C_RED);
        draw_text(35, 121, "NO MOVES LEFT", C_RED, 1);
        draw_text(35, 140, "A TO RESTART", C_WHITE, 1);
    }

    render_display();
}

// =====================================================
// GAME STATUS
// =====================================================

bool game2048_is_over()
{
    return over;
}

int game2048_score()
{
    return score;
}
