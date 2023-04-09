from gnuradio.eng_arg import eng_float, intx
from gnuradio.filter import firdes
from gnuradio import iio
from gnuradio import gr
from threading import *
import socket
import select
import lora
import time

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

class RX(gr.top_block):
    def __init__(self, bw , sf, dec, r_rate):
        gr.top_block.__init__(self, "Decode LoRa packets")
        
        # Variables
        self.bw = bw 
        self.sf = sf        
        self.dec = dec
        self.r_rate = r_rate
        self.samp_rate  = 1000000
        self.freq = 866100000
        self.pluto_buffer = 32768
       
        # Blocks

        # Message Sink Block
        self.lora_message_socket_sink_0 = lora.message_socket_sink('127.0.0.1', 40868, 0)

        # LoRa Receive Block
        self.lora_lora_receiver_0 = lora.lora_receiver(self.samp_rate, self.freq, [self.freq], bw, sf, False, 4, True, self.r_rate, False, dec, False, False)
       
        # Pluto Source Block
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('192.168.2.1' if '192.168.2.1' else iio.get_pluto_uri(), [True, True],  self.pluto_buffer)
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
def check_mode():
    # Create a Poll Socket
    socket_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_fd.setblocking(False)
    socket_fd.bind((localIP, checkModePort))

    # Controller's Contact Information
    controlerAddress = (localIP, controlerPort)

    time.sleep(1)

    while(True):
        index = 0
        while index < TRIES:
            readable, _, _ = select.select([socket_fd], [], [], TIMEOUT)
            if EXIT:
                msgToControler = "EXIT"
                socket_fd.sendto(msgToControler.encode(), controlerAddress)
                exit()

            if socket_fd not in readable:
                index = index + 1
                continue
            
            data, _ = socket_fd.recvfrom(bufferSize)
            index = 0
            text = "Error"

            try:
                text = data.split(b')')[-1].split(b'\x00')[0].decode()
                print(f'The message is: \033[93m{text}\033[0m')
            except:
                try:
                    text1 = data.split(b'\x00')[-1]
                    text2 = data.split(b'\x00')[-2]
                    if len(text1) > 5:
                        print(f'The message is: \033[91m{text1}\033[0m')
                    else:
                        print(f'The message is: \033[91m{text2}\033[0m')
                except:
                    pass

    
                

        msgToControler = "CHANGE MODE"
        print(f'\033[31m{msgToControler}\033[0m')
        socket_fd.sendto(msgToControler.encode(), controlerAddress)


# Thread controler
def controller():  
   
    # Create Socket
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((localIP, controlerPort))

    while True:
        for i in range(len(modes_list)):
            # Mode's Variables
            mode = modes_list[i]['Mode']
            bw = modes_list[i]['bw']
            sf = modes_list[i]['sf']
            dec = modes_list[i]['dec']
            r_rate = modes_list[i]['r_rate']
         
            print(f'\033[32m-------------- MODE {mode} ---------------')
            print(f'Bandwidth: {bw} Speading Factor: {sf}')
            print('-------------------------------------\033[0m')
            
            # Initialize and Start RX block
            tb =  None
            tb = RX(bw, sf, dec, r_rate)
            tb.start()    

            # Receive from Check_modes Thread
            data, _ = UDPServerSocket.recvfrom(bufferSize)
            data = data.decode('UTF-8')


            tb.stop()
            tb.wait()

            if data == "EXIT":
                exit()
            
            time.sleep(0.5)


def main():
    global EXIT

    # Creating Threads
    Thread_check_mode = Thread(target = check_mode)
    Thread_controler = Thread(target = controller)

    # Start Threads
    Thread_check_mode.start()
    Thread_controler.start()  

    input()
    EXIT = True

    Thread_check_mode.join()
    Thread_controler.join()

if __name__ == '__main__':
    main()
