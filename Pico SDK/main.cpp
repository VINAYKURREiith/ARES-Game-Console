#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "core/common.hpp"
#include "games/pong/pong.hpp"
#include "games/snake/snake.hpp"
#include "games/invaders/invaders.hpp"
#include "games/game2048/game2048.hpp"
#include "games/tetris/tetris.hpp"
#include "games/racing/racing.hpp"
#include "games/breakout/breakout.hpp"
#include "games/sokoban/sokoban.hpp"
#include "audio/audio.hpp"

#define SPI_PORT spi0
#define PIN_SCK 18
#define PIN_MOSI 19
#define PIN_MISO 20

enum ConsoleState { STATE_MENU, STATE_HUB, STATE_DIFFICULTY, STATE_HIGHSCORES, STATE_GAME, STATE_PAUSE, STATE_SETTINGS, STATE_BUTTON_TEST, STATE_DISPLAY_TEST, STATE_AUDIO_TEST };
static int active_game=0, selected_game=0;
static int selected_difficulty=0; // 0 Easy, 1 Medium, 2 Hard
static int hub_selection=0, difficulty_selection=0, highscores_selection=0;
static bool settings_from_hub=false;
static bool settings_from_menu=false;
static ConsoleState state=STATE_MENU;
static bool resume_available=false;
static int settings_selection = 0;
static int pause_selection = 0;
static int diagnostic_frame = 0;
static int high_scores[8][3]={{0}};
static const char *difficulty_names[3]={"EASY","MEDIUM","HARD"};
static bool prev[8]={false,false,false,false,false,false,false,false};

