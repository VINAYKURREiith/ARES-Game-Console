# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.3.1)
set(toolchainVersion 15_2_Rel1)
set(picotoolVersion 2.3.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
cmake_minimum_required(VERSION 3.13)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()

set(sdkVersion 2.3.1)
set(toolchainVersion 15_2_Rel1)
set(picotoolVersion 2.3.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if(EXISTS ${picoVscode})
    include(${picoVscode})
endif()

set(PICO_BOARD pico2 CACHE STRING "Board type")
# Reserve the final 4 KiB sector of the Pico 2 4 MiB flash for persistent settings.
set(PICO_FLASH_SIZE_BYTES 4190208 CACHE STRING "Firmware flash region (last 4 KiB reserved for ARES settings)" FORCE)
include(pico_sdk_import.cmake)
project(ARES_GAME_CONSOLE C CXX ASM)
pico_sdk_init()

add_executable(ARES_GAME_CONSOLE
    main.cpp
    core/common.cpp
    audio/audio.cpp
    games/pong/pong.cpp
    games/snake/snake.cpp
    games/invaders/invaders.cpp
    games/breakout/breakout.cpp
    games/game2048/game2048.cpp
    games/tetris/tetris.cpp
    games/racing/racing.cpp
    games/sokoban/sokoban.cpp
)

pico_set_program_name(ARES_GAME_CONSOLE "ARES_GAME_CONSOLE")
pico_set_program_version(ARES_GAME_CONSOLE "0.3")
pico_enable_stdio_uart(ARES_GAME_CONSOLE 0)
pico_enable_stdio_usb(ARES_GAME_CONSOLE 1)

target_link_libraries(ARES_GAME_CONSOLE
    pico_stdlib
    hardware_spi
    hardware_pwm
    m
)

target_include_directories(ARES_GAME_CONSOLE PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/core
    ${CMAKE_CURRENT_LIST_DIR}/games/snake
    ${CMAKE_CURRENT_LIST_DIR}/games/pong
    ${CMAKE_CURRENT_LIST_DIR}/games/invaders
    ${CMAKE_CURRENT_LIST_DIR}/games/breakout
    ${CMAKE_CURRENT_LIST_DIR}/games/game2048
    ${CMAKE_CURRENT_LIST_DIR}/games/tetris
    ${CMAKE_CURRENT_LIST_DIR}/games/racing
    ${CMAKE_CURRENT_LIST_DIR}/games/sokoban
    ${CMAKE_CURRENT_LIST_DIR}/audio
)

pico_add_extra_outputs(ARES_GAME_CONSOLE)
