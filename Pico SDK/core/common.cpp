#include "common.hpp"
#include "../assets/reference_game_icons.hpp"
#include "../assets/ares_menu_background.hpp"
#include <stdio.h>
#include <string.h>
#include "hardware/spi.h"
#include "hardware/pwm.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "pico/bootrom.h"
#include "pico/stdlib.h"
#include <stdlib.h>
#include <math.h>
#include <initializer_list>

// ARES GAME CONSOLE — Pico 2 + 320x240 SPI TFT
// ARES Pocket Arcade — Pico 2, buzzer on GP13, backlight PWM on GP14

#define SPI_PORT spi0
#define PIN_RST 17
#define PIN_SCK 18
#define PIN_MOSI 19
#define PIN_MISO 20
#define PIN_CS 21
#define PIN_DC 22
#define BUZZER_PIN 13
#define TFT_BACKLIGHT_PIN 14

// Buttons: GP2 through GP9, active LOW
const uint8_t buttons[8] = {2, 3, 4, 5, 6, 7, 8, 9};

// Reserve the final 4 KiB flash sector for user settings in CMake.
static constexpr uint32_t SETTINGS_MAGIC = 0x41524553u;
static constexpr uint32_t SETTINGS_OFFSET =
    4u * 1024u * 1024u - FLASH_SECTOR_SIZE;

struct StoredSettings {
    uint32_t magic;
    uint32_t version;
    uint32_t sound_enabled;
    uint32_t volume;
    uint32_t brightness;
    uint32_t checksum;
};

int SCREEN_W = 320;
int SCREEN_H = 240;

bool console_sound_enabled = true;
uint8_t console_volume = 64;
uint8_t console_brightness = 100;

static bool backlight_pwm_ready = false;

uint16_t framebuffer[MAX_SCREEN_W * MAX_SCREEN_H];

static uint32_t settings_checksum(const StoredSettings &s) {
    return s.magic ^ s.version ^ s.sound_enabled ^
           s.volume ^ s.brightness ^ 0xA53C91E7u;
}

int game_level = 1;
int console_difficulty = 0;

const char *menu_items[MENU_COUNT] = {
    "PONG", "BREAKOUT", "2048", "RACING",
    "TETRIS", "INVADERS", "SNAKE", "SOKOBAN"
};

static constexpr uint32_t TFT_SPI_INIT_HZ = 24000000;

// --------------------------------------------------
// DISPLAY COMMUNICATION
// --------------------------------------------------

void write_cmd(uint8_t cmd) {
    gpio_put(PIN_DC, 0);
    gpio_put(PIN_CS, 0);

    spi_write_blocking(SPI_PORT, &cmd, 1);

    while (spi_is_busy(SPI_PORT))
        tight_loop_contents();

    gpio_put(PIN_CS, 1);
}

void write_data(const uint8_t *data, size_t len) {
    if (!data || len == 0) return;

    gpio_put(PIN_DC, 1);
    gpio_put(PIN_CS, 0);

    spi_write_blocking(SPI_PORT, data, len);

    while (spi_is_busy(SPI_PORT))
        tight_loop_contents();

    gpio_put(PIN_CS, 1);
}

void write_byte(uint8_t value) {
    write_data(&value, 1);
}

static void write_cmd_data(
    uint8_t cmd,
    const uint8_t *data,
    size_t len
) {
    gpio_put(PIN_CS, 0);
    gpio_put(PIN_DC, 0);

    spi_write_blocking(SPI_PORT, &cmd, 1);

    if (len && data) {
        gpio_put(PIN_DC, 1);
        spi_write_blocking(SPI_PORT, data, len);
    }

    while (spi_is_busy(SPI_PORT))
        tight_loop_contents();

    gpio_put(PIN_CS, 1);
}

static void write_cmd_bytes(
    uint8_t cmd,
    std::initializer_list<uint8_t> bytes
) {
    uint8_t data[16];
    size_t n = 0;

    for (uint8_t b : bytes) {
        if (n < sizeof(data))
            data[n++] = b;
    }

    write_cmd_data(cmd, data, n);
}