static void menu_redraw() {
    draw_menu(selected_game,false);
}
static void game_init(int g) {
    switch(g) {
        case 0:pong_init();break; case 1:breakout_init();break;
        case 2:game2048_init();break; case 3:racing_init();break;
        case 4:tetris_init();break; case 5:invaders_init();break;
        case 6:snake_init();break; case 7:sokoban_start_level(1);break;
    }
}
static void game_update(int g,bool u,bool d,bool l,bool r,bool aedge) {
    switch(g) {
        case 0:pong_update(l,r);break; case 1:breakout_update(u,d,l,r,aedge);break;
        case 2:game2048_update(u,d,l,r,aedge);break; case 3:racing_update(u,d,l,r,aedge);break;
        case 4:tetris_update(u,d,l,r,aedge);break; case 5:invaders_update(u,d,l,r,aedge);break;
        case 6:snake_frame(u,d,l,r,aedge);break; case 7:sokoban_update(u,d,l,r,aedge);break;
    }
}
static void game_draw(int g) {
    switch(g) {
        case 0:pong_draw();break; case 1:breakout_draw();break;
        case 2:game2048_draw();break; case 3:racing_draw();break;
        case 4:tetris_draw();break; case 5:invaders_draw();break;
        case 6:snake_draw();break; case 7:sokoban_draw();break;
    }
}
static bool game_over(int g) {
    switch(g) {
        case 0:return pong_is_over();case 1:return breakout_is_over();
        case 2:return game2048_is_over();case 3:return racing_is_over();
        case 4:return tetris_is_over();case 5:return invaders_is_over();
        case 6:return snake_is_over();case 7:return sokoban_is_over();
    } return true;
}
static bool game_won(int g) {
    switch(g) {
        case 0:return pong_is_won();
        case 1:return breakout_is_won();
        case 5:return invaders_is_won();
        case 7:return sokoban_is_won();
        default:return false;
    }
}
static int game_score(int g) {
    switch(g) {
        case 0:return pong_get_player_score();case 1:return breakout_score();
        case 2:return game2048_score();case 3:return racing_score();
        case 4:return tetris_score();case 5:return invaders_score();
        case 6:return snake_score();case 7:return sokoban_score();
    } return 0;
}
static void enter_menu() { state=STATE_MENU; menu_redraw(); }
static void draw_game_hub() {
    draw_arcade_background(); draw_text(12,8,"ARES",C_CYAN,3); draw_text(100,16,menu_items[selected_game],C_WHITE,2);
    rect(12,40,SCREEN_W-24,2,C_PURPLE);
    const char *items[4]={"PLAY","RESUME","HIGH SCORES","SETTINGS"};
    for(int i=0;i<4;i++){int y=58+i*38; if(i==hub_selection){rect(24,y-4,SCREEN_W-48,30,0x1084);border_rect(24,y-4,SCREEN_W-48,30,C_CYAN);} draw_text(42,y+5,items[i],i==hub_selection?C_YELLOW:C_WHITE,2); if(i==1&&!resume_available)draw_text(SCREEN_W-94,y+7,"EMPTY",C_DARK,1);}
    draw_text(14,SCREEN_H-16,"A SELECT   B GAMES",C_CYAN,1); render_display();
}
static void draw_difficulty_screen() {
    draw_arcade_background(); draw_text(12,8,menu_items[selected_game],C_CYAN,2); draw_text(12,35,"SELECT DIFFICULTY",C_WHITE,2); rect(12,61,SCREEN_W-24,2,C_PURPLE);
    for(int i=0;i<3;i++){int y=78+i*42;uint16_t c=(i==0?C_GREEN:(i==1?C_YELLOW:C_RED));if(i==difficulty_selection){rect(24,y-5,SCREEN_W-48,32,0x1084);border_rect(24,y-5,SCREEN_W-48,32,C_CYAN);}draw_text(48,y+4,difficulty_names[i],i==difficulty_selection?c:C_WHITE,2);}
    draw_text(14,SCREEN_H-16,"UP/DN SELECT  A PLAY  B BACK",C_CYAN,1);render_display();
}
static void draw_highscores_screen() {
    draw_arcade_background();draw_text(12,8,"HIGH SCORES",C_CYAN,2);draw_text(12,34,menu_items[selected_game],C_WHITE,1);rect(12,50,SCREEN_W-24,2,C_PURPLE);
    for(int i=0;i<3;i++){int y=70+i*42;uint16_t c=(i==0?C_GREEN:(i==1?C_YELLOW:C_RED));draw_text(22,y,difficulty_names[i],c,2);draw_number(230,y,high_scores[selected_game][i],C_WHITE,2);}
    draw_text(14,SCREEN_H-16,"B BACK",C_CYAN,1);render_display();
}
static AresMusicTrack music_for_game(int g) {
    switch(g) { case 0:return MUSIC_PONG; case 1:return MUSIC_BREAKOUT; case 2:return MUSIC_2048; case 3:return MUSIC_RACING; case 4:return MUSIC_TETRIS; case 5:return MUSIC_INVADERS; case 6:return MUSIC_SNAKE; default:return MUSIC_SOKOBAN; }
}
static void leave_settings() {
    // Do not erase/program flash in the input loop: this was causing the
    // Settings exit (B button) to appear frozen on this hardware build.
    // Settings persistence will be re-enabled after flash-write handling is fixed.
    if(settings_from_menu) {
        settings_from_menu=false;
        state=STATE_MENU;
        menu_redraw();
    } else if(settings_from_hub) {
        settings_from_hub=false;
        state=STATE_HUB;
        draw_game_hub();
    } else if(resume_available) {
        state=STATE_PAUSE;
        draw_pause_screen(game_score(active_game),pause_selection);
    } else {
        enter_menu();
    }
}

