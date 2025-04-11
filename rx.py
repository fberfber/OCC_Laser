import numpy as np
import cv2
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
from matplotlib.pyplot import plot as plot
from matplotlib.pyplot import show as show
from matplotlib.pyplot import scatter as scatter
from matplotlib.pyplot import figure as figure
from pathlib import Path
from reedsolo import RSCodec 
# Path to the folder
folder_path = Path("/home/fberfber/Desktop/app/final/OCCTrials10012025/paritycheck")

# Count the number of files in the folder
num_files = len([f for f in folder_path.iterdir() if f.is_file()])


#This is a trial for testing the perfomance of the modulation scheme, with error correction implemented. 

packets = [ ]
handshake = []
lost_bytes = 0
cutoffs = []
first = True
def get_handshake(path :str, show_me = False):
    split_20 =np.asarray([])
    num_files = len([f for f in Path(path).iterdir() if f.is_file()])
    handshake = []
    for file in range(num_files):
        
        img = cv2.imread(Path(path+"/frame"+str(file)+".png"))
        img = cv2.GaussianBlur(img, (1,3),sigmaX=0, sigmaY=0)
        blue, green, r= cv2.split(img)
        output = np.mean(r, axis =1)

        #EDGE ZEROS CORRECTION 
        copy_output = output
        copy_output[copy_output<2] = 0
        if copy_output[0]==0:
            copy_output [0]=255
        if copy_output[-1]==0:
            copy_output[-1] =255
        #_______________________________________!
        # SYMBOL SEPERATION SEPERATION
        headers, _ = find_peaks(-output,distance =12, prominence=6) 
        headers = np.asarray([i for i in headers if (4> output[i] ) ] )
        #_______________________________________!
        # HANDSHAKING SEQUENCIES SEPERATION
        if split_20.size>0:
            split_20_last = split_20[-1]
        split_20 , _ = find_peaks(-copy_output,distance =100,plateau_size = (20,864)) 

        if split_20.size==0 and len(handshake)>0:
            return handshake, [file-1, split_20_last] #Marks the end of the handshaking
        #_______________________________________!
        for m in range(0,split_20.size,1):
            try:
                x= [ ]
                handshake_sequence = headers[(headers>split_20[m] )& (headers<split_20[m+1])] #get a handshake sequence
                for m in range(len(handshake_sequence)):
                    try:
                        x.append(output[handshake_sequence[m]:handshake_sequence[m+1]]) #get the bytes of the sequence
                    except:
                        handshake.append(x)
                        #The end of the handshake sequencies of the frame is reached
                        pass
            except:
                pass                    
        
        if show_me:
            figure("Handshake Sequences")
            scatter(split_20, output[split_20], color = "black", label = "handshake sequence")
            scatter(handshake_sequence, output[handshake_sequence], color = "red", label = "byte sequence")
            plt.xticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 864], [str(i) for i in [0, 100, 200, 300, 400, 500, 600, 700, 800, 864]])
            plot(output, label ="input signal")
            plt.grid()
            plt.legend(fontsize=15)
            show()
def decode(seq, lost_packets = None, encoding = None,show_me = False):
    """
    <seq>: raw packet data acquired 
    <lost_packets>: the number of the lost packets at each frame transition
    <encoding>: the symbol encoding of the variable length encoding used
    <show_me>: used for data visualization

    """ 
    bits =      [] # here are stored the demodulated packets in a binary string form
    indices =   [] # the indices for seperating the acquired packets from each frame
    for block in seq:
        if block ==1:                       # frame transition, compensating for the lost bytes by marking an erasure
            for i in range(lost_packets[0]):
                indices.append(len(bits)+i) # saving the erasure position
                bits.append("00000000")     # marking the erasure
            lost_packets.pop(0)             
        else:
            for byte in block:

                demodulated_packet=""       # here will be saved the demodulated 8-bit packet 
            
                p = byte
                headers,_ = find_peaks(-p, distance=6, prominence=40)   # marks the symbol transitions 
                p1=headers[0]
                p2= headers[1]
                p3 =headers[2]
                x = [0,p1,p2,p3,len(p)]
                # Symbol decoding {Ti}, i =0,1,2,3 -> {Si}, i=0,1,2,3 
                for i in range(len(x)):
                    try:
                        symbol = p[x[i]:x[i+1]]
                        if i==0:
                            symbol = symbol[symbol>=p[p1]]
                        if i==3:
                            symbol = symbol[symbol>=p[p3]]
                        # Decoding procedure 
                        pixel_height = len(symbol)
                        if encoding: # demodulation with statistical encoding 
                            h = int(round((pixel_height - 12.39)/6.15)) # demodulation with encoding   
                            demodulated_packet += encoding[h]           
                        else:           # demodulation  with simple encoding 
                            period = int(round((pixel_height - 12.39)/6.15)) #from final_length.py 
                            demodulated_packet +=bin(period)[2:].zfill(2)   
                    except:
                        pass
                #______________________________!!
                bits.append(demodulated_packet)
                if show_me:
                    figure("Sequence")
                    plot(p)
                    scatter(headers, p[headers], color = "black")
                    show()
    return bits, indices