// --------------------------------------------------
// DISPLAY INITIALIZATION
// --------------------------------------------------

void display_init() {
    spi_init(SPI_PORT, TFT_SPI_INIT_HZ);

    spi_set_format(
        SPI_PORT,
        8,
        SPI_CPOL_0,
        SPI_CPHA_0,
        SPI_MSB_FIRST
    );

    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    gpio_init(PIN_CS);
    gpio_set_dir(PIN_CS, GPIO_OUT);
    gpio_put(PIN_CS, 1);

    gpio_init(PIN_DC);
    gpio_set_dir(PIN_DC, GPIO_OUT);
    gpio_put(PIN_DC, 0);

    gpio_init(PIN_RST);
    gpio_set_dir(PIN_RST, GPIO_OUT);
    gpio_put(PIN_RST, 1);

    sleep_ms(10);
    gpio_put(PIN_RST, 0);
    sleep_ms(10);
    gpio_put(PIN_RST, 1);
    sleep_ms(120);

    // ST7789 initialization sequence
    write_cmd(0x01);
    sleep_ms(120);

    write_cmd(0x11);
    sleep_ms(120);

    write_cmd_bytes(0x3A, {0x55});
    write_cmd_bytes(0x36, {0x60});

    write_cmd_bytes(0xB2, {
        0x0C, 0x0C, 0x00, 0x33, 0x33
    });

    write_cmd_bytes(0xB7, {0x35});
    write_cmd_bytes(0xBB, {0x19});
    write_cmd_bytes(0xC0, {0x2C});
    write_cmd_bytes(0xC2, {0x01});
    write_cmd_bytes(0xC3, {0x12});
    write_cmd_bytes(0xC4, {0x20});
    write_cmd_bytes(0xC6, {0x0F});

    write_cmd_bytes(0xD0, {0xA4, 0xA1});

    write_cmd_bytes(0xE0, {
        0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F,
        0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23
    });

    write_cmd_bytes(0xE1, {
        0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F,
        0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23
    });

    write_cmd(0x20);
    write_cmd(0x13);

    sleep_ms(10);

    // Backlight PWM
    gpio_set_function(TFT_BACKLIGHT_PIN, GPIO_FUNC_PWM);

    uint slice = pwm_gpio_to_slice_num(TFT_BACKLIGHT_PIN);

    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_wrap(&cfg, 999);

    pwm_init(slice, &cfg, true);

    backlight_pwm_ready = true;

    set_console_brightness(console_brightness);

    clear_screen(C_BLACK);
    render_display();

    write_cmd(0x29);
    sleep_ms(100);
}

void set_console_brightness(uint8_t brightness) {
    if (brightness > 100)
        brightness = 100;

    console_brightness = brightness;

    if (backlight_pwm_ready) {
        uint slice = pwm_gpio_to_slice_num(TFT_BACKLIGHT_PIN);
        uint channel = pwm_gpio_to_channel(TFT_BACKLIGHT_PIN);

        pwm_set_chan_level(
            slice,
            channel,
            (uint16_t)(
                (uint32_t)brightness * 999u / 100u
            )
        );
    }
}

// --------------------------------------------------
// DISPLAY WINDOW AND RENDERING
// --------------------------------------------------

void set_window(int x0, int y0, int x1, int y1) {
    write_cmd(0x2A);

    uint8_t col[] = {
        (uint8_t)(x0 >> 8),
        (uint8_t)x0,
        (uint8_t)(x1 >> 8),
        (uint8_t)x1
    };

    write_data(col, 4);

    write_cmd(0x2B);

    uint8_t row[] = {
        (uint8_t)(y0 >> 8),
        (uint8_t)y0,
        (uint8_t)(y1 >> 8),
        (uint8_t)y1
    };

    write_data(row, 4);

    write_cmd(0x2C);
}

