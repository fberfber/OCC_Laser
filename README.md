# OCC_Laser <br>
Optical Camera Communications (OCC) Project - Laser transmitter <br>
Hardware: 
-> Raspberry Pi5 5
-> RPi cam module 3 wide - 120fps
-> Esp32 Wrover kit module (Wifi connectivity)
Jan 9, 2025 <br>
1)final_length.py : Calibration of the pixel heights of the {1T, 2T, 3T, 4T} sequencies <br>
2)final_readoutcalibration: Calibration of the readout rate (pixel rows read / 1e-6s) and the guard time between frames <br>
3)final_rx.py: Signal processing and demodulation of an input frame that encodes the message "check" (10.588kb/s - Pre-error correction ).
Jan 14, 2025 <br>
A variable length 2-bit encoding is implemented with Reed Solomon error correction code for longer text messages. A data rate of ~10kbps 
with error correction was achieved with successful decoding.
