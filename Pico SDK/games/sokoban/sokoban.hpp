#pragma once
void sokoban_init();
void sokoban_update(bool up,bool down,bool left,bool right,bool a_edge);
void sokoban_draw();
bool sokoban_is_over();
bool sokoban_is_won();
int sokoban_score();

void sokoban_start_level(int level);