void render_display() {
    set_window(0, 0, SCREEN_W - 1, SCREEN_H - 1);

    uint8_t buffer[1024];

    const int total = SCREEN_W * SCREEN_H;
    int index = 0;

    while (index < total) {
        int count = total - index;

        if (count > 512)
            count = 512;

        for (int i = 0; i < count; i++) {
            uint16_t pixel_value = framebuffer[index + i];

            buffer[2 * i] = pixel_value >> 8;
            buffer[2 * i + 1] = pixel_value & 0xFF;
        }

        write_data(buffer, count * 2);

        index += count;
    }
}

void clear_screen(uint16_t color) {
    for (int i = 0; i < SCREEN_W * SCREEN_H; i++)
        framebuffer[i] = color;
}

void draw_arcade_background() {
    if (SCREEN_W == 320 && SCREEN_H == 240) {
        draw_bitmap_rgb565(
            0, 0, 320, 240,
            ARES_MENU_BACKGROUND_RGB565
        );
    } else {
        clear_screen(C_BLACK);
    }
}

void pixel(int x, int y, uint16_t color) {
    if (x >= 0 && x < SCREEN_W &&
        y >= 0 && y < SCREEN_H) {
        framebuffer[y * SCREEN_W + x] = color;
    }
}

void draw_bitmap_rgb565(
    int x,
    int y,
    int w,
    int h,
    const uint16_t *pixels
) {
    if (!pixels || w <= 0 || h <= 0)
        return;

    for (int yy = 0; yy < h; ++yy) {
        for (int xx = 0; xx < w; ++xx) {
            int dx = x + xx;
            int dy = y + yy;

            if (dx >= 0 && dx < SCREEN_W &&
                dy >= 0 && dy < SCREEN_H) {
                framebuffer[dy * SCREEN_W + dx] =
                    pixels[yy * w + xx];
            }
        }
    }
}

void rect(int x, int y, int w, int h, uint16_t color) {
    for (int yy = y; yy < y + h; yy++) {
        for (int xx = x; xx < x + w; xx++) {
            pixel(xx, yy, color);
        }
    }
}

void border_rect(
    int x,
    int y,
    int w,
    int h,
    uint16_t color
) {
    rect(x, y, w, 2, color);
    rect(x, y + h - 2, w, 2, color);
    rect(x, y, 2, h, color);
    rect(x + w - 2, y, 2, h, color);
}

// --------------------------------------------------
// FONT AND TEXT
// --------------------------------------------------

const uint8_t *glyph(char c) {
    static const uint8_t blank[5] = {
        0, 0, 0, 0, 0
    };

    static const uint8_t font[36][5] = {
        {7,5,5,5,7}, {2,6,2,2,7}, {7,1,7,4,7},
        {7,1,7,1,7}, {5,5,7,1,1}, {7,4,7,1,7},
        {7,4,7,5,7}, {7,1,1,1,1}, {7,5,7,5,7},
        {7,5,7,1,7}, {2,5,7,5,5}, {6,5,6,5,6},
        {3,4,4,4,3}, {6,5,5,5,6}, {7,4,6,4,7},
        {7,4,6,4,4}, {3,4,5,5,3}, {5,5,7,5,5},
        {7,2,2,2,7}, {1,1,1,5,2}, {5,5,6,5,5},
        {4,4,4,4,7}, {5,7,7,5,5}, {5,7,7,7,5},
        {2,5,5,5,2}, {6,5,6,4,4}, {2,5,5,7,3},
        {6,5,6,5,5}, {3,4,2,1,6}, {7,2,2,2,2},
        {5,5,5,5,7}, {5,5,5,5,2}, {5,5,7,7,5},
        {5,5,2,5,5}, {5,5,2,2,2}, {7,1,2,4,7}
    };

    if (c >= '0' && c <= '9')
        return font[c - '0'];

    if (c >= 'A' && c <= 'Z')
        return font[10 + c - 'A'];

    return blank;
}

void draw_char(
    int x,
    int y,
    char c,
    uint16_t color,
    int scale
) {
    const uint8_t *g = glyph(c);

    for (int row = 0; row < 5; row++) {
        for (int col = 0; col < 3; col++) {
            if (g[row] & (1 << (2 - col))) {
                rect(
                    x + col * scale,
                    y + row * scale,
                    scale,
                    scale,
                    color
                );
            }
        }
    }
}

