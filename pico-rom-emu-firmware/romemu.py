# pico-rom-emu-firmware (c) by Greg Coonrod
# 
# pico-rom-emu-firmware is licensed under a
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
# 
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

from machine import Pin
from utime import sleep_us, ticks_ms
from sys import print_exception

DEBUG = False

# RAM control pins for WEb, OEb, and CSb
pin_ram_web = Pin(7, Pin.OUT)
pin_ram_oeb = Pin(8, Pin.OUT)
pin_ram_csb = Pin(9, Pin.OUT)

# Latch control pins for LADL, LADH, and LADD
# These pins are used to latch the XDA bus into the 
# RAM address (High and Low) and data pins.
# 74HCT574 is used to latch the data and address pins
pin_ladl = Pin(10, Pin.OUT)
pin_ladh = Pin(11, Pin.OUT)
pin_ladd = Pin(12, Pin.OUT)

# Reset pin used to force the external system into reset
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

# Latch Output Enable pin for the 74HCT574 latch
pin_loeb = Pin(26, Pin.OUT)

def init_pins():
    # Initialize all pins
    # pins ending in 'b' are active low
    pin_ram_web.on()
    pin_ram_oeb.on()
    pin_ram_csb.on()

    pin_ladl.off()
    pin_ladh.off()
    pin_ladd.off()

    pin_rstb.on()

    pin_xda7.off()
    pin_xda6.off()
    pin_xda5.off()
    pin_xda4.off()
    pin_xda3.off()
    pin_xda2.off()
    pin_xda1.off()
    pin_xda0.off()

    pin_loeb.on()

def write_xda(data):
    # Write data to the XDA pins
    pin_xda7.value((data >> 7) & 0x01)
    pin_xda6.value((data >> 6) & 0x01)
    pin_xda5.value((data >> 5) & 0x01)
    pin_xda4.value((data >> 4) & 0x01)
    pin_xda3.value((data >> 3) & 0x01)
    pin_xda2.value((data >> 2) & 0x01)
    pin_xda1.value((data >> 1) & 0x01)
    pin_xda0.value(data & 0x01)

# Assume Latch Output Enable and RAM CSb are always on
def write_ram(addr, data):
    address_high = (addr >> 8) & 0xFF
    address_low = addr & 0xFF

    # Write the high byte of the address to the XDA pins
    write_xda(address_high)
    # toggle the latch to store the high byte of the address
    pin_ladh.on()
    sleep_us(1) # 1ms delay to latch the address
    pin_ladh.off()

    # Write the low byte of the address to the XDA pins
    write_xda(address_low)
    # toggle the latch to store the low byte of the address
    pin_ladl.on()
    sleep_us(1) # 1ms delay to latch the address
    pin_ladl.off()

    # Write the data to the XDA pins
    write_xda(data)
    # toggle the latch to store the data
    pin_ladd.on()
    sleep_us(1) # 1ms delay to latch the data
    pin_ladd.off()

    # Pulse the WEb pin to write the data to RAM
    pin_ram_web.off()
    sleep_us(1) # 1ms delay to write the data
    pin_ram_web.on()

def main():
    # assert reset
    pin_rstb.off()
    sleep_us(100) # hold reset for 100ms

    # Starting address
    addr = 0x0000

    # Select RAM and enable latch output
    pin_ram_csb.off()
    pin_loeb.off()

    start = ticks_ms()
    bytes_written = 0
    try:
        with open("rom.bin", "rb") as rom:
            # Read the ROM file byte by byte and write it to the RAM
            while True:
                byte = rom.read(1)
                if not byte:
                    break
                byte =  int.from_bytes(byte, 'little')
                write_ram(addr, byte)
                addr += 1
                bytes_written += 1
                if DEBUG & (bytes_written % 256 == 0):
                    print(f"Wrote {bytes_written / 256} pages to RAM")
                
    except Exception as e:
        print_exception(e)
        return
    finally:
        # De-assert reset
        pin_ram_csb.on()
        pin_loeb.on()
        pin_rstb.on()

    end = ticks_ms()
    elapsed = (end - start) / 1000.0
    print(f"Wrote {bytes_written} bytes to RAM in {elapsed:.2f} seconds")
    print(f"Average write speed: {bytes_written / elapsed:.2f} bytes/second")
              

if __name__ == "__main__":
    print("Writing ROM to RAM...")
    init_pins()
    main()
    print("Finished writing ROM to RAM.")