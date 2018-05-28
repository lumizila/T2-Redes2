#!/usr/bin/python3
import socket
import struct
import sys
import threading
from time import sleep
from datetime import datetime, date
from collections import OrderedDict


def send_hearbeat(sockhp):

    print("Heartbeat started")
    message = 'SM-Heartbeat'

    multicast_group1 = ('224.3.29.71', 10000)

    while True:
        try:
           # Send data to the multicast group
            sent = sockhp.sendto(message.encode(), multicast_group1)

        except:
            print("Could not send heartbeat")
            pass

        sleep(10)


def election(tabelaServidores):
    timenow = datetime.now().time()
    for key in tabelaServidores:
        timedelta = datetime.combine(
            date.today(), timenow) - datetime.combine(date.today(), tabelaServidores[key])
        print(key + " last update was: " +
              str(timedelta.seconds) + " seconds ago")
        if(timedelta.total_seconds() > 40):
            print("Removing " + key + " from table")
            del tabelaServidores[key]
        else:
            print(key + " still able to run")


def update_heartbeat(address, tabelaServidores):
    if(str(address) in tabelaServidores):
        print("Updating Heartbeat table from: " +
              str(address) + " at " + str(datetime.now().time()))
        tabelaServidores.update({str(address): datetime.now().time()})
    else:
        print("Adding new server to table: ", address)
        tabelaServidores.update({str(address): datetime.now().time()})
        tabelaServidores = OrderedDict(
            sorted(tabelaServidores.items(), key=lambda x: x[0]))

    print("Calling election")
    election(tabelaServidores)


def main():

    # Create the datagram socket
    sockhp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 2)
    sockhp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    # iniciando tabela de servidores
    tabelaServidores = OrderedDict(
        {socket.gethostbyname(socket.gethostname()): datetime.now().time()})
    print(tabelaServidores.items())
    hb = threading.Thread(target=send_hearbeat, args=(sockhp,))
    hb.start()

    #### SERVER ####
    multicast_group = '224.3.29.71'
    server_address = ('', 10000)

    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind to the server address
    sock.bind(server_address)

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Receive/respond loop
    while True:
        print('waiting to receive message')
        data, address = sock.recvfrom(1024)
        print('Received message: ' + data.decode('utf-8'))
        #print('received ' + str(len(data)) + ' bytes from ' + str(address))
        if(data[:2].decode('utf-8') == 'SM'):
            update_heartbeat(address[0], tabelaServidores)

        elif(data[:2].decode('utf-8') == 'CM'):
            print(tabelaServidores.items()[0])
            if(socket.gethostbyname(socket.gethostname()) == list(tabelaServidores.items())[0][0]):
                print('sending acknowledgement to', address)
                sock.sendto('ack'.encode(), address)
            else:
                print("I am not the chosen one")

    hb.join()
    print('closing Heartbeat')
    sockhp.close()

    print('closing socket')
    sock.close()

if __name__ == "__main__":
    main()
