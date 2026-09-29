🎮 ARES Game Console

A DIY handheld retro gaming console built around the Raspberry Pi
Pico 2 and an SSD1306 OLED display, designed as a compact
embedded-systems project combining hardware, MicroPython, graphics,
input handling, game logic, and audio.

The project is developed as a practical embedded gaming platform rather
than just a single game. It provides a menu-driven interface from which
multiple retro-style games can be launched.

Repository:
ARES-Game-Console

📸 Project Photos

Boot Screen

The console starts with a custom ARES/Pico 2 boot screen displayed on
the OLED.



Game Selection Interface

The OLED provides a menu-based interface for selecting and launching
games.



✨ Project Highlights

🎮 Handheld-style retro gaming system

🧠 Raspberry Pi Pico 2 based controller

🖥️ 0.96-inch SSD1306 OLED display

🎛️ Six-button game control interface

🕹️ Menu-driven game selection

🎨 Custom boot animation and user interface

💾 Game/high-score management architecture

🔊 Audio/music support

⚡ USB-powered embedded platform

🐍 MicroPython-based software

📦 Modular game architecture

🧰 Hardware

Component                           Description

Raspberry Pi Pico 2             Main microcontroller and
game-processing platform

SSD1306 0.96" OLED              128×64 graphical display

6 Push Buttons                  User input and game controls

Breadboard                      Hardware prototyping

USB Cable                       Power and programming

Audio Hardware                  Audio output for game sounds/music

OLED Interface

The SSD1306 OLED is connected through I²C.

Typical interface signals:

Pico 2                 SSD1306
──────────────────────────────
3.3V       ───────────► VCC
GND        ───────────► GND
SDA        ───────────► SDA
SCL        ───────────► SCL

The display is used for:

Boot animation

Main menu

Game selection

Game graphics

Scores

High scores

Game status information

🎛️ Button Mapping

The current six-button configuration uses:

Button     GPIO Function

UP          GP2 Menu navigation / game-specific action
DOWN        GP3 Menu navigation / game-specific action
LEFT        GP4 Move left
RIGHT       GP5 Move right
A           GP6 Primary action
B           GP7 Secondary action / Back

The exact function of A/B/UP/DOWN can be assigned differently for
individual games.

💻 Software Stack

The software is written primarily in MicroPython for the Raspberry
Pi Pico 2.

Technologies

MicroPython

Python

Raspberry Pi Pico 2

SSD1306 OLED driver

I²C communication

GPIO input handling

PWM/audio where required

Frame-based graphics rendering

Game-state management

MicroPython is designed for microcontrollers and constrained embedded
systems, making it suitable for this type of Pico-based application.

🕹️ Game Architecture

The console is organized around a main menu and separate game modules.

Conceptually:

                    ┌─────────────────┐
                    │    BOOT         │
                    │   ANIMATION     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   MAIN MENU     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
       Pong               Snake           Space Invaders
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   GAME STATE    │
                    │ SCORE / PAUSE   │
                    │ HIGH SCORE      │
                    └─────────────────┘

This modular approach allows individual games to be developed and tested
independently while sharing common hardware and UI components.

🎮 Game Features

The project is designed to support several retro-style games, including:

Pong

Snake

Space Invaders

Dino

2048

Tetris

Full Speed

Lunar Module

The game architecture can be extended with additional games without
redesigning the complete hardware platform.

🖥️ User Interface

The UI is designed around the limitations of a 128×64 monochrome
OLED.

The interface includes:

Boot Animation

A custom startup animation provides an arcade-style boot experience.

Main Menu

Games are presented through a scrollable menu controlled using the
UP/DOWN buttons.

Game State

The software architecture supports concepts such as:

GAME
LEVEL
CURRENT SCORE
HIGH SCORE
GAME STATE

This provides a foundation for implementing:

New Game

Resume

Level Selection

High Scores

Pause

Game Over

Menu Navigation

🏆 Score & High-Score System

The console is designed to maintain game scores and high scores.

A typical game state can be represented as:

GAME STATE
│
├── Current Score
├── High Score
├── Level
├── Playing
├── Paused
└── Game Over

Future versions can persist high scores in Pico flash or another
non-volatile storage mechanism.

🔊 Audio

Audio is included as part of the arcade experience.

