# Pico-ROM-Emu

Pico-ROM-Emu is a project designed to emulate ROM functionality using the Raspberry Pi Pico. It consists of two main sub-projects: a KiCad-based physical circuit schematic and PCB design, and MicroPython-based firmware.

## Sub-Projects

### 1. KiCad Circuit Schematic and PCB Design
This sub-project contains the hardware design files for the Pico-ROM-Emu. Using KiCad, it provides:
- A detailed circuit schematic for the emulator.
- PCB layout files for manufacturing the hardware.

### 2. MicroPython Firmware (`pico-rom-emu-firmware`)
This sub-project contains the firmware written in MicroPython. It is responsible for:
- Copying provided ROM binary images to the embedded SRAM

## Getting Started
1. Clone the repository:
    ```bash
    git clone https://github.com/gcoonrod/pico-rom-emu.git
    ```
2. Navigate to the respective sub-project directories for setup instructions.

## License
This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE).

## Contributions
Contributions are welcome! Please open an issue or submit a pull request.

## Contact
For questions or feedback, feel free to reach out via the repository's issue tracker.