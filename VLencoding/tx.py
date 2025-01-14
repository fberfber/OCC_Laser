"""""
#1. Get data from upper layer 
with open(r"/home/fberfber/Desktop/sometext.txt","rb") as f:
    file_content = f.read()
#--------------------------------------------------------------------

#2. perform lzma compression
import lzma
rawcomp = lzma.compress(file_content)
print("Compression Rate: %d/%d = %f"%(len(rawcomp),len(file_content),len(rawcomp)/len(file_content)))
#--------------------------------------------------------------------

#3. Perform Solomon-Reed error correction algorithm
from reedsolo import RSCodec 
import numpy as np
k = len(rawcomp)
print(k)
t = int(np.around(0.5*k))
n = k + 2*t

rsc = RSCodec(n - k) #nsyn ---> nsyn/2 : the capacity of the algorithm for total number of error corrections
enc = rsc.encode(rawcomp)
dec = rsc.decode(enc)[0]
if dec == rawcomp :
    print("Succesful encoding-decoding")
else:
    print("Error: Decoded message does not match the encoded message")
print("Effective Compression Rate: %d/%d = %f"%(len(enc),len(file_content),len(enc)/len(file_content)))

#4. Send to Esp32 for transmission

# Data to send

def access_bit(data, num):
    base = int(num // 8)
    shift = int(num % 8)
    return (data[base] >> shift) & 0x1
data = enc
bits = [access_bit(data,i) for i in range(len(data)*8)]
data = bits
data_chars  = [str(i) for i in data]
data = ''

for c in data_chars:
    data += c
"""


import requests
def send(pulse_duration, data):

    esp32_server_url_Send = "http://192.168.0.56/Send"
    esp32_server_url_Setup = "http://192.168.0.56/Setup"
    esp32_server_url_Start = "http://192.168.0.56/Start"
    url_with_params_send = f"{esp32_server_url_Send}?data={data}"
    url_with_params_setup = f"{esp32_server_url_Setup}?data={pulse_duration}"
    url_with_params_start = f"{esp32_server_url_Start}"
    try:
        # Sending the Get request
        response = requests.get(url_with_params_setup)
        print(response)
        print("Response from ESP32:", response.text)

    except requests.exceptions.RequestException as e:
        print("Error connecting to ESP32:", e)
    try:
        # Sending the Get request
        response = requests.get(url_with_params_send)
        print(response)
        print("Response from ESP32:", response.text)

    except requests.exceptions.RequestException as e:
        print("Error connecting to ESP32:", e)
    return response.text
if __name__ == "__main__":
    send(56,"0101"*100)
