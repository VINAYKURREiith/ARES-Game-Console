
# 🎮 ARES – Pocket Arcade

### A Custom Retro Gaming Console Powered by Raspberry Pi Pico 2

ARES Pocket Arcade is a compact, standalone retro gaming console built around the **Raspberry Pi Pico 2 (RP2350)**. It brings classic arcade-style games to an embedded platform through custom graphics rendering, real-time input handling, game-state management, and hardware-level display interfacing.

The project explores embedded systems, low-level hardware programming, graphics rendering, game-loop design, and performance optimization on a resource-constrained microcontroller.

---

## 📸 Project Overview

ARES is designed as a self-contained gaming platform with:

- A custom boot interface and game-selection menu.
- A 2.8-inch colour TFT display.
- Eight-button game controls.
- Multiple retro-style games.
- Framebuffer-based graphics rendering.
- Score and game-state management.
- Buzzer-based sound effects.
- USB-powered operation.

The console runs its firmware directly on the Raspberry Pi Pico 2 without requiring a PC during gameplay.

---

## ✨ Key Features

- **Custom Embedded Console:** Built using the Raspberry Pi Pico 2 (RP2350).
- **Colour TFT Interface:** 320 × 240 display resolution in landscape orientation.
- **Multiple Games:** Eight arcade-style games integrated into one console.
- **Custom Graphics Engine:** Framebuffer-based rendering for game graphics.
- **Input Management:** Eight physical buttons mapped to GPIO pins.
- **Game State Management:** Menu navigation, gameplay, scoring, and game-over handling.
- **Audio Feedback:** Buzzer-based sound effects using PWM.
- **Performance Monitoring:** Frame-rate measurement and display performance analysis.
- **Standalone Operation:** Firmware executes directly from the Pico 2.

---

## 🕹️ Games Included

| No. | Game | Description |
|---|---|---|
| 1 | 2048 | Number-merging puzzle game |
| 2 | Pong | Classic two-paddle arcade game |
| 3 | Sky Invaders | Space-shooter inspired by Space Invaders |
| 4 | Breakout | Paddle-controlled brick-breaking game |
| 5 | Tetris | Falling-block puzzle game |
| 6 | Snake | Classic snake movement and food collection |
| 7 | Racing | Arcade-style racing game |
| 8 | Sokoban | Grid-based box-pushing puzzle |

Each game uses the common console interface and input hardware while maintaining its own gameplay logic.

---

## 🔧 Hardware Components

| Component | Specification / Purpose |
|---|---|
| Microcontroller | Raspberry Pi Pico 2 |
| MCU Architecture | RP2350 |
| Display | Waveshare 2.8-inch TFT |
| Display Resolution | 320 × 240 pixels |
| Display Interface | SPI |
| Display Controller | HX8347D |
| Input Interface | 8 push buttons |
| Audio | PWM buzzer |
| Power Supply | USB 5 V |
| Development Interface | USB |

### Display

The console uses a Waveshare 2.8-inch TFT display with a 320 × 240 resolution.

The display provides a colour graphical interface for:

- Boot screen and main menu.
- Game graphics and animations.
- Player movement and game objects.
- Score and status information.
- Game-over and menu screens.

### Button Configuration

The physical controls are connected to the Pico 2 GPIO pins.

| Button | GPIO |
|---|---|
| UP | GP2 |
| DOWN | GP3 |
| LEFT | GP4 |
| RIGHT | GP5 |
| A | GP6 |
| B | GP7 |
| X | GP8 |
| Y | GP9 |

The buttons provide directional movement, selection, gameplay actions, and navigation.

### Audio

A PWM-controlled buzzer connected to GP15 provides basic sound feedback during gameplay.

---

## 🧠 System Architecture

The console follows a modular embedded software architecture.

```text
             Raspberry Pi Pico 2
                  (RP2350)
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
      TFT Display  8 Buttons    Buzzer
          |           |           |
          +-----------+-----------+
                      |
                      v
              ARES Game Engine
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Main Menu   Input System  Audio
          |
          v
      Game Selection
          |
    +-----+-----+-----+-----+
    |     |     |     |     |
   2048  Pong  Tetris Snake ...
    |
    v
  Game Logic
    |
    v
 Graphics / Framebuffer
    |
    v
  TFT Display Output
```

### Software Modules

The architecture separates the major responsibilities:

- **Display Driver:** Handles TFT initialization and display communication.
- **Graphics Engine:** Manages drawing operations and framebuffer rendering.
- **Input Manager:** Reads and processes physical button inputs.
- **Game Manager:** Handles game selection and transitions.
- **Game Modules:** Implement individual game logic and mechanics.
- **Audio Module:** Generates buzzer-based sound effects.
- **System Manager:** Coordinates the overall console operation.

