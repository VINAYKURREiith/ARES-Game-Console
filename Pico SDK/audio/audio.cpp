#include "audio.hpp"
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/gpio.h"
#include <stdint.h>

namespace {
constexpr uint PIN_BUZZER = 13;

bool enabled = true;
bool sfx_enabled = true;
bool music_enabled = true;
bool paused = false;

uint8_t volume = 64;
AresMusicTrack track = MUSIC_MENU;
uint8_t note = 0;

uint32_t next_note = 0;
uint32_t tone_until = 0;

struct Note {
    uint16_t hz;
    uint16_t ms;
};

static const Note menu[] = {
    {523,130},{659,130},{784,180},{659,130},
    {880,220},{784,220},{659,180},{523,260}
};

static const Note pong[] = {
    {659,90},{784,90},{988,120},{784,90},
    {659,90},{523,160},{659,90},{784,140}
};

static const Note puzzle[] = {
    {392,180},{523,180},{659,220},{523,180},
    {440,260},{392,240},{330,180},{392,200}
};

static const Note action[] = {
    {784,90},{988,90},{1175,150},{988,90},
    {784,90},{659,180},{784,90},{988,150}
};

static const Note space[] = {
    {440,110},{554,110},{659,150},{880,110},
    {659,110},{554,180},{440,100},{659,180}
};

static const Note calm[] = {
    {330,200},{392,200},{494,260},{392,200},
    {349,260},{294,300},{330,180},{392,220}
};

static const Note racing[] = {
    {659,70},{784,70},{880,100},{784,70},
    {988,100},{880,130},{784,80},{988,150}
};

const Note* get_notes() {
    switch (track) {
        case MUSIC_PONG: return pong;
        case MUSIC_2048:
        case MUSIC_SOKOBAN: return puzzle;
        case MUSIC_BREAKOUT:
        case MUSIC_TETRIS: return action;
        case MUSIC_INVADERS: return space;
        case MUSIC_SNAKE: return calm;
        case MUSIC_RACING: return racing;
        default: return menu;
    }
}

void buzzer_stop() {
    pwm_set_enabled(pwm_gpio_to_slice_num(PIN_BUZZER), false);
    gpio_put(PIN_BUZZER, 0);
}

void buzzer_play(uint16_t hz) {
    if (!enabled || hz == 0) {
        buzzer_stop();
        return;
    }

    uint slice = pwm_gpio_to_slice_num(PIN_BUZZER);
    uint channel = pwm_gpio_to_channel(PIN_BUZZER);

    // 125 MHz / 125 = 1 MHz PWM counter
    pwm_set_clkdiv(slice, 125.0f);

    uint32_t wrap = 1000000u / hz;
    if (wrap < 2) wrap = 2;

    pwm_set_wrap(slice, wrap - 1);

    // Fixed 50% duty cycle; no volume adjustment.
    pwm_set_chan_level(slice, channel, wrap / 2);

    pwm_set_enabled(slice, true);
}

void play_effect(uint16_t hz, uint16_t ms) {
    if (!enabled || !sfx_enabled) return;

    buzzer_play(hz);
    tone_until = to_ms_since_boot(get_absolute_time()) + ms;
}
}

void audio_init() {
    gpio_set_function(PIN_BUZZER, GPIO_FUNC_PWM);

    enabled = true;
    sfx_enabled = true;
    music_enabled = true;
    paused = false;

    track = MUSIC_MENU;
    note = 0;
    next_note = 0;
    tone_until = 0;

    buzzer_stop();
}

void audio_enable(bool value) {
    enabled = value;
    tone_until = 0;
    next_note = 0;

    if (!enabled) {
        buzzer_stop();
    }
}

bool audio_is_enabled() {
    return enabled;
}

void audio_set_sfx_enabled(bool value) {
    sfx_enabled = value;
    if (!value) {
        tone_until = 0;
        buzzer_stop();
    }
}

bool audio_sfx_enabled() {
    return sfx_enabled;
}

void audio_set_music_enabled(bool value) {
    music_enabled = value;
    next_note = 0;

    if (!value) {
        buzzer_stop();
    }
}

bool audio_music_enabled() {
    return music_enabled;
}

void audio_set_volume(uint8_t value) {
    // Kept temporarily for compatibility with the old main.cpp.
    // The buzzer output remains fixed at 50% duty.
    volume = value;
}

uint8_t audio_get_volume() {
    return volume;
}

void audio_play_sfx(AresSfx s) {
    static const uint16_t hz[] = {
        650,880,1100,760,430,520,740,1050,1450,
        190,1200,980,500,1320,260,220,1560
    };

    static const uint16_t ms[] = {
        35,55,65,35,75,30,85,125,55,
        180,110,95,65,230,180,320,280
    };

    if ((uint)s < SFX_COUNT) {
        play_effect(hz[s], ms[s]);
    }
}

void audio_play_merge(uint32_t value) {
    audio_play_sfx(
        value >= 2048 ? SFX_VICTORY :
        value >= 128 ? SFX_TILE_BIG_MERGE :
                       SFX_TILE_MERGE
    );
}

void audio_set_music(AresMusicTrack value) {
    if (value >= MUSIC_TRACK_COUNT) value = MUSIC_MENU;

    if (track != value) {
        track = value;
        note = 0;
        next_note = 0;
    }
}

void audio_pause_music(bool value) {
    paused = value;
    next_note = 0;

    if (paused) {
        buzzer_stop();
    }
}

void audio_update() {
    if (!enabled) return;

    uint32_t now = to_ms_since_boot(get_absolute_time());

    // Let sound effects finish before continuing music.
    if (tone_until != 0) {
        if ((int32_t)(now - tone_until) < 0) return;

        tone_until = 0;
        buzzer_stop();
        next_note = now;
    }

    if (!music_enabled || paused) return;
    if ((int32_t)(now - next_note) < 0) return;

    Note n = get_notes()[note];

    buzzer_play(n.hz);

    next_note = now + n.ms;
    note = (note + 1) % 8;
}