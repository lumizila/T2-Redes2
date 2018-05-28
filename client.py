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
    print("Welcome to the calculator Client! Type 'quit' to quit the program.")
    print("To make a calculation, type a reverse polish math expression,\nfor example 5+3 becomes 5 3 +")
    message = input("Please write your expression(or quit): ")
    if(message != "quit"):
        message = "CM" + message
        print(message)
        try:
            # Send data to the multicast group
            sent = sock.sendto(message.encode(), multicast_group)
            print('sending: ', message)

            # Look for responses from all recipients
            while True:
                print('waiting to receive')
                try:
                    data, server = sock.recvfrom(16)
                except socket.timeout:
                    print('timed out, no more responses')
                    break
                else:
                    print('received: ', data.decode(
                        'utf-8'), ' from: ', server)
                    break
        except:
            print("in except")
            pass
print('closing socket')
sock.close()
