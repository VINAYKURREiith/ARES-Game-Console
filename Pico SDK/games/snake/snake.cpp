#include "snake.hpp"
#include "../../core/common.hpp"
#include "../../audio/audio.hpp"
#include <stdlib.h>

struct Point {
    int x, y;
};

// ---------------- 320x240 SNAKE SETTINGS ----------------
// 30 columns x 20 rows = 300 x 200 pixels of playable area.
// The 20-pixel top strip is reserved for the title and score.
static constexpr int CELL = 10;
static constexpr int GRID_X = 10;
static constexpr int GRID_Y = 30;
static constexpr int GRID_COLS = 30;
static constexpr int GRID_ROWS = 20;
static constexpr int MAX_SNAKE = GRID_COLS * GRID_ROWS;

static Point snake[MAX_SNAKE];
static int snake_length;
static Point food;
static int direction; // 0 right, 1 down, 2 left, 3 up
static int score;
static bool game_over;
static bool game_won;

static uint32_t last_move;

// ---------------- HELPERS ----------------
static bool same_point(Point a, Point b)
{
    return a.x == b.x && a.y == b.y;
}

static bool cell_is_occupied(int x, int y)
{
    Point p = {x, y};

    for (int i = 0; i < snake_length; i++)
    {
        if (same_point(p, snake[i]))
            return true;
    }

    return false;
}

// Select a free cell without getting stuck in an infinite loop
// when the snake fills the entire board.
static bool spawn_food()
{
    int free_cells = MAX_SNAKE - snake_length;

    if (free_cells <= 0)
        return false;

    // Random probing, followed by a guaranteed linear search.
    for (int attempt = 0; attempt < 100; attempt++)
    {
        int x = rand() % GRID_COLS;
        int y = rand() % GRID_ROWS;

        if (!cell_is_occupied(x, y))
        {
            food.x = x;
            food.y = y;
            return true;
        }
    }

    for (int y = 0; y < GRID_ROWS; y++)
    {
        for (int x = 0; x < GRID_COLS; x++)
        {
            if (!cell_is_occupied(x, y))
            {
                food.x = x;
                food.y = y;
                return true;
            }
        }
    }

    return false;
}

// ---------------- INITIALIZE ----------------
void snake_init()
{
    snake_length = 4;

    // Start near the centre, facing right.
    snake[0] = {15, 10};
    snake[1] = {14, 10};
    snake[2] = {13, 10};
    snake[3] = {12, 10};

    direction = 0;
    score = 0;
    game_over = false;
    game_won = false;

    spawn_food();

    last_move = to_ms_since_boot(get_absolute_time());

    audio_play_sfx(SFX_UI_CONFIRM);
}

// ---------------- DRAW FOOD ----------------
static void draw_food()
{
    int fx = GRID_X + food.x * CELL;
    int fy = GRID_Y + food.y * CELL;

    // Bright food tile with a small highlight.
    rect(fx + 1, fy + 1, CELL - 2, CELL - 2, C_RED);
    rect(fx + 3, fy + 2, 3, 2, C_ORANGE);
}

// ---------------- DRAW SNAKE ----------------
static void draw_snake()
{
    for (int i = snake_length - 1; i >= 0; i--)
    {
        int sx = GRID_X + snake[i].x * CELL;
        int sy = GRID_Y + snake[i].y * CELL;

        if (i == 0)
        {
            // Head.
            rect(sx + 1, sy + 1, CELL - 2, CELL - 2, C_CYAN);

            // Eyes are positioned according to travel direction.
            if (direction == 0) // right
            {
                rect(sx + 6, sy + 2, 2, 2, C_BLACK);
                rect(sx + 6, sy + 6, 2, 2, C_BLACK);
            }
            else if (direction == 1) // down
            {
                rect(sx + 2, sy + 6, 2, 2, C_BLACK);
                rect(sx + 6, sy + 6, 2, 2, C_BLACK);
            }
            else if (direction == 2) // left
            {
                rect(sx + 2, sy + 2, 2, 2, C_BLACK);
                rect(sx + 2, sy + 6, 2, 2, C_BLACK);
            }
            else // up
            {
                rect(sx + 2, sy + 2, 2, 2, C_BLACK);
                rect(sx + 6, sy + 2, 2, 2, C_BLACK);
            }
        }
        else
        {
            // Alternate two green shades for a segmented body.
            uint16_t body_color = (i & 1) ? C_GREEN : 0x05E0;
            rect(sx + 1, sy + 1, CELL - 2, CELL - 2, body_color);
        }
    }
}

