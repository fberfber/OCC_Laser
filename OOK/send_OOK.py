from collections import Counter
import math
import time
from reedsolo import RSCodec 
import numpy as np
from tx import send 
import lzma
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
	#Count the occurences of each 2-bit sequence 
	frequency_dict = dict(Counter(frequencies))
	print("occurences ",frequency_dict)
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
	print(encoding)
	print("Encoding	: ", {key: encoding[key] for key in sorted(encoding.keys())})
	print("Initial expected length  l1 : ", l1)
	print("Adjusted expected length l2 : ", l2)
	print("Expected Length Ratio: l2/l1: ", l2/l1)
	print("- - - - - - - - - - - - - - - - - ")
	return encoding, send_raw

with open(r"/home/fberfber/Desktop/satelite_image.jpg","rb") as f:
    
	
	file_content = f.read()

#--------------------------------------------------------------------

#2. perform lzma compression

rawcomp = lzma.compress(file_content, preset = 9)
print("Compression Rate: %d/%d = %f"%(len(rawcomp),len(file_content),len(rawcomp)/len(file_content)))
#words = ["@On-Off Keying Modulation - OCC experimental setup@", "CC experimental setup", "Department of Aeronautical Studies"]
words = ["@Επίσημη Δοκιμή@","Ανάπτυξη Συστήματος FSO", "Διαμόρφωση: On-Off Keying - ΟΟΚ", "Σχολή Ικάρων","Αεροπορική Βάση Δεκέλειας" ,"@Τερματισμός Δοκιμής@"]

for i,w in enumerate(words):
	print(f"Message {i}:"," ",w)
y = input("Initiate")
gap  = "1000000001"
messages = []
length = 0
for word in words:
	dataTx = word.encode('utf-8')
	k = len(dataTx)
	t 	= int(np.ceil(0.4*k))	#for 40% packet loss 
	n 	= k + 2*t



	rsc = RSCodec(n-k) 		#nsyn ---> nsyn/2 : the capacity of the algorithm for total number of error corrections
	enc = rsc.encode(dataTx)
	nsym = n - k
	#_____________________________________!

	dataTx_bits = ''.join(format(byte, '08b') for byte in enc)

	codec_bits = "1" 
	nsyn= format(nsym, '08b')
	#Transmit the RS encoding-decoding size (nsyn)_____________________________________!

	bits =gap+nsyn+gap+nsyn+gap

	for i in range(0,len(dataTx_bits),8):
		print(int(i/8), " : ", dataTx_bits[i:i+8])
		bits+=dataTx_bits[i:i+8]+gap
	messages.append(bits)

	L = int(np.ceil(len(bits)))
	length += L
L_bits = format(length, '016b')


init_bits = gap+L_bits[0:8]+gap+L_bits[0:8]+gap+L_bits[8:16]+gap+L_bits[8:16]+"1"
send(108, init_bits)
duration = 0 

for m in messages:
	t0 = time.time()

	send(108, m)

	duration+=time.time()-t0
print("Loaded data after ",np.around(duration,3), " seconds")
y = input("Type anything to proceed ")

send(108,'1')

