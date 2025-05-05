# pico-rom-emu-firmware (c) by Greg Coonrod
#
# pico-rom-emu-firmware is licensed under a
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

from machine import Pin, UART
from utime import sleep_us, ticks_ms, sleep_ms
from sys import print_exception, stdin, stdout
import select
import struct  # For packing/unpacking address

DEBUG = False

# RAM control pins for WEb, OEb, and CSb
pin_ram_web = Pin(7, Pin.OUT)
pin_ram_oeb = Pin(8, Pin.OUT)
pin_ram_csb = Pin(9, Pin.OUT)

# Latch control pins for LADL, LADH, and LADD
pin_ladl = Pin(10, Pin.OUT)
pin_ladh = Pin(11, Pin.OUT)
pin_ladd = Pin(12, Pin.OUT)

# Reset pin
pin_rstb = Pin(14, Pin.OUT)

# eXternal Data and Address pins (XDA)
pin_xda7 = Pin(15, Pin.OUT)
pin_xda6 = Pin(16, Pin.OUT)
pin_xda5 = Pin(17, Pin.OUT)
pin_xda4 = Pin(18, Pin.OUT)
pin_xda3 = Pin(19, Pin.OUT)
pin_xda2 = Pin(20, Pin.OUT)
pin_xda1 = Pin(21, Pin.OUT)
pin_xda0 = Pin(22, Pin.OUT)

# Latch Output Enable pin
pin_loeb = Pin(26, Pin.OUT)


# --- Pin Initialization ---
def init_pins():
    pin_ram_web.on()
    pin_ram_oeb.on()
    pin_ram_csb.on()
    pin_ladl.off()
    pin_ladh.off()
    pin_ladd.off()
    pin_rstb.on()  # Start with reset de-asserted (system running)
    write_xda(0)  # Set XDA pins to output low
    pin_loeb.on()  # Latch outputs disabled initially


# --- XDA Bus Control ---
def write_xda(data):
    pin_xda7.value((data >> 7) & 0x01)
    pin_xda6.value((data >> 6) & 0x01)
    pin_xda5.value((data >> 5) & 0x01)
    pin_xda4.value((data >> 4) & 0x01)
    pin_xda3.value((data >> 3) & 0x01)
    pin_xda2.value((data >> 2) & 0x01)
    pin_xda1.value((data >> 1) & 0x01)
    pin_xda0.value(data & 0x01)


# --- RAM Write Function ---
def write_ram(addr, data):
    address_high = (addr >> 8) & 0xFF
    address_low = addr & 0xFF

    # Write high address byte
    write_xda(address_high)
    pin_ladh.on()
    sleep_us(1)
    pin_ladh.off()

    # Write low address byte
    write_xda(address_low)
    pin_ladl.on()
    sleep_us(1)
    pin_ladl.off()

    # Write data byte
    write_xda(data)
    pin_ladd.on()
    sleep_us(1)
    pin_ladd.off()

    # Pulse WEb to write
    pin_ram_web.off()
    sleep_us(1)
    pin_ram_web.on()


# --- Serial ROM Upload Function ---
def receive_rom_serial():
    """
    Waits for serial upload command 'U'.
    Receives a 2-byte little-endian starting address.
    Receives ROM data byte-by-byte until host sends 'E'.
    Writes received data to RAM.
    """
    # Use USB CDC serial
    # Set up polling object for stdin
    poll_obj = select.poll()
    poll_obj.register(stdin, select.POLLIN)

    print("Ready for serial ROM upload. Send 'U' to start.")

    # Wait for Upload command 'U'
    start_cmd = None
    while start_cmd != b"U":
        # Check if data is available on stdin
        poll_results = poll_obj.poll(1)  # Timeout after 1ms
        if poll_results:
            start_cmd = stdin.buffer.read(1)
        sleep_ms(10)  # Small delay to prevent busy-waiting

    print("Start command received.")
    stdout.buffer.write(b"A")  # Send Acknowledge

    # Receive 2-byte starting address (little-endian)
    addr_bytes = stdin.buffer.read(2)
    if len(addr_bytes) < 2:
        print("Error: Did not receive address.")
        return 0, 0  # Indicate error

    start_addr = struct.unpack("<H", addr_bytes)[
        0
    ]  # '<H' is little-endian unsigned short
    print(f"Receiving ROM data starting at address: 0x{start_addr:04X}")

    addr = start_addr
    bytes_written = 0
    start_time = ticks_ms()

    # Assert reset during upload
    pin_rstb.off()
    sleep_us(100)

    # Select RAM and enable latch output
    pin_ram_csb.off()
    pin_loeb.off()

    try:
        while True:
            # Wait for a byte, but check for End command 'E'
            # Use polling with a short timeout to remain responsive
            poll_results = poll_obj.poll(1000)  # Wait up to 1 second for data
            if not poll_results:
                print("Warning: Timeout waiting for data.")
                # Consider breaking or adding more robust error handling
                continue  # Keep waiting for now

            byte = stdin.buffer.read(1)

            if not byte:  # Should not happen with poll, but good practice
                print("Error: Serial connection closed unexpectedly.")
                break

            if byte == b"E":  # Check for End command
                print("End command received.")
                stdout.buffer.write(b"K")  # Send Confirmation
                break

            # Write the received byte to RAM
            write_ram(addr, byte[0])
            addr += 1
            bytes_written += 1

            # Optional: Add progress indicator
            if DEBUG and (bytes_written % 256 == 0):
                print(f"Received {bytes_written} bytes...")

    except Exception as e:
        print("Error during serial reception:")
        print_exception(e)
        bytes_written = 0  # Indicate failure
    finally:
        # De-select RAM, disable latch output (important first!)
        pin_ram_csb.on()
        pin_loeb.on()
        # De-assert reset *after* disabling RAM/latches
        pin_rstb.on()
        sleep_us(100)  # Give time for reset to propagate

    end_time = ticks_ms()
    return bytes_written, start_time, end_time, start_addr


# --- Main Execution ---
def main():
    init_pins()
    print("Pico ROM Emulator Ready.")
    print("Send 'U' over serial to upload a ROM.")

    while True:
        # Wait for and perform serial upload
        bytes_written, start_time, end_time, start_addr = receive_rom_serial()

        if bytes_written > 0:
            elapsed_ms = end_time - start_time
            elapsed_s = elapsed_ms / 1000.0
            write_speed = bytes_written / elapsed_s if elapsed_s > 0 else 0
            print(
                f"\nSuccessfully wrote {bytes_written} bytes starting at 0x{start_addr:04X} to RAM."
            )
            print(f"Time taken: {elapsed_s:.2f} seconds")
            print(f"Average write speed: {write_speed:.2f} bytes/second")
            print("\nSystem reset released. Emulator running...")
            print("Send 'U' again to upload another ROM.")
        else:
            print("\nROM upload failed or was cancelled.")
            print("Send 'U' to try again.")

        # The loop continues, waiting for the next 'U' command


if __name__ == "__main__":
    main()
