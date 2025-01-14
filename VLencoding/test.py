from collections import Counter
import math
def entropy(symbols: dict):
	E = 0
	N =sum(symbols.values())
	for s in symbols.values():
		pi = s/N
		E  += -(pi * math.log(pi,2))
	
	return E
def expected_L(symbols: dict):
	N =sum(symbols.values())
	L = 0
	i = 0
	for n in symbols.values():
	
		pi = n/N
		L += pi * (i+2)
		i+=1
	return L
def VL4encode(dataTx_bits):
	print("Variable length 2-bit encoding")
	print("- - - - - - - - - - - - - - - - - ")
	frequencies = []
	for m in range(0,len(dataTx_bits), 2):
		twins =  int(dataTx_bits[m: m +2], 2)
		frequencies.append(twins)
	frequency_dict = dict(Counter(frequencies))
	symb_dict = {key: frequency_dict[key] for key in sorted(frequency_dict.keys())}
	sorted_dict = dict(sorted(frequency_dict.items(), key=lambda item: item[1], reverse=True))
	e2= entropy(sorted_dict)
	l2 = expected_L(sorted_dict)
	e1 = entropy(symb_dict)
	l1 = expected_L(symb_dict)

	c = 1
	send_raw = sorted_dict
	for key in sorted_dict:
		sorted_dict[key]="0"+c*"1"
		c+=1
	encoding =sorted_dict
	print("Encoding	: ", {key: encoding[key] for key in sorted(encoding.keys())})
	print("Initial expected length  l1 : ", l1)
	print("Adjusted expected length l2 : ", l2)
	print("Expected Length Ratio: l2/l1: ", l2/l1)
	print("- - - - - - - - - - - - - - - - - ")
	return encoding, send_raw

word = "Hellenic Airforce Academy"
dataTx = word.encode("utf-8")
dataTx_bits = ''.join(format(byte, '08b') for byte in dataTx)
# Reed Solomon Encoding _____________________________________!
from reedsolo import RSCodec 
import numpy as np
k 	= len(dataTx)
t 	= int(np.around(0.3*k))	#for 30% packet loss 
n 	= k + 2*t
rsc = RSCodec(n - k) 		#nsyn ---> nsyn/2 : the capacity of the algorithm for total number of error corrections
enc = rsc.encode(dataTx)
#_____________________________________!

dataTx_bits = ''.join(format(byte, '08b') for byte in enc)
encoding , send_raw = VL4encode(dataTx_bits)
send_enc = {key: send_raw[key] for key in sorted(send_raw.keys())}	# forms the symbol encoding header sequence
codec_bits = "1" 
nsyn= bin(n-k)[2:].zfill(8)

#Transmit the RS encoding-decoding size (nsyn)_____________________________________!
for m in range(0,len(nsyn),8):
	ms1 =  encoding[int(nsyn[m: m +2], 2)]
	ms2 =  encoding[int(nsyn[m+2: m +4], 2)]
	ls1 =  encoding[int(nsyn[m+4 : m +6], 2)]
	ls2 =  encoding[int(nsyn[m+6 : m +8], 2)]
	codec_bits += "0" + ms1 +ms2 + ls1 + ls2
codec_bits += "001"+"0"*20+"1"+codec_bits[1:] +"001"+"0"*20+"10"
#_____________________________________!

#Transmit the the symbol encoding header sequence _____________________________________!
symbol_bits = ""
for symbol_encoding in send_enc.values():
	symbol_bits+= symbol_encoding
symbol_bits += "001"+"0"*20+"10"+symbol_bits +"001"+"0"*20+"1"
#_____________________________________!
data_bits = ""
#Transmit the data packets _____________________________________!
for m in range(0,len(dataTx_bits), 8):
	
	ms1 =  encoding[int(dataTx_bits[m: m +2], 2)]
	ms2 =  encoding[int(dataTx_bits[m+2: m +4], 2)]
	ls1 =  encoding[int(dataTx_bits[m+4 : m +6], 2)]
	ls2 =  encoding[int(dataTx_bits[m+6 : m +8], 2)]
	data_bits += "0" + ms1 +ms2 + ls1 + ls2
#_____________________________________!
#Final bitstream formation 
bits = codec_bits + symbol_bits + data_bits
bits+="001"
print("Message transmitted: ",word)
print(int(len(dataTx_bits)/8), " bytes")
from tx import send 

#x = input("send")
#send(56,bits)