void draw_text(
    int x,
    int y,
    const char *text,
    uint16_t color,
    int scale
) {
    while (*text) {
        draw_char(x, y, *text++, color, scale);
        x += 4 * scale;
    }
}

void draw_number(
    int x,
    int y,
    int value,
    uint16_t color,
    int scale
) {
    char s[12];

    snprintf(s, sizeof(s), "%d", value);

    draw_text(x, y, s, color, scale);
}

// --------------------------------------------------
// BUZZER
// --------------------------------------------------

void buzzer_tone(uint frequency, uint duration_ms) {
    if (frequency == 0) {
        gpio_put(BUZZER_PIN, 0);
        sleep_ms(duration_ms);
        return;
    }

    uint slice = pwm_gpio_to_slice_num(BUZZER_PIN);
    uint chan = pwm_gpio_to_channel(BUZZER_PIN);

    pwm_set_clkdiv(slice, 125.0f);

    uint wrap = 1000000 / frequency - 1;

    pwm_set_wrap(slice, wrap);

    pwm_set_chan_level(
        slice,
        chan,
        (wrap + 1) / 2
    );

    pwm_set_enabled(slice, true);

    sleep_ms(duration_ms);

    pwm_set_enabled(slice, false);
    gpio_put(BUZZER_PIN, 0);
}

void init_buzzer() {
    gpio_set_function(BUZZER_PIN, GPIO_FUNC_PWM);

    uint slice = pwm_gpio_to_slice_num(BUZZER_PIN);

    pwm_set_enabled(slice, false);
}

// --------------------------------------------------
// SETTINGS SAVE AND LOAD
// --------------------------------------------------

void load_console_settings() {
    const uint8_t *flash =
        (const uint8_t *)(XIP_BASE + SETTINGS_OFFSET);

    StoredSettings stored{};

    memcpy(&stored, flash, sizeof(stored));

    if (stored.magic == SETTINGS_MAGIC &&
        stored.version == 3 &&
        stored.checksum == settings_checksum(stored) &&
        stored.sound_enabled <= 1 &&
        stored.volume <= 100 &&
        stored.brightness <= 100) {

        console_sound_enabled =
            stored.sound_enabled != 0;

        console_volume = (uint8_t)stored.volume;

        console_brightness =
            (uint8_t)stored.brightness;

    } else {
        console_sound_enabled = true;
        console_volume = 64;
        console_brightness = 100;
    }

    SCREEN_W = 320;
    SCREEN_H = 240;

    set_console_brightness(console_brightness);
}

void save_console_settings() {
    StoredSettings stored{
        SETTINGS_MAGIC,
        3,
        console_sound_enabled ? 1u : 0u,
        console_volume,
        console_brightness,
        0
    };

    stored.checksum = settings_checksum(stored);

    uint8_t page[FLASH_PAGE_SIZE];

    memset(page, 0xFF, sizeof(page));

    memcpy(page, &stored, sizeof(stored));

    uint32_t ints = save_and_disable_interrupts();

    flash_range_erase(
        SETTINGS_OFFSET,
        FLASH_SECTOR_SIZE
    );

    flash_range_program(
        SETTINGS_OFFSET,
        page,
        FLASH_PAGE_SIZE
    );

    restore_interrupts(ints);
}

// --------------------------------------------------
// SETTINGS SCREEN
// --------------------------------------------------

static void draw_button_glyph(
    int x,
    int y,
    const char *label,
    uint16_t color
) {
    border_rect(x, y, 28, 22, color);

    draw_text(x + 8, y + 7, label, color, 1);
}

void draw_settings_screen(
    int selected,
    bool sfx_enabled,
    bool music_enabled
) {
    draw_arcade_background();

    draw_text(12, 7, "ARES", C_CYAN, 3);
    draw_text(100, 16, "SETTINGS", C_WHITE, 2);

    rect(12, 40, SCREEN_W - 24, 2, C_PURPLE);

    // VOLUME option removed. Remaining options preserved.
    const char *items[7] = {
        "BUZZER SFX",
        "SPEAKER MUSIC",
        "BRIGHTNESS",
        "BUTTON TEST",
        "DISPLAY TEST",
        "AUDIO TEST",
        "BACK"
    };

    const int y0 = 43;
    const int row_h = 22;

    for (int i = 0; i < 7; i++) {
        int y = y0 + i * row_h;

        if (i == selected) {
            rect(
                10,
                y - 1,
                SCREEN_W - 20,
                row_h - 1,
                0x1084
            );

            border_rect(
                10,
                y - 1,
                SCREEN_W - 20,
                row_h - 1,
                C_CYAN
            );
        }

        draw_text(
            18,
            y + 5,
            items[i],
            i == selected ? C_YELLOW : C_WHITE,
            1
        );

        if (i == 0) {
            draw_text(
                SCREEN_W - 66,
                y + 5,
                sfx_enabled ? "ON" : "OFF",
                sfx_enabled ? C_GREEN : C_RED,
                1
            );
        }

        if (i == 1) {
            draw_text(
                SCREEN_W - 66,
                y + 5,
                music_enabled ? "ON" : "OFF",
                music_enabled ? C_GREEN : C_RED,
                1
            );
        }

        if (i == 2) {
            rect(
                SCREEN_W - 88,
                y + 7,
                58,
                6,
                C_DARK
            );

            rect(
                SCREEN_W - 88,
                y + 7,
                (int)(58 * console_brightness / 100),
                6,
                C_YELLOW
            );
        }
    }

    draw_text(
        14,
        SCREEN_H - 12,
        "UP/DN MOVE  LEFT/RIGHT ADJUST  A SELECT  B BACK",
        C_CYAN,
        1
    );

    render_display();
}

// --------------------------------------------------
// BUTTON TEST
// --------------------------------------------------

void draw_button_test_screen(int pressed_mask) {
    draw_arcade_background();

    draw_text(12, 10, "BUTTON TEST", C_CYAN, 2);

    const char *labels[8] = {
        "UP", "DOWN", "LEFT", "RIGHT",
        "A", "B", "START", "MENU"
    };

    for (int i = 0; i < 8; i++) {
        int x = 18 + (i % 4) * 74;
        int y = 65 + (i / 4) * 64;

        uint16_t c =
            (pressed_mask & (1 << i)) ? C_GREEN : C_DARK;

        border_rect(x, y, 58, 38, c);

        draw_text(
            x + 8,
            y + 14,
            labels[i],
            (pressed_mask & (1 << i)) ? C_GREEN : C_WHITE,
            1
        );
    }

    draw_text(
        16,
        SCREEN_H - 18,
        "B BACK",
        C_CYAN,
        1
    );

    render_display();
}

// --------------------------------------------------
// DISPLAY TEST
// --------------------------------------------------

void draw_display_test_screen(int frame) {
    clear_screen(
        frame % 3 == 0 ? C_BLACK :
        (frame % 3 == 1 ? 0x2104 : 0xFFFF)
    );

    border_rect(
        3,
        3,
        SCREEN_W - 6,
        SCREEN_H - 6,
        frame % 3 == 0 ? C_CYAN :
        (frame % 3 == 1 ? C_RED : C_BLUE)
    );

    draw_text(
        20,
        18,
        "DISPLAY TEST",
        frame % 3 == 2 ? C_BLACK : C_WHITE,
        2
    );

    draw_text(
        20,
        60,
        "320 X 240 LANDSCAPE",
        frame % 3 == 2 ? C_BLACK : C_YELLOW,
        1
    );

    const uint16_t colors[8] = {
        C_RED, C_GREEN, C_BLUE, C_CYAN,
        C_YELLOW, C_PURPLE, C_ORANGE, C_WHITE
    };

    for (int i = 0; i < 8; i++) {
        rect(i * 37 + 12, 105, 24, 24, colors[i]);
    }

    draw_text(
        16,
        SCREEN_H - 18,
        "B BACK",
        frame % 3 == 2 ? C_BLACK : C_WHITE,
        1
    );

    render_display();
}

