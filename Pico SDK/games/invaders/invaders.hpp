#pragma once
void invaders_init();
void invaders_update(bool up, bool down, bool left, bool right, bool a_edge);
void invaders_draw();
bool invaders_is_over();
int invaders_score();

bool invaders_is_won();
