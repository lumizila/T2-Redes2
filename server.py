#!/usr/bin/python3
import socket
import struct
import sys
import threading
from time import sleep
from datetime import datetime, date
from collections import OrderedDict

ops = {
  "+": (lambda a, b: a + b),
  "-": (lambda a, b: a - b),
  "*": (lambda a, b: a * b),
  "/": (lambda a, b: a / b)
}

def eval(expression):
  tokens = expression.split()
  stack = []

  for token in tokens:
    if token in ops:
      arg2 = stack.pop()
      arg1 = stack.pop()
      result = ops[token](arg1, arg2)
      stack.append(result)
    else:
      stack.append(int(token))

  return stack.pop()

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
    keys = []
    for key in tabelaServidores:
        timedelta = datetime.combine(
            date.today(), timenow) - datetime.combine(date.today(), tabelaServidores[key])
        print(key + " last update was: " +
              str(timedelta.seconds) + " seconds ago")
        if(timedelta.total_seconds() > 40):
            keys.append(key)
        else:
            print(key + " still able to run")
    #This for is necessary cause, when you delete during a interaction  causes:
    #RuntimeError: OrderedDict mutated during iteration
    for key in keys:
        print("Removing " + key + " from table")
        del tabelaServidores[key]

    return tabelaServidores

def update_heartbeat(address, tabelaServidores,counter):
    if(str(address) in tabelaServidores):
        print("Updating Heartbeat table from: " +
              str(address) + " at " + str(datetime.now().time()))
        tabelaServidores.update({str(address): datetime.now().time()})
    else:
        print("Adding new server to table: ", address)
        tabelaServidores.update({str(address): datetime.now().time()})
        tabelaServidores = OrderedDict(
            sorted(tabelaServidores.items(), key=lambda x: x[0]))
    if(counter == 0):
        print("Calling election")
        tabelaServidores = election(tabelaServidores)
    return tabelaServidores

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
    counter = 0
    # Receive/respond loop
    while True:
        print('waiting to receive message')
        data, address = sock.recvfrom(1024)
        print('Received message: ' + data.decode('utf-8'))
        #print('received ' + str(len(data)) + ' bytes from ' + str(address))
        if(data[:2].decode('utf-8') == 'SM'):
            tabelaServidores = update_heartbeat(address[0], tabelaServidores, counter)
            counter = (counter + 1)% (len(tabelaServidores)*4)
        elif(data[:2].decode('utf-8') == 'CM'):
            if(socket.gethostbyname(socket.gethostname()) == list(tabelaServidores.items())[0][0]):
                print(data[-2:].decode('utf-8'))
                print(str(eval(data[-2:].decode('utf-8')))
                sys.exit(0)
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