def get_encoding(hbits: list):
    
    if len(hbits)<2:
        print("Not enough handshake sequencies")
        return 0
    if len(hbits)==2:
        y= [hbits[1][i:i+2] for i in range(0,8,2)]
        if y.count('00') ==1 and y.count('01')==1 and y.count('10')==1 and y.count('11')==1:
            symbol_bits = hbits[1]
            codec_bits = hbits[0]
        else:
            print("Error at symbol sequence decryption")
            return 0 
    elif len(hbits)==3:
        y1= [hbits[2][i:i+2] for i in range(0,8,2)]
        if y1.count('00') ==1 and y1.count('01')==1 and y1.count('10')==1 and y1.count('11')==1 :
            symbol_bits = hbits[2]
            codec_bits  = hbits[0]
        else:
            print("Error at symbol sequence decryption")
            return 0 
    elif len(hbits)==4:  
        if hbits[2]!=hbits[3] or hbits[0]!=hbits[1]:
            print("Error at sequence decryption")
            return 0 
        else:
            symbol_bits = hbits[4]
            codec_bits  = hbits[0]
    else:
        print("Too many arguments")
        return 0
    duration = [0,1,2,3]
    
    encoding_twins = [symbol_bits[i:i+2] for i in range(0,8,2)]
    s_duration = [bin(duration[i])[2:].zfill(2) for i in range(len(duration))]
    encoding = {int(encoding_twins[i],2): bin(duration[i])[2:].zfill(2) for i in range(len(duration))}
    inv = { encoding_twins[i]:s_duration[i] for i in range(len(encoding_twins))}

    codec = ""
    codec_bits = [codec_bits[i:i+2] for i in range(0,8,2)]
    for twin in codec_bits:
        codec+= inv[twin]
    
    return encoding, int(codec,2)
def get_data(path:str,starting_frame, starting_row, show_me = False):
    """
    <path>: path to your data, <starting_frame>: the frame at which data transmission starts (after the handshaking),
    <starting row>: the pixel row of the frame where transmission starts. <show_me>: used for data visualization 
    Returns the raw packet data and the data describing the packet(=byte) loss that occurs in-between the frames due to the time gap
    """
    raw_packets = []
    loss_data = []
    for file in range(starting_frame, num_files,1):

        #image read, preprocessing
        img = cv2.imread(Path(path+"/frame"+str(file)+".png"))     
        img = cv2.GaussianBlur(img, (1,3),sigmaX=0, sigmaY=0)
        _, _, r= cv2.split(img)
        output = np.mean(r, axis =1)
        #___________________________!

        if file ==starting_frame:
            output = output[starting_row:]
        if file == num_files -1:
            end_row= len(output[output>3])
        # Finds the packet (byte) seperation valleys of the signal
        headers, _ = find_peaks(-output,distance =12, prominence=6) 
        headers = np.asarray([i for i in headers if (4> output[i] ) ] ) #filtering the non data seperation markers 
        #___________________________!
        # Finds the symbol seperation valleys of the signal 
        symbol_peaks, _ = find_peaks(-output,distance =4,height=(-255,-1), prominence=30) 
        #___________________________!

        # Acquiring data for describing the packet loss --!----!------------------!-----------!------
        discarded_rows_up = 0       #counts the rows above the first symbol transmitted
        discarded_symbols_up =0     #counts the last symbols transmitted for the earliest lost packet, at the start of the frame
        discarded_rows_down = 0     #counts the rows below the last symbol transmitted
        discarded_symbols_down =0   #counts the first symbols transmitted for the latest lost packet, at the end of the frame     
        
        if np.average(output[:headers[0]])>3 and file!=starting_frame:      
            #check if there are lost symbols inside the frame       
            discarded_peaks_up      = symbol_peaks[symbol_peaks<headers[0]]
            discarded_rows_up   += symbol_peaks.size
            discarded_symbols_up += discarded_peaks_up.size
        
        if np.average(output[headers[-1]:])>3 and file!=num_files:   
            #check if there are lost symbols inside the frame               
            discarded_peaks_down         = symbol_peaks[symbol_peaks>headers[-1]]
            discarded_symbols_down += discarded_peaks_down.size   
            discarded_rows_down    += int(len(output)- symbol_peaks[-1])
        loss_data.append({"discarded_rows_up": discarded_rows_up,"discarded_symbols_up":discarded_symbols_up,"discarded_rows_down" :discarded_rows_down,"discarded_symbols_down":discarded_symbols_down  })
        #___________________________!
        # Extracts the raw data of the packets acquired inside the frame
        raw_packets_frame = []
        for i , c in enumerate(headers):
            try:
                next = headers[i+1]
                raw_packets_frame.append(output[c:next])
                if show_me:
                    figure("Packet")
                    plot(output[c:next])
                    show()
            except:
                raw_packets.append(raw_packets_frame)
                pass
        #___________________________!   
        # Marks the packet loss in the raw packet data array, used in decoding the data by marking the erasures
        if file!=num_files-1:
            raw_packets.append(1) 
        #___________________________! 
        #data visualization   
        if show_me:
            plt.figure("Data Sequences")
            plot(output)
            if file!=num_files:
                scatter(discarded_peaks_down, output[discarded_peaks_down],color = "red")
            if file!=starting_frame:
                scatter(discarded_peaks_up, output[discarded_peaks_up],color = "red")
            scatter(headers, output[headers],color = "green")
            show()
        #___________________________!       
    return raw_packets, loss_data, end_row