// --------------------------------------------------
// AUDIO TEST
// --------------------------------------------------

void draw_audio_test_screen(bool sound_enabled) {
    draw_arcade_background();

    draw_text(12, 10, "AUDIO TEST", C_CYAN, 3);

    rect(12, 43, SCREEN_W - 24, 2, C_PURPLE);

    draw_text(
        20, 64,
        "ARES BUZZER OUTPUT",
        C_WHITE, 1
    );

    draw_text(
        20, 88,
        "PWM OUTPUT: GP13",
        C_CYAN, 1
    );

    draw_text(
        20, 104,
        "MUSIC + GAME EFFECTS",
        C_CYAN, 1
    );

    draw_text(
        20, 132,
        sound_enabled ? "SOUND ENABLED" : "SOUND DISABLED",
        sound_enabled ? C_GREEN : C_RED,
        1
    );

    draw_text(
        20, 170,
        "A PLAY TEST TONE",
        C_YELLOW, 1
    );

    draw_text(
        20, 205,
        "B BACK TO SETTINGS",
        C_CYAN, 1
    );

    render_display();
}

// --------------------------------------------------
// GAME ICONS
// --------------------------------------------------

void draw_game_icon(int game, int x, int y) {
    switch (game) {
        case 0: {
            int ix = x + 12;
            int iy = y + 7;

            rect(ix, iy, 70, 29, 0x0861);
            border_rect(ix, iy, 70, 29, C_CYAN);

            for (int yy = iy + 4; yy < iy + 26; yy += 7)
                rect(ix + 34, yy, 2, 4, C_PURPLE);

            rect(ix + 7, iy + 7, 4, 14, C_CYAN);
            rect(ix + 59, iy + 9, 4, 12, C_BLUE);
            rect(ix + 43, iy + 10, 6, 6, C_YELLOW);
            rect(ix + 44, iy + 11, 4, 4, C_WHITE);
            break;
        }

        case 1:
            draw_bitmap_rgb565(
                x + 17, y + 8,
                ARES_ICON_W, ARES_ICON_H,
                icon_breakout
            );
            break;

        case 2: {
            int ix = x + 14;
            int iy = y + 4;
            int sz = 14;
            int gap = 3;

            const uint16_t tilec[4] = {
                0x4208, 0xDCA0, 0xFBE0, 0xF800
            };

            for (int yy = 0; yy < 2; yy++) {
                for (int xx = 0; xx < 2; xx++) {
                    int tx = ix + xx * (sz + gap);
                    int ty = iy + yy * (sz + gap);

                    uint16_t c = tilec[(xx + yy * 2) % 4];

                    rect(tx, ty, sz, sz, c);
                    border_rect(tx, ty, sz, sz, C_WHITE);
                }
            }

            draw_text(ix + 3, iy + 4, "2", C_WHITE, 1);
            draw_text(ix + 20, iy + 4, "0", C_WHITE, 1);
            draw_text(ix + 3, iy + 21, "4", C_WHITE, 1);
            draw_text(ix + 20, iy + 21, "8", C_WHITE, 1);
            break;
        }

        case 3:
            draw_bitmap_rgb565(
                x + 17, y + 8,
                ARES_ICON_W, ARES_ICON_H,
                icon_racing
            );
            break;

        case 4:
            draw_bitmap_rgb565(
                x + 17, y + 8,
                ARES_ICON_W, ARES_ICON_H,
                icon_tetris
            );
            break;

        case 5:
            draw_bitmap_rgb565(
                x + 17, y + 8,
                ARES_ICON_W, ARES_ICON_H,
                icon_invaders
            );
            break;

        case 6:
            rect(x + 10, y + 10, 10, 10, C_GREEN);
            rect(x + 20, y + 10, 10, 10, C_GREEN);
            rect(x + 30, y + 10, 10, 10, C_CYAN);
            rect(x + 30, y + 20, 10, 10, C_CYAN);
            rect(x + 40, y + 20, 10, 10, C_CYAN);
            rect(x + 58, y + 22, 7, 7, C_RED);
            break;

        case 7:
            draw_bitmap_rgb565(
                x + 17, y + 8,
                ARES_ICON_W, ARES_ICON_H,
                icon_sokoban
            );
            break;
    }
}

