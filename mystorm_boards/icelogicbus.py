import os
import subprocess
import serial
import serial.tools.list_ports as lp
from amaranth.build import *
from amaranth_boards.resources import *
from amaranth.vendor.lattice_ice40 import LatticeICE40Platform

__all__ = ["IceLogicBusPlatform"]

# Pinout definitions
LED =" J11" #B7
RX = " K7"
TX = " L7"
SPI =" K9 J9 L10 L7" #si,so, sck,ss
TILE1 = " F1 F2 F4 F3 G1 G2 G3 H3 H1 H2 J1 K1" #C
TILE2 = " K11 H10 J10 G8 H11 G10 D9 E11 G9 G11 F10 F9" #G
TILE3= " B1 B2 C4 C3 C2 C1 E1 D1 D2 D3 E2 E3" #B
TILE4 = " A9 C8 A8 C7 A6 A5 A2 A3 F11 E9 E10 E8" #F

BLADE1 = " K7 L7 J7 H7 L8 J8"
BLADE2 = " B3 A1 A4 B4 B5 D5"
BLADE3 = " D7 B6 A7 B8 B9 C9"
BLADE4 = " D10 D11 C11 B11 A11 A10"
# USER = " J11 B6 D7 B7"
# SUPER = " B4 A4 A1 B3 _ _ _ _"
GENPINS = " - - - - - - - -"
# QSPIE = " J8 H7 K7 L8 H9 L7 J7" # qdo,qd1,qd2,qd3,qck,qss,qdr
# TILE2 = " D10 D11 B11 C11 A10 A11 C9 B9 A7 B8 D5 B5"



MEZZA = " L1 J3 L2 K3 L3 J4 K4 L4 J5 K5 K6 - - - - - - - - - - -" # Rx,Tx, DQ2,DQ4,DQK,DQ0,DQ5,DQR,DQ1,DQ6,DQ7,DQ3,DS0
MEZZB = " L10 - J9 K9 - - - - - - - - - - - - - - - - -"

# IceLogicDeck : https://github.com/folknology/IceLogicDeck
class IceLogicBusPlatform(LatticeICE40Platform):
    upload_port = None
    device = "iCE40HX4K"
    package = "BG121"
    default_clk = "clk25"
    resources = [
        Resource("clk25", 0, Pins("B7", dir="i"),
                 Clock(25e6), Attrs(GLOBAL=True, IO_STANDARD="SB_LVCMOS")
                 ),
        # led
        Resource("led", 0, Pins(LED, dir="o", invert=True),
                 Attrs(IO_STANDARD="SB_LVCMOS")
                 ),
        Resource("tx", 0, Pins(TX, dir="o"),
                 Attrs(IO_STANDARD="SB_LVCMOS")
                 ),
        Resource("rx", 0, Pins(RX, dir="o"),
                 Attrs(IO_STANDARD="SB_LVCMOS")
                 ),
        # SPI
        # Resource("sck", 0, Pins("L10", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # Resource("copi", 0, Pins("J9", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # Resource("cs_n", 0, Pins("L7", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # Resource("cipo", 0, Pins("K9", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # QSPIE
        Resource("qd0", 0, Pins("J9", dir="io"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qd1", 0, Pins("K9", dir="io"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qd2", 0, Pins("K6",  dir="io"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qd3", 0, Pins("L5",  dir="io"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qck", 0, Pins("L10", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qss", 0, Pins("K10", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        Resource("qdr", 0, Pins("J7", dir="i"), Attrs(IO_STANDARD="SB_LVCMOS")),
        # Uart
        UARTResource(0,
                     rx="K7", tx="L7",
                     attrs=Attrs(IO_STANDARD="SB_LVCMOS", PULLUP=1),
                     role="dce"
                     ),
        # *SPIFlashResources(0,
        #                    cs_n="L7", clk="L10", copi="J9", cipo="K9",
        #                    attrs=Attrs(IO_STANDARD="SB_LVCMOS")
        #                    )
        #Hyperram ?
    ]
    connectors  = [
        # Tile connectors
        Connector("tile", 1, TILE1 + GENPINS),  #
        Connector("tile", 2, TILE2 + GENPINS),  #
        Connector("tile", 3, TILE3 + GENPINS),  #
        Connector("tile", 4, TILE4 + GENPINS),  #
        # Micro Blade connectores
        Connector("blade", 1, BLADE1),
        Connector("blade", 2, BLADE2),
        Connector("blade", 3, BLADE3),
        Connector("blade", 4, BLADE4),
        # Mezzanine Connectors
        Connector("mez", 0, MEZZA),  #
        Connector("mez", 1, MEZZB),  #
    ]

    def get_port(self):
        for p in lp.comports():
            if p.vid == 5824:
                self.upload_port = p

    def toolchain_program(self, products, name, **kwargs):
        if self.upload_port is None:
            self.get_port()
            if self.upload_port is None:
                print("could not find a suitable device for upload port, cannot upload")
                return
            else:
                print("Found device for uploading: ", self.upload_port.product + ' as device ' + self.upload_port.device)

        print("Uploading ", self.upload_port.product + ' as device ' + self.upload_port.device)
        with serial.Serial(self.upload_port.device) as ser:
            with products.extract("{}.bin".format(name)) as bitstream_filename:
                with open(bitstream_filename, 'rb') as f:
                    ser.write(f.read())
        # device = os.environ.get("DEVICE", p.device) # "/dev/ttyACM2"
        # with products.extract("{}.bin".format(name)) as bitstream_filename:
        #     subprocess.check_call(["cp", bitstream_filename, device])

    # def upload(self port=None):
    # if port is None:
    #     for p in lp():
    #         if p.vid is 5824:
    #             ser = serial.Serial(p.device)
    #             with open(products.extract("{}.bin".format(name))) as f:
    #                 ser.write(f.read())

    def bus_send(self, bytes2send):
        if self.upload_port is None:
            self.get_port()
            if self.upload_port is None:
                print("could not find a suitable device for upload port, cannot upload")
                return
            else:
                print("Found device for uploading: ", self.upload_port.product + ' as device ' + self.upload_port.device)

        with serial.Serial(self.upload_port.device) as ser:
            ser.write(bytes2send)

#bus_send(bytearray(b'\x00\xff'))

if __name__ == "__main__":
    #from .test.blinky import *
    from amaranth_boards.test.blinky import *
    IceLogicBusPlatform().build(Blinky(), do_program=True)