def get_packet_loss(loss_data:dict):
    """
    Calculates the number (1 or 2) of packets that are disrupted at the frame transition caused due to the guard time.
    """
    gap = []
    c = 0
    for dict in loss_data:
        gap.append(dict["discarded_symbols_up"])    
        gap.append(dict["discarded_symbols_down"])
    packets_lost=[]
    start = 1
    for i , val in enumerate(gap[1:len(gap)-1:2]):
        i = start +i*2
        try:
            valnext = gap[i+1]
        except:
            break
        if valnext + val >=3:
            packets_lost.append(2)
        else:
            packets_lost.append(1)
    return packets_lost
def compare(data, nsyn):
    """
    Gives the expected 8-bit sequence of the reed solomon (nsyn errors) encoding
    """
    rsc = RSCodec(nsyn) #nsyn ---> nsyn/2 : the capacity of the algorithm for total number of error corrections
    enc = rsc.encode(data)
    dataTx_bits = ''.join(format(byte, '08b') for byte in enc)
    expected = [dataTx_bits[i:i+8] for i in range(0,len(dataTx_bits),8)]
def data_rate(starting_frame,starting_row, end_row):
    Dt = (864-starting_row)*9                     # 9us = rd = readout time
    for i in range(starting_frame+1, num_files-1):    
        Dt += 8324                            # tg = 521us = guard time, tf = 8324 = frame duration 
    Dt += end_row*9
    return Dt


# Acquire the handshake sequencies 
hseq, pos   = get_handshake("/home/fberfber/Desktop/app/final/OCCTrials10012025/paritycheck")
hbits       = decode(hseq)[0]
print(hbits)
#______________________________________________________________________________________________________________!
# Retrieve the symbol encoding and the Reed Solomon nsyn parameter
encoding, nsyn  = get_encoding(hbits)
#______________________________________________________________________________________________________________!
# Extract the raw packet data and acquire the packet loss data that describe the number of packets lost
raw_packets, loss_data, end_row     = get_data("/home/fberfber/Desktop/app/final/OCCTrials10012025/paritycheck", pos[0], pos[1])
lost_packets                        = get_packet_loss(loss_data)
# Decode the raw packet data to their 8-bit packet form
pbits, indices  = decode(raw_packets,lost_packets, encoding)
#______________________________________________________________________________________________________________!

rsc = RSCodec(nsyn) #nsyn ---> nsyn/2 : the capacity of the algorithm for total number of error corrections / nsyn: Erasures 
""" # for comparing with the expected result 

word = "Hellenic Airforce Academy"
dataTx = word.encode("utf-8")
expected = compare(dataTx, nsyn)
"""
bytes = bytearray()
for block in pbits:
    bytes.append(int(block,2))
try:

    output = rsc.decode(bytes, erase_pos=indices)
except:
    print("Failede to decode")
"""
for i , y in enumerate(pbits):
    try:
        print(i, y, expected[i])
    except:
        print(i, y, "         ")
"""

print("Monday, 13/01/2025")
print("________________________")
print("Variable length encoding scheme")
print(f"Number of files processed   : {num_files}")
print("Bytes received               : ", len(pbits))
for i,key in enumerate(list(encoding.keys())):
    val = "0"+ (key+1)*"1"
    encoding[val] = encoding.pop(key)

print("Encoding scheme      : ", encoding)
print("Data rate            : ", np.around((len(pbits)/data_rate(pos[0],pos[1], end_row))*1e3,3)," kB/s")
print("Data rate    (bits/s): ", np.around((len(pbits)/data_rate(pos[0],pos[1], end_row))*1e3*8,3)," kbit/s")
print("Data rate (pre error corrrection) : ", np.around(((len(pbits)+16)/data_rate(pos[0],pos[1], end_row))*1e3*8,3)," kbit/s")
print("________________________")
print("Message received     : ", output[0].decode("utf-8"))

  
