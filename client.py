import socket
import struct
import sys

multicast_group = ('224.3.29.71', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
sock.settimeout(0.2)

# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

message = "start"
while(message != "quit"):
    print("-----------------------------//--------------------------------")
    print("Welcome to the calculator Client! Type 'quit' to quit the program.")
    print("To make a calculation, type a reverse polish math expression,\nfor example 5+3 becomes 5 3 +")
    print("-----------------------------//--------------------------------") 
    message = input("Please write your expression(or quit): ")
    if(message != "quit"):
        message = "CM" + message
        print(message)
        if(message == ""):
            print("ERROR: The message can not be empty.")
        else:  
            try:
                # Send data to the multicast group
                sent = sock.sendto(message.encode(), multicast_group)
                print('Sending math expression: ', message)

                # Look for responses from all recipients
                while True:
                    print('Waiting to receive answer')
                    try:
                        data, server = sock.recvfrom(64)
                    except socket.timeout:
                        print('ERROR: timed out, no more responses')
                        break
                    else:
                        print('Received message: "', data.decode(
                            'utf-8'), '" from: ', server)
                        print("RESULT:\n"+message[2:]+" = "+data.decode('utf-8'))
                        break
            except:
                print("Could not send message through socket")
                pass
print('Closing client socket')
sock.close()