int main() {
    stdio_init_all(); sleep_ms(150); // short USB-stdio settle; faster startup
    load_console_settings();
    spi_init(SPI_PORT,24000000);
    spi_set_format(SPI_PORT,8,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
    gpio_set_function(PIN_SCK,GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI,GPIO_FUNC_SPI);
    gpio_set_function(PIN_MISO,GPIO_FUNC_SPI);
    display_init();
    for(int i=0;i<8;i++){gpio_init(buttons[i]);gpio_set_dir(buttons[i],GPIO_IN);gpio_pull_up(buttons[i]);}
    init_buzzer(); audio_init(); audio_enable(true); audio_set_volume(console_volume); audio_set_music(MUSIC_MENU); srand(to_ms_since_boot(get_absolute_time()));
    draw_boot_screen(); menu_redraw();

    while(true) {
        audio_update();
        bool now[8]; for(int i=0;i<8;i++) now[i]=pressed(i);
        bool ue=now[0]&&!prev[0], de=now[1]&&!prev[1];
        bool le=now[2]&&!prev[2], re=now[3]&&!prev[3];
        bool ae=now[4]&&!prev[4], be=now[5]&&!prev[5];
        bool se=now[6]&&!prev[6], me=now[7]&&!prev[7];

        if(state==STATE_MENU) {
            // Navigation spans all eight games. Horizontal moves one item;
            // vertical moves by a row and naturally changes page.
            if(ue) {selected_game=(selected_game+6)%8;menu_redraw();}
            if(de) {selected_game=(selected_game+2)%8;menu_redraw();}
            if(le) {selected_game=(selected_game+7)%8;menu_redraw();}
            if(re) {selected_game=(selected_game+1)%8;menu_redraw();}
            if(se) {selected_game=(selected_game+4)%8;menu_redraw();sleep_ms(160);}
            if(ae) {hub_selection=0;state=STATE_HUB;draw_game_hub();}
            // GP8 flips between game pages; GP9 opens global settings from the main menu.
            if(me) { settings_from_menu=true; settings_from_hub=false; settings_selection=0; state=STATE_SETTINGS; draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); sleep_ms(160); }
            // B resumes the last active game without resetting its state.
            if(be&&resume_available) {state=STATE_GAME;game_draw(active_game);}
            sleep_ms(12);
        } else if(state==STATE_HUB) {
            if(ue){hub_selection=(hub_selection+3)%4;draw_game_hub();}
            if(de){hub_selection=(hub_selection+1)%4;draw_game_hub();}
            if(be){state=STATE_MENU;menu_redraw();}
            if(ae){
                if(hub_selection==0){difficulty_selection=selected_difficulty;state=STATE_DIFFICULTY;draw_difficulty_screen();}
                else if(hub_selection==1){if(resume_available&&active_game==selected_game){state=STATE_GAME;game_draw(active_game);}else{difficulty_selection=selected_difficulty;state=STATE_DIFFICULTY;draw_difficulty_screen();}}
                else if(hub_selection==2){state=STATE_HIGHSCORES;draw_highscores_screen();}
                else{settings_from_hub=true;settings_from_menu=false;state=STATE_SETTINGS;settings_selection=0;draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled());}
            }
            sleep_ms(15);
        } else if(state==STATE_DIFFICULTY) {
            if(ue){difficulty_selection=(difficulty_selection+2)%3;draw_difficulty_screen();}
            if(de){difficulty_selection=(difficulty_selection+1)%3;draw_difficulty_screen();}
            if(be){state=STATE_HUB;draw_game_hub();}
            if(ae){selected_difficulty=difficulty_selection;console_difficulty=selected_difficulty;game_level=1;active_game=selected_game;game_init(active_game);resume_available=true;state=STATE_GAME;audio_pause_music(false);audio_set_music(music_for_game(active_game));game_draw(active_game);}
            sleep_ms(15);
        } else if(state==STATE_HIGHSCORES) {
            if(be||ae){state=STATE_HUB;draw_game_hub();sleep_ms(120);}
            sleep_ms(15);
        } else if(state==STATE_GAME) {
            if(be) {resume_available=true;audio_set_music(MUSIC_MENU);audio_pause_music(false);enter_menu();}
            else if(se) {state=STATE_PAUSE;pause_selection=0;audio_pause_music(true);draw_pause_screen(game_score(active_game),pause_selection);}
            else {
                game_update(active_game,now[0],now[1],now[2],now[3],ae);
                int score=game_score(active_game);
                if(score>high_scores[active_game][selected_difficulty]) high_scores[active_game][selected_difficulty]=score;
                if(game_over(active_game)) {
                    game_draw(active_game);
                    if(game_won(active_game)) {
                        // Keep the clear screen visible; A restarts the current game.
                        if(ae) { game_init(active_game); game_draw(active_game); }
                        else sleep_ms(30);
                    } else if(ae) { game_init(active_game); game_draw(active_game); }
                    else sleep_ms(30);
                } else {game_draw(active_game);sleep_ms(active_game==4?32:16);}
            }
        } else if(state==STATE_PAUSE) {
            // Pause menu: Resume, Settings, Main Menu.
            if(ue) pause_selection=(pause_selection+2)%3;
            if(de) pause_selection=(pause_selection+1)%3;
            if(ue||de) draw_pause_screen(game_score(active_game),pause_selection);
            if(ae) {
                if(pause_selection==0) { state=STATE_GAME; audio_pause_music(false); game_draw(active_game); }
                else if(pause_selection==1) { settings_from_hub=false; settings_from_menu=false; state=STATE_SETTINGS; settings_selection=0; draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); }
                else { resume_available=true; audio_set_music(MUSIC_MENU); audio_pause_music(false); enter_menu(); }
            }
            if(be) { state=STATE_GAME; audio_pause_music(false); game_draw(active_game); }
            sleep_ms(20);
        } else if(state==STATE_SETTINGS) {
            if(ue) { settings_selection=(settings_selection+6)%7; draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); }
            if(de) { settings_selection=(settings_selection+1)%7; draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); }
            if(le && settings_selection==2) { console_brightness=(console_brightness<10)?0:console_brightness-10; set_console_brightness(console_brightness); draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); }
            if(re && settings_selection==2) { console_brightness=(console_brightness>90)?100:console_brightness+10; set_console_brightness(console_brightness); draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); }
            if(ae) {
                switch(settings_selection) {
                    case 0: audio_set_sfx_enabled(!audio_sfx_enabled()); draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); break;
                    case 1: audio_set_music_enabled(!audio_music_enabled()); draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); break;
                    case 2: console_brightness=(console_brightness>=100)?0:console_brightness+10; set_console_brightness(console_brightness); draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled()); break;
                    case 3: state=STATE_BUTTON_TEST; draw_button_test_screen(0); break;
                    case 4: state=STATE_DISPLAY_TEST; diagnostic_frame=0; draw_display_test_screen(diagnostic_frame); break;
                    case 5: state=STATE_AUDIO_TEST; audio_play_sfx(SFX_UI_CONFIRM); draw_audio_test_screen(audio_sfx_enabled() || audio_music_enabled()); break;
                    default: leave_settings(); break;
                }
                sleep_ms(150);
            }
            // B or MENU always exits Settings to the screen that opened it.
            if(be || me) { leave_settings(); sleep_ms(150); }
            sleep_ms(15);
        } else if(state==STATE_BUTTON_TEST) {
            int mask=0; for(int i=0;i<8;i++) if(now[i]) mask|=(1<<i);
            draw_button_test_screen(mask);
            if(be) {state=STATE_SETTINGS;draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled());sleep_ms(150);}
            sleep_ms(25);
        } else if(state==STATE_DISPLAY_TEST) {
            if((diagnostic_frame++%20)==0) draw_display_test_screen(diagnostic_frame/20);
            if(be) {state=STATE_SETTINGS;draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled());sleep_ms(150);}
            sleep_ms(15);
        } else if(state==STATE_AUDIO_TEST) {
            if(ae) { audio_play_sfx(SFX_VICTORY); draw_audio_test_screen(audio_sfx_enabled() || audio_music_enabled()); sleep_ms(150); }
            if(be) {state=STATE_SETTINGS;draw_settings_screen(settings_selection,audio_sfx_enabled(),audio_music_enabled());sleep_ms(150);}
            sleep_ms(15);
        }
        for(int i=0;i<8;i++)prev[i]=now[i];
        sleep_ms(4);
    }
}
