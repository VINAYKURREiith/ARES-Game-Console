#pragma once
void game2048_init();
void game2048_update(bool up, bool down, bool left, bool right, bool a_edge);
void game2048_draw();
bool game2048_is_over();
int game2048_score();
