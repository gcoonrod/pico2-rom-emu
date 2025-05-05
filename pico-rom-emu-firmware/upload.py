# pico-rom-emu (c) by Greg Coonrod
# 
# pico-rom-emu is licensed under a
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
# 
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

import serial
import sys
import time
import struct # For packing address

def upload_rom(serial_port, baud_rate, file_path, start_address):
    """
    Uploads a ROM file (.bin) to the Pico ROM Emulator over serial.

    Args:
        serial_port (str): The serial port the Pico is connected to (e.g., 'COM3', '/dev/ttyACM0').
        baud_rate (int): The baud rate (should match Pico configuration, though typically ignored for USB CDC).
        file_path (str): Path to the .bin ROM file.
        start_address (int): The starting memory address (0x0000 to 0xFFFF).
    """
    try:
        print(f"Opening serial port {serial_port} at {baud_rate} baud...")
        ser = serial.Serial(serial_port, baud_rate, timeout=2)
        time.sleep(1) # Give the serial port time to initialize

        print(f"Attempting to upload '{file_path}' starting at address 0x{start_address:04X}...")

        # 1. Send Start command 'U'
        print("Sending start command 'U'...")
        ser.write(b'U')
        ser.flush()

        # 2. Wait for Acknowledge 'A'
        print("Waiting for acknowledge 'A'...")
        ack = ser.read(1)
        if ack != b'A':
            print(f"Error: Expected 'A' acknowledgement, but received: {ack}")
            ser.close()
            return False
        print("Acknowledge received.")

        # 3. Send 2-byte starting address (little-endian)
        addr_bytes = struct.pack('<H', start_address) # '<H' = little-endian unsigned short
        print(f"Sending start address: 0x{start_address:04X} ({addr_bytes.hex()})")
        ser.write(addr_bytes)
        ser.flush()

        # 4. Send ROM data
        print("Sending ROM data...")
        bytes_sent = 0
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(1) # Read one byte at a time
                    if not chunk:
                        break # End of file
                    ser.write(chunk)
                    bytes_sent += 1
                    if bytes_sent % 256 == 0:
                         print(f"Sent {bytes_sent} bytes...", end='\r')

            print(f"\nFinished sending {bytes_sent} bytes.")

        except FileNotFoundError:
            print(f"Error: File not found at '{file_path}'")
            ser.close()
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            ser.close()
            return False

        # 5. Send End command 'E'
        print("Sending end command 'E'...")
        ser.write(b'E')
        ser.flush()

        # 6. Wait for Confirmation 'K'
        print("Waiting for confirmation 'K'...")
        confirm = ser.read(1)
        if confirm == b'K':
            print("Confirmation 'K' received. Upload successful!")
            ser.close()
            return True
        else:
            print(f"Error: Expected 'K' confirmation, but received: {confirm}")
            ser.close()
            return False

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python upload_rom.py <serial_port> <rom_file.bin> <start_address_hex>")
        print("Example: python upload_rom.py COM3 my_rom.bin 8000")
        sys.exit(1)

    port = sys.argv[1]
    rom_file = sys.argv[2]
    try:
        address = int(sys.argv[3], 16) # Interpret address as hexadecimal
        if not (0x0000 <= address <= 0xFFFF):
            raise ValueError("Start address must be between 0x0000 and 0xFFFF")
    except ValueError as e:
        print(f"Error: Invalid start address '{sys.argv[3]}'. {e}")
        sys.exit(1)

    # --- Configuration ---
    BAUD = 115200 # Baud rate often doesn't matter for USB CDC, but set it anyway

    if upload_rom(port, BAUD, rom_file, address):
        print("Upload completed successfully.")
    else:
        print("Upload failed.")
        sys.exit(1)