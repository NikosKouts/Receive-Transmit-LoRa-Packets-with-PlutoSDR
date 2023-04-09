from gnuradio.eng_arg import eng_float, intx
from gnuradio.filter import firdes
from gnuradio import iio
from gnuradio import gr
from threading import *
import socket
import select
import lora
import time
import sys

#Global Variables
localIP     = "127.0.0.1"
controlerPort   = 4000
checkModePort   = 40868
bufferSize  = 1024
TIMEOUT = 0.1
TRIES = 150

EXIT = False

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


class Receiver(gr.top_block):
    def __init__(self, bw , sf, dec, r_rate):
        gr.top_block.__init__(self, "Decode LoRa packets")
        
        # Variables
        self.bw = bw 
        self.sf = sf        
        self.dec = dec
        self.r_rate = r_rate
        self.samp_rate  = 1000000
        self.freq = 866100000
       
        # Blocks
        self.lora_message_socket_sink_0 = lora.message_socket_sink('127.0.0.1', 40868, 0)
        self.lora_lora_receiver_0 = lora.lora_receiver(self.samp_rate, self.freq, [self.freq], bw, sf, False, 4, True, self.r_rate, False, dec, False, False)
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('192.168.2.1' if '192.168.2.1' else iio.get_pluto_uri(), [True, True], 32768)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(self.freq)
        self.iio_pluto_source_0.set_samplerate(self.samp_rate)
        self.iio_pluto_source_0.set_gain_mode(0, 'manual')
        self.iio_pluto_source_0.set_gain(0, 64)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)

        # Connections
        self.msg_connect((self.lora_lora_receiver_0, 'frames'), (self.lora_message_socket_sink_0, 'in'))
        self.connect((self.iio_pluto_source_0, 0), (self.lora_lora_receiver_0, 0))



# Thread Change Mode
def decoder():
    # Create a Socket
    socket_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_fd.setblocking(False)
    socket_fd.bind((localIP, checkModePort))


    while True:
        readable, _, _ = select.select([socket_fd], [], [], TIMEOUT)
        if EXIT:
            return()

        if socket_fd not in readable:
            continue
            
        data, _ = socket_fd.recvfrom(bufferSize)
        message = "Error"

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



def main(top_block_cls=Receiver):
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

 
    print(f'\033[32m-------------- MODE {mode} ---------------')
    print(f'Bandwidth: {bw} Speading Factor: {sf}')
    print('-------------------------------------\033[0m')

    tb = Receiver(bw, sf, dec, r_rate)
    tb.start()    

    input()
    EXIT = True

    tb.stop()
    tb.wait()

    Thread_decoder.join()
    

if __name__ == '__main__':
    main()
