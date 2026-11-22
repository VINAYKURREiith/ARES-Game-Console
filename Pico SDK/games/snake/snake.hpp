#pragma once
#include <stdint.h>
void snake_init();
void snake_update(bool up, bool down, bool left, bool right);
void snake_draw();
bool snake_is_over();
int snake_score();
uint32_t snake_last_move();
void snake_set_last_move(uint32_t value);
void snake_frame(bool up, bool down, bool left, bool right, bool a_edge);
