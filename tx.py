
#1. Get data from upper layer 
"""""
with open(r"/home/fberfber/Desktop/sometext.txt","rb") as f:
    file_content = f.read()
#--------------------------------------------------------------------

#2. perform lzma compression
import lzma
rawcomp = lzma.compress(file_content)
print("Compression Rate: %d/%d = %f"%(len(rawcomp),len(file_content),len(rawcomp)/len(file_content)))
#--------------------------------------------------------------------

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
    send(50,"0001011011101111"*100)