// --------------------------------------------------
// BOOT SCREEN
// --------------------------------------------------

void draw_boot_screen() {
    const int cx = SCREEN_W / 2;
    const int cy = SCREEN_H / 2 - 10;

    for (int f = 0; f < 10; f++) {
        clear_screen(C_BLACK);

        for (int i = 0; i < 12; i++) {
            int sx = (i * 47 + f * 9) % SCREEN_W;
            int sy = (i * 31 + f * 5) % SCREEN_H;

            rect(
                sx, sy,
                2 + (i % 2),
                2 + (i % 2),
                i % 3 ? C_CYAN : C_PURPLE
            );
        }

        int r = 16 + f * 5;

        border_rect(cx - r, cy - r / 2, r * 2, r, C_CYAN);

        if (f > 4)
            draw_text(
                cx - 42, cy - 19,
                "ARES",
                (f % 4 == 0) ? C_WHITE : C_CYAN,
                4
            );

        if (f > 11)
            draw_text(
                cx - 49, cy + 18,
                "POCKET ARCADE",
                C_YELLOW, 1
            );

        if (f > 17) {
            for (int k = 0; k < 4; k++) {
                int px = cx - 30 + k * 20;

                rect(
                    px, cy + 37, 9, 4,
                    (f + k) % 2 ? C_CYAN : C_PURPLE
                );
            }
        }

        render_display();
        sleep_ms(15);
    }

    for (int f = 0; f < 3; f++) {
        clear_screen(C_BLACK);

        int inset = (f % 2) * 3;

        border_rect(
            12 + inset,
            32 + inset,
            SCREEN_W - 24 - inset * 2,
            150 - inset * 2,
            f % 2 ? C_PURPLE : C_CYAN
        );

        draw_text(
            cx - 42, 58,
            "ARES",
            f % 2 ? C_WHITE : C_CYAN,
            4
        );

        draw_text(
            cx - 49, 98,
            "POCKET ARCADE",
            C_YELLOW, 1
        );

        draw_text(
            cx - 42, 133,
            "PRESS START",
            C_GREEN, 1
        );

        render_display();
        sleep_ms(35);
    }
}

// --------------------------------------------------
// MAIN GAME MENU
// --------------------------------------------------