The design can support:

Game sound effects

Background music

Startup sound

Menu sounds

Game-specific music

For higher-quality audio output, an external I²S amplifier such as the
MAX98357A can be used with a suitable speaker.

⚙️ Power Management

The console is designed for USB-powered operation and can be extended
with battery power.

A power-saving architecture can include:

User Activity
     │
     ▼
Reset inactivity timer
     │
     ▼
No input for configured period
     │
     ▼
Power-saving / sleep mode
     │
     ▼
Button activity
     │
     ▼
Resume

This is particularly useful when the console is converted into a
standalone battery-powered handheld device.

📁 Repository Structure

The repository contains the MicroPython implementation and project
documentation.

A typical structure is:

ARES-Game-Console/
│
├── micropython/
│   ├── main.py
│   ├── boot_animation.py
│   ├── PicoGame.py
│   ├── PicoPong.py
│   ├── PicoSnake.py
│   ├── PicoSpaceInvaders.py
│   ├── PicoDino.py
│   ├── Pico2048.py
│   ├── PicoTetris.py
│   └── ...
│
├── images/
│
└── README.md

The exact filenames may evolve as the project is developed.

🚀 Getting Started

1. Clone the repository

git clone https://github.com/VINAYKURREiith/ARES-Game-Console.git
cd ARES-Game-Console

2. Install MicroPython on the Pico 2

Flash the appropriate MicroPython firmware for the Raspberry Pi Pico 2.

3. Connect the Hardware

Connect:

SSD1306 OLED through I²C

Six buttons to the configured GPIO pins

Audio hardware if required

USB to the Pico 2

4. Upload the MicroPython Files

Upload the required .py files to the Pico 2 filesystem.

The main entry point should be:

main.py

5. Run the Console

After rebooting the Pico 2:

BOOT ANIMATION
      ↓
MAIN MENU
      ↓
SELECT GAME
      ↓
PLAY

🧪 Development & Debugging

During development, the Pico can be connected to a computer through USB
for:

Code upload

Serial debugging

Runtime error monitoring

Testing individual games

Testing OLED communication

Testing button inputs

For MicroPython development, tools such as mpremote can also be used
to interact with the device and transfer/run scripts over the serial
connection. citeturn2search8

🔌 System Block Diagram

                       ┌──────────────────┐
                       │   Raspberry Pi   │
                       │      Pico 2      │
                       └────────┬─────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ SSD1306    │    │ 6 Buttons  │    │   Audio    │
       │ OLED       │    │ GP2 - GP7  │    │  Output    │
       └────────────┘    └────────────┘    └────────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Game Engine    │
                       │                 │
                       │ Menu / Input    │
                       │ Graphics        │
                       │ Physics         │
                       │ Score           │
                       │ Game State      │
                       └─────────────────┘

🎯 Learning Objectives

This project provides hands-on experience with:

Embedded systems

Raspberry Pi Pico 2

MicroPython

GPIO programming

I²C communication

OLED graphics

Game-loop design

Input handling

Framebuffer rendering

State machines

Game physics

Score management

Audio generation

Power management

Modular software architecture

🔮 Future Improvements

Planned or possible extensions include:

🔋 Rechargeable battery system

📦 Custom 3D-printed enclosure

📡 Wi-Fi multiplayer

🎵 Per-game background music

🔊 Improved audio system

💾 Persistent save/high-score storage

⚡ DMA-based display updates

💤 Automatic power-saving mode

🎮 More games

🖥️ Larger color display

🕹️ Improved game controller layout

🧵 FreeRTOS-based implementation

🌐 Multiplayer networking

📌 Project Status

Current stage: Functional prototype

The prototype demonstrates:

Raspberry Pi Pico 2 operation

SSD1306 OLED graphics

Custom boot screen

Game-selection interface

Button-based navigation

Modular retro-game architecture

The project can be further developed into a compact standalone handheld
console.

👨‍💻 Author

Vinay Kurre

B.Tech --- Electrical Engineering
Indian Institute of Technology Hyderabad

GitHub: VINAYKURREiith

⭐ Repository

ARES-Game-Console

If you find the project interesting, consider giving the repository a
⭐.

📄 License

This project is intended for educational, experimental, and personal
embedded-systems development.
