import gnuradio.lora_sdr as lora_sdr
from gnuradio.filter import firdes
from gnuradio import blocks
from gnuradio import iio
from gnuradio import gr
import pmt
import sys

modes_list = [
	{'Mode':1, 'bw':125000, 'sf':12},
	{'Mode':2, 'bw':250000, 'sf':12},
	{'Mode':3, 'bw':125000, 'sf':10},
    {'Mode':4, 'bw':500000, 'sf':12},
    {'Mode':5, 'bw':250000, 'sf':10},
    {'Mode':6, 'bw':500000, 'sf':11},
    {'Mode':7, 'bw':250000, 'sf':9},
    {'Mode':8, 'bw':500000, 'sf':9},
    {'Mode':9, 'bw':500000, 'sf':8},
    {'Mode':10, 'bw':500000, 'sf':7},
]


class TX(gr.top_block):

    def __init__(self, bw, sf):
        gr.top_block.__init__(self, "Transmit LoRa packets", catch_exceptions=True)
        
        # Variables
        self.sf = sf
        self.samp_rate = samp_rate = 1000000
        self.freq = freq = 866100000
        self.bw = bw

        # Blocks
        self.lora_tx_0 = lora_sdr.lora_sdr_lora_tx(
            bw=self.bw,
            cr=1,
            has_crc=True,
            impl_head=False,
            samp_rate=self.samp_rate,
            sf=self.sf,
         ldro_mode=2,frame_zero_padd=1280 )
        self.iio_pluto_sink_0 = iio.fmcomms2_sink_fc32('192.168.2.1' if '192.168.2.1' else iio.get_pluto_uri(), [True, True], 32768, False)
        self.iio_pluto_sink_0.set_len_tag_key('')
        self.iio_pluto_sink_0.set_bandwidth(20000000)
        self.iio_pluto_sink_0.set_frequency(freq)
        self.iio_pluto_sink_0.set_samplerate(samp_rate)
        self.iio_pluto_sink_0.set_attenuation(0, 10)
        self.iio_pluto_sink_0.set_filter_params('Auto', '', 0, 0)
        self.blocks_message_strobe_0_0_0 = blocks.message_strobe(pmt.intern("    Nitlab_Ping"), 5000)


        # Connections
        self.msg_connect((self.blocks_message_strobe_0_0_0, 'strobe'), (self.lora_tx_0, 'in'))
        self.connect((self.lora_tx_0, 0), (self.iio_pluto_sink_0, 0))


   
def check_valid_Mode(mode):
    if mode < 1 or mode > 10:
        print("\033[31margv[1] must be the number of the Mode\033[0m")
        for i in range (len(modes_list)):
            Mode = modes_list[i]['Mode']
            sf = modes_list[i]['sf']
            bw = modes_list[i]['bw']
            print(f'Mode: {Mode} (sf: {sf} bw: {bw})')

        exit()

def main():
    global EXIT
    if len(sys.argv) != 2:
        check_valid_Mode(0)
        
    mode = int(sys.argv[1])
    
    #Check if Mode is Valid
    check_valid_Mode(mode)

    bw  = modes_list[mode-1]['bw']
    sf = modes_list[mode-1]['sf']
    
    tb = TX(bw, sf)
    tb.start()

    input()

    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