---

## 💻 Software and Development Tools

| Technology | Application |
|---|---|
| C / C++ | Embedded firmware development |
| Raspberry Pi Pico SDK | Hardware and peripheral programming |
| CMake | Build configuration |
| Ninja | Build automation |
| PIO | Programmable I/O support where used |
| SPI | TFT display communication |
| GPIO | Button input handling |
| PWM | Buzzer sound generation |
| DMA | Hardware transfer optimization where implemented |
| VS Code | Development environment |

The firmware is compiled into a UF2 binary that can be flashed onto the Raspberry Pi Pico 2.

---

## 🎨 Graphics and Rendering

The console uses a framebuffer-oriented graphics approach.

A framebuffer stores pixel information before it is transferred to the display.

For a 320 × 240 display using RGB565 colour representation:

\[
320 \times 240 \times 2 = 153600 \text{ bytes}
\]

This corresponds to approximately 150 KiB of pixel data for one full frame.

The graphics system supports:

- Pixel and shape drawing.
- Game-object rendering.
- Text and score rendering.
- Screen updates.
- Game-specific graphical layouts.

---

## ⚡ Performance Evaluation

The console's rendering performance can be evaluated using frames per second (FPS).

FPS represents the number of frames rendered per second.

\[
FPS = \frac{\text{Number of Frames}}{\text{Elapsed Time}}
\]

During project testing, a frame rate of approximately **19.53 FPS** was observed.

At 320 × 240 resolution with RGB565:

\[
\text{Frame Size} = 150 \text{ KiB}
\]

The corresponding theoretical full-frame pixel-data rate at 19.53 FPS is approximately:

\[
150 \times 19.53 = 2929.5 \text{ KiB/s}
\]

Actual display-interface traffic and rendering performance depend on the update strategy and implementation.

---

## 🚀 Getting Started

### 1. Requirements

Install the following development tools:

- Raspberry Pi Pico SDK
- ARM GNU Toolchain
- CMake
- Ninja
- Git
- Visual Studio Code (recommended)

### 2. Clone the Repository

```bash
git clone https://github.com/VINAYKURREiith/ARES-Game-Console.git

cd ARES-Game-Console
```

### 3. Configure the Pico SDK

Set the Pico SDK environment variable.

Windows PowerShell:

```powershell
$env:PICO_SDK_PATH = "C:\path\to\pico-sdk"
```

Use the location where the SDK is installed on your system.

### 4. Build the Firmware

From the project root, configure and build using CMake and Ninja:

```bash
cmake -S . -B build -G Ninja
cmake --build build
```

The exact build commands may need adjustment if the project uses a different CMake configuration or build directory.

### 5. Flash the Pico 2

1. Disconnect the Raspberry Pi Pico 2 from USB.
2. Hold the BOOTSEL button.
3. Connect the Pico 2 to the computer.
4. Release BOOTSEL when the `RPI-RP2` drive appears.
5. Copy the generated `.uf2` firmware file to the drive.

The Pico 2 will reboot and execute the ARES firmware.

---

## 🧪 Testing and Validation

The project involves hardware and software validation, including:

- TFT initialization and communication testing.
- Display orientation and colour testing.
- GPIO button-input testing.
- Game functionality and state-transition testing.
- Buzzer output testing.
- Frame-rate measurement.
- Firmware compilation and flashing.
- Runtime debugging through USB.

---

## 📚 Learning Outcomes

This project provides practical experience in:

- Embedded C/C++ programming.
- Raspberry Pi Pico 2 and RP2350 architecture.
- Hardware peripheral interfacing.
- SPI communication.
- GPIO and PWM programming.
- Framebuffer-based graphics.
- Display-driver development.
- Game-loop implementation.
- Real-time input processing.
- Memory allocation and optimization.
- Embedded firmware development.
- CMake-based build systems.

---

## 🔮 Possible Future Improvements

- Rechargeable battery-powered operation.
- Custom PCB and enclosure design.
- Persistent high-score storage.
- Wi-Fi-based multiplayer.
- Additional arcade games.
- Improved graphics and animation performance.
- Enhanced audio output.
- Further display-transfer optimization.

---

## 👨‍💻 Author

**Vinay Kurre**

B.Tech – Electrical Engineering  
Indian Institute of Technology Hyderabad

- GitHub: [VINAYKURREiith](https://github.com/VINAYKURREiith)
- Project: [ARES Game Console](https://github.com/VINAYKURREiith/ARES-Game-Console)
- LinkedIn: [Vinay Kurre](https://www.linkedin.com/in/vinay-kurre-44bba52a8/)

---

## ⭐ Support

If you find this project interesting, consider starring the repository!

Built with curiosity, embedded systems, and a love for retro gaming. 🎮
