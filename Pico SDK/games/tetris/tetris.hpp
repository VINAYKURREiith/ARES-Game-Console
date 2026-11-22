#pragma once
void tetris_init();
void tetris_update(bool up, bool down, bool left, bool right, bool a_edge);
void tetris_draw();
bool tetris_is_over();
int tetris_score();
