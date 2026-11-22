#pragma once
#include <stdint.h>
#include "pico/stdlib.h"

#define MAX_SCREEN_W 320
#define MAX_SCREEN_H 320
extern int SCREEN_W;
extern int SCREEN_H;
#define C_BLACK  0x0000
#define C_WHITE  0xFFFF
#define C_CYAN   0x07FF
#define C_GREEN  0x07E0
#define C_RED    0xF800
#define C_BLUE   0x001F
#define C_YELLOW 0xFFE0
#define C_PURPLE 0x781F
#define C_DARK   0x1082
#define C_ORANGE 0xFD20

extern const uint8_t buttons[8];
extern uint16_t framebuffer[MAX_SCREEN_W * MAX_SCREEN_H];
extern int game_level; // Retained as a fixed baseline for legacy game modules.
extern int console_difficulty; // 0 = Easy, 1 = Medium, 2 = Hard.

void display_init();
void render_display();
void clear_screen(uint16_t color);
void draw_arcade_background();
void pixel(int x, int y, uint16_t color);
void draw_bitmap_rgb565(int x, int y, int w, int h, const uint16_t *pixels);
void rect(int x, int y, int w, int h, uint16_t color);
void border_rect(int x, int y, int w, int h, uint16_t color);
void draw_text(int x, int y, const char *text, uint16_t color, int scale);
void draw_number(int x, int y, int value, uint16_t color, int scale);
void buzzer_tone(uint frequency, uint duration_ms);
void init_buzzer();
bool pressed(int index);
void draw_boot_screen();
void draw_menu(int selected, bool show_coming_soon);
void draw_pause_screen(int current_score, int selected = 0);
extern bool console_sound_enabled;
extern uint8_t console_volume;
extern uint8_t console_brightness;
void set_console_brightness(uint8_t brightness);
void load_console_settings();
void save_console_settings();
void draw_settings_screen(int selected, bool sfx_enabled, bool music_enabled);
void draw_button_test_screen(int pressed_mask);
void draw_display_test_screen(int frame);
void draw_audio_test_screen(bool sound_enabled);

constexpr int MENU_COUNT = 8;
constexpr int GAMES_PER_PAGE = 4;
// Shared game labels defined once in core/common.cpp and used by main.cpp.
extern const char *menu_items[MENU_COUNT];
