#pragma once
void racing_init();
void racing_update(bool up, bool down, bool left, bool right, bool a_edge);
void racing_draw();
bool racing_is_over();
int racing_score();