void draw_menu(int selected, bool show_coming_soon) {
    draw_arcade_background();

    int page = selected / GAMES_PER_PAGE;

    draw_text(10, 8, "ARES", C_CYAN, 4);
    draw_text(12, 34, "ARCADE", C_WHITE, 2);

    char page_label[12];

    snprintf(
        page_label,
        sizeof(page_label),
        "PAGE %d/2",
        page + 1
    );

    draw_text(
        SCREEN_W - 67,
        16,
        page_label,
        C_YELLOW,
        1
    );

    rect(10, 53, SCREEN_W - 20, 2, C_PURPLE);

    draw_text(12, 61, "SELECT GAME", C_WHITE, 1);

    const int margin = 10;
    const int gap_x = 8;
    const int gap_y = 8;

    const int tile_w =
        (SCREEN_W - margin * 2 - gap_x) / 2;

    const int footer_h = 36;

    const int available_h =
        SCREEN_H - 82 - footer_h - gap_y;

    const int tile_h =
        (available_h - gap_y) / 2;

    const int tile_x[2] = {
        margin,
        margin + tile_w + gap_x
    };

    const int tile_y[2] = {
        78,
        78 + tile_h + gap_y
    };

    for (int local = 0; local < GAMES_PER_PAGE; local++) {
        int game = page * GAMES_PER_PAGE + local;

        int col = local % 2;
        int row = local / 2;

        int x = tile_x[col];
        int y = tile_y[row];

        bool is_selected = game == selected;

        border_rect(
            x, y,
            tile_w, tile_h,
            is_selected ? C_CYAN : C_DARK
        );

        int label_width =
            (int)strlen(menu_items[game]) * 4;

        if (SCREEN_H >= 300) {
            draw_game_icon(
                game,
                x + (tile_w - 82) / 2,
                y + 3
            );

            draw_text(
                x + (tile_w - label_width) / 2,
                y + tile_h - 20,
                menu_items[game],
                is_selected ? C_YELLOW : C_WHITE,
                1
            );

            draw_text(
                x + tile_w / 2 - 10,
                y + tile_h - 9,
                "READY",
                C_GREEN,
                1
            );
        } else {
            draw_game_icon(
                game,
                x + (tile_w - 82) / 2,
                y - 5
            );

            draw_text(
                x + (tile_w - label_width) / 2,
                y + 36,
                menu_items[game],
                is_selected ? C_YELLOW : C_WHITE,
                1
            );

            draw_text(
                x + tile_w / 2 - 10,
                y + 44,
                "READY",
                C_GREEN,
                1
            );
        }
    }

    rect(
        10,
        SCREEN_H - 38,
        SCREEN_W - 20,
        1,
        C_DARK
    );

    draw_text(
        12,
        SCREEN_H - 30,
        "ARROWS MOVE  A PLAY",
        C_WHITE,
        1
    );

    draw_button_glyph(
        12, SCREEN_H - 22,
        "A", C_GREEN
    );

    draw_text(
        48, SCREEN_H - 15,
        "PLAY", C_WHITE, 1
    );

    draw_button_glyph(
        92, SCREEN_H - 22,
        "X", C_PURPLE
    );

    draw_text(
        128, SCREEN_H - 15,
        "PAGE", C_CYAN, 1
    );

    draw_text(
        184, SCREEN_H - 15,
        "MENU SETTINGS",
        C_YELLOW, 1
    );

    if (show_coming_soon) {
        rect(
            25,
            SCREEN_H / 2 - 28,
            SCREEN_W - 50,
            56,
            C_DARK
        );

        border_rect(
            25,
            SCREEN_H / 2 - 28,
            SCREEN_W - 50,
            56,
            C_YELLOW
        );

        draw_text(
            38,
            SCREEN_H / 2 - 10,
            "COMING SOON",
            C_YELLOW,
            2
        );
    }

    render_display();
}

// --------------------------------------------------
// PAUSE SCREEN
// --------------------------------------------------

void draw_pause_screen(int current_score, int selected) {
    draw_arcade_background();

    draw_text(12, 8, "ARES", C_CYAN, 3);
    draw_text(112, 16, "PAUSED", C_YELLOW, 2);

    draw_text(18, 43, "SCORE", C_WHITE, 1);
    draw_number(66, 43, current_score, C_GREEN, 1);

    // Three pause-menu options; Stage Select removed.
    const char *items[3] = {
        "RESUME",
        "SETTINGS",
        "MAIN MENU"
    };

    for (int i = 0; i < 3; i++) {
        int y = 76 + i * 38;

        if (i == selected)
            rect(22, y, SCREEN_W - 44, 29, 0x1084);

        border_rect(
            22, y,
            SCREEN_W - 44,
            29,
            (i == selected) ? C_CYAN : C_BLUE
        );

        draw_text(
            34, y + 10,
            items[i],
            i == selected ? C_YELLOW : C_WHITE,
            1
        );
    }

    draw_button_glyph(
        12, SCREEN_H - 23,
        "A", C_GREEN
    );

    draw_text(
        48, SCREEN_H - 16,
        "CHOOSE", C_WHITE, 1
    );

    draw_button_glyph(
        SCREEN_W - 48,
        SCREEN_H - 23,
        "B", C_CYAN
    );

    render_display();
}

// --------------------------------------------------
// BUTTON INPUT
// --------------------------------------------------

// Button index:
// 0 Up, 1 Down, 2 Left, 3 Right,
// 4 A, 5 B, 6 Start, 7 Menu.

bool pressed(int index) {
    if (index < 0 || index >= 8)
        return false;

    return gpio_get(buttons[index]) == 0;
}