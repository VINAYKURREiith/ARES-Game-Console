#pragma once
#include <stdint.h>
void pong_init();
void pong_update(bool left, bool right);
void pong_draw();
bool pong_is_over();
int pong_get_player_score();
uint32_t pong_get_last_frame();
void pong_set_last_frame(uint32_t value);
void pong_frame(bool up, bool down, bool left, bool right, bool a_edge);

bool pong_is_won();
