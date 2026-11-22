#pragma once
#include <stdint.h>
enum AresSfx : uint8_t { SFX_UI_MOVE, SFX_UI_CONFIRM, SFX_PADDLE_HIT, SFX_WALL_HIT, SFX_BRICK_BREAK, SFX_TILE_MOVE, SFX_TILE_MERGE, SFX_TILE_BIG_MERGE, SFX_LASER, SFX_EXPLOSION, SFX_LINE_CLEAR, SFX_PICKUP, SFX_BOX_PUSH, SFX_PUZZLE_SOLVED, SFX_LIFE_LOST, SFX_GAME_OVER, SFX_VICTORY, SFX_COUNT };
enum AresMusicTrack : uint8_t { MUSIC_MENU, MUSIC_PONG, MUSIC_2048, MUSIC_BREAKOUT, MUSIC_INVADERS, MUSIC_TETRIS, MUSIC_SNAKE, MUSIC_RACING, MUSIC_SOKOBAN, MUSIC_TRACK_COUNT };
// Non-blocking synthesized tone API. Current backend drives the GP13 diagnostic buzzer.
void audio_init(); void audio_update(); void audio_enable(bool enabled); bool audio_is_enabled();
void audio_set_sfx_enabled(bool enabled); bool audio_sfx_enabled();
void audio_set_music_enabled(bool enabled); bool audio_music_enabled();
void audio_set_volume(uint8_t volume); uint8_t audio_get_volume(); void audio_play_sfx(AresSfx effect); void audio_play_merge(uint32_t tile_value); void audio_set_music(AresMusicTrack track); void audio_pause_music(bool pause);
