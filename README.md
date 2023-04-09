# Receive and Transmit LoRa packets

## Prerequisites

- Python 3
- GnuRadio
- https://github.com/rpp0/gr-lora (Receivers)
- https://github.com/tapparelj/gr-lora_sdr (Transmitter)


## How to Run

### Run Receiver
python3 Receiver.py {mode}

### Run Receiver_with_sink
python3 Receiver_with_sink.py {mode}

### Run Dynamic_Receiver
python3 Dynamic_Receiver.py

### Run Transmitter
python3 Transmitter.py {mode}

Which {mode} is a number between 1 and 10 and describes which mode the scripts will use.
