#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Decode LoRa packets
# GNU Radio version: 3.10.1.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import gr
from gnuradio.fft import window
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iio
import lora
from threading import *
import socket
import time
import select

#Global Variables
localIP     = "127.0.0.1"
checkModePort   = 40868
bufferSize  = 1024

EXIT = False
TIMEOUT = 0.1


modes_list = [
	{'Mode':1, 'bw':125000, 'sf':12, 'dec':4, 'r_rate': True},
	{'Mode':2, 'bw':250000, 'sf':12, 'dec':2, 'r_rate': True},
	{'Mode':3, 'bw':125000, 'sf':10, 'dec':4, 'r_rate': False},
    {'Mode':4, 'bw':500000, 'sf':12, 'dec':1, 'r_rate': True},
    {'Mode':5, 'bw':250000, 'sf':10, 'dec':2, 'r_rate': False},
    {'Mode':6, 'bw':500000, 'sf':11, 'dec':1, 'r_rate': True},
    {'Mode':7, 'bw':250000, 'sf':9, 'dec':2, 'r_rate': False},
    {'Mode':8, 'bw':500000, 'sf':9, 'dec':1, 'r_rate': True},
    {'Mode':9, 'bw':500000, 'sf':8, 'dec':1, 'r_rate': True},
    {'Mode':10, 'bw':500000, 'sf':7, 'dec':1, 'r_rate': True},
]


from gnuradio import qtgui

class Receiver(gr.top_block, Qt.QWidget):

    def __init__(self, sf, bw, dec, r_rate):
        gr.top_block.__init__(self, "Decode LoRa packets", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Decode LoRa packets")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "recv")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        # Variables
        self.bw = bw 
        self.sf = sf        
        self.dec = dec
        self.r_rate = r_rate
        self.samp_rate  = 1000000
        self.freq = 866100000

        ##################################################
        # Blocks
        ##################################################
        self.qtgui_sink_x_0 = qtgui.sink_c(
            512, #fftsize
            window.WIN_HAMMING, #wintype
            self.freq, #fc
            1000000, #bw
            "PSD", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            False, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0.set_update_time(1.0/60)
        self._qtgui_sink_x_0_win = sip.wrapinstance(self.qtgui_sink_x_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0.enable_rf_freq(True)

        self.top_layout.addWidget(self._qtgui_sink_x_0_win)
        self.lora_message_socket_sink_0 = lora.message_socket_sink('127.0.0.1', 40868, 0)
        self.lora_lora_receiver_0 = lora.lora_receiver(1e6, self.freq, [self.freq], bw, sf, False, 4, True, self.r_rate, False, dec, False, False)
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('192.168.2.1' if '192.168.2.1' else iio.get_pluto_uri(), [True, True], 32768)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(self.freq)
        self.iio_pluto_source_0.set_samplerate(1000000)
        self.iio_pluto_source_0.set_gain_mode(0, 'manual')
        self.iio_pluto_source_0.set_gain(0, 64)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.lora_lora_receiver_0, 'frames'), (self.lora_message_socket_sink_0, 'in'))
        self.connect((self.iio_pluto_source_0, 0), (self.lora_lora_receiver_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.qtgui_sink_x_0, 0))
    


# Thread Change Mode
def decoder():
    # Create a Socket
    socket_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_fd.setblocking(False)
    socket_fd.bind((localIP, checkModePort))


    while True:
        readable, _, _ = select.select([socket_fd], [], [], TIMEOUT)
        if EXIT:
            exit()

        if socket_fd not in readable:
            continue
            
        data, _ = socket_fd.recvfrom(bufferSize)
        message = "Error"
        print(data)
        try:
            message = data.split(b')')[-1].split(b'\x00')[0].decode()
            print(f'The message is: \033[93m{message}\033[0m')
        except:
            try:
                message1 = data.split(b'\x00')[-1]
                message2 = data.split(b'\x00')[-2]
                if len(message1) > 5:
                    print(f'The message is: \033[91m{message1}\033[0m')
                else:
                    print(f'The message is: \033[91m{message2}\033[0m')
            except:
                pass


def check_valid_Mode(mode):
    if mode < 1 or mode > 10:
        print("\033[31margv[1] must be the number of the Mode\033[0m")
        for i in range (len(modes_list)):
            Mode = modes_list[i]['Mode']
            sf = modes_list[i]['sf']
            bw = modes_list[i]['bw']
            print(f'Mode: {Mode} (sf: {sf} bw: {bw})')

        exit()



def main(top_block_cls=Receiver, options=None):
    global EXIT
    if len(sys.argv) != 2:
        check_valid_Mode(0)
        
    mode = int(sys.argv[1])
    
    #Check if Mode is Valid
    check_valid_Mode(mode)

    bw  = modes_list[mode-1]['bw']
    sf = modes_list[mode-1]['sf']
    dec = modes_list[mode-1]['dec']
    r_rate = modes_list[mode-1]['r_rate']

    Thread_decoder = Thread(target = decoder)

    # Start Threads
    Thread_decoder.start()


    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(sf, bw, dec, r_rate)

    tb.start()


    print(f'\033[32m-------------- MODE {mode} ---------------')
    print(f'Speading Factor: {sf} Bandwidth: {bw}')
    print('-------------------------------------\033[0m')

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()
    EXIT = True
    Thread_decoder.join()


if __name__ == '__main__':
    main()
