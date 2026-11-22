#pragma once
void breakout_init();
void breakout_update(bool up,bool down,bool left,bool right,bool a_edge);
void breakout_draw();
bool breakout_is_over();
int breakout_score();

bool breakout_is_won();