// ---------------- DRAW GAME ----------------
void snake_draw()
{
    clear_screen(C_BLACK);

    // Compact header keeps almost the entire screen for gameplay.
    draw_text(10, 5, "SNAKE", C_CYAN, 2);
    draw_text(190, 7, "SCORE", C_WHITE, 1);
    draw_number(230, 7, score, C_YELLOW, 1);

    // Maximum practical playfield: 300 x 200 pixels.
    rect(GRID_X - 2, GRID_Y - 2,
         GRID_COLS * CELL + 4, GRID_ROWS * CELL + 4, C_DARK);

    border_rect(GRID_X - 2, GRID_Y - 2,
                GRID_COLS * CELL + 4, GRID_ROWS * CELL + 4, C_CYAN);

    rect(GRID_X, GRID_Y,
         GRID_COLS * CELL, GRID_ROWS * CELL, C_BLACK);

    // Subtle grid lines.
    for (int x = 1; x < GRID_COLS; x++)
        rect(GRID_X + x * CELL, GRID_Y, 1,
             GRID_ROWS * CELL, 0x0841);

    for (int y = 1; y < GRID_ROWS; y++)
        rect(GRID_X, GRID_Y + y * CELL,
             GRID_COLS * CELL, 1, 0x0841);

    if (!game_won)
        draw_food();

    draw_snake();

    if (game_over)
    {
        // Compact overlay contained entirely inside the playfield.
        rect(65, 94, 190, 58, C_DARK);
        border_rect(65, 94, 190, 58, game_won ? C_GREEN : C_RED);

        if (game_won)
        {
            draw_text(105, 105, "YOU WIN!", C_GREEN, 2);
        }
        else
        {
            draw_text(105, 105, "GAME OVER", C_RED, 2);
        }

        draw_text(105, 130, "PRESS A", C_YELLOW, 1);
    }

    render_display();
}

// ---------------- GAME MOVEMENT ----------------
static void update_game()
{
    if (game_over)
        return;

    Point next = snake[0];

    if (direction == 0) next.x++;
    if (direction == 1) next.y++;
    if (direction == 2) next.x--;
    if (direction == 3) next.y--;

    // WRAP-AROUND WALLS:
    // Leaving one edge makes the snake enter from the opposite edge,
    // keeping the same row or column.
    if (next.x < 0)
        next.x = GRID_COLS - 1;
    else if (next.x >= GRID_COLS)
        next.x = 0;

    if (next.y < 0)
        next.y = GRID_ROWS - 1;
    else if (next.y >= GRID_ROWS)
        next.y = 0;

    bool eating = same_point(next, food);

    // If not eating, the tail moves away this turn, so entering its
    // current cell is allowed. If eating, the tail stays in place.
    int collision_length = eating ? snake_length : snake_length - 1;

    for (int i = 0; i < collision_length; i++)
    {
        if (same_point(next, snake[i]))
        {
            game_over = true;
            audio_play_sfx(SFX_GAME_OVER);
            return;
        }
    }

    if (eating)
    {
        if (snake_length < MAX_SNAKE)
            snake_length++;

        score += 1;
    }

    // Move body from tail toward head.
    for (int i = snake_length - 1; i > 0; i--)
        snake[i] = snake[i - 1];

    snake[0] = next;

    if (eating)
    {
        audio_play_sfx(SFX_PICKUP);

        if (!spawn_food())
        {
            game_over = true;
            game_won = true;
            audio_play_sfx(SFX_VICTORY);
        }
    }
}

// ---------------- INPUT ----------------
void snake_update(bool up, bool down, bool left, bool right)
{
    // Only accept a direction that is not directly opposite
    // to the current direction.
    if (up && direction != 1)
        direction = 3;
    else if (down && direction != 3)
        direction = 1;
    else if (left && direction != 0)
        direction = 2;
    else if (right && direction != 2)
        direction = 0;

    update_game();
}

// ---------------- STATUS / TIMING API ----------------
bool snake_is_over()
{
    return game_over;
}

int snake_score()
{
    return score;
}

uint32_t snake_last_move()
{
    return last_move;
}

void snake_set_last_move(uint32_t value)
{
    last_move = value;
}

void snake_frame(bool up, bool down, bool left, bool right, bool a_edge)
{
    // A restarts after game over.
    if (game_over)
    {
        if (a_edge)
            snake_init();

        return;
    }

    uint32_t now = to_ms_since_boot(get_absolute_time());

    uint32_t move_interval =
        (game_level == 0) ? 190 :
        (game_level == 2) ? 95 : 140;

    if (now - last_move >= move_interval)
    {
        snake_update(up, down, left, right);
        last_move = now;
    }
}
