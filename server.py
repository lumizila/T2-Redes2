#!/usr/bin/python3
import socket
import struct
import sys
import threading
from time import sleep
import datetime
from collections import OrderedDict

def send_hearbeat():

  multicast_group = ('224.3.29.71', 10000)

  # Create the datagram socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Set the time-to-live for messages to 1 so they do not go past the
  # local network segment.
  ttl = struct.pack('b', 1)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
  print("Heartbeat started")
  message = 'SM-Heartbeat';
 
  while True:
    try:
   # Send data to the multicast group
      print ('sending: ', message)
      sent = sock.sendto(message, multicast_group)

    except:
      pass

    sleep(5)

  print ('closing Heartbeat')
  sock.close()


def main():
  #iniciando tabela de servidores
  tabelaServidores = OrderedDict({socket.gethostbyname(socket.gethostname()): datetime.datetime.now().time()})
  hb = threading.Thread(target=send_hearbeat)
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
      
      print('received' + str(len(data)) + 'bytes from' + str(address))
      print('Message:' + str(data))
      if(data[:2] == 'SM'):
		if(str(address[0]) in tabelaServidores):
		  print("Updating Heartbeat table from: " + str(address[0]) + " at " + str(datetime.datetime.now().time()) )
          tabelaServidores.update({str(adress[0]) : datetime.datetime.now().time()})
          print(tabelaServidores.items())
        else:
		  print("Adding new server to table: ", adress[0]);
		  tabelaServidores.update({str(adress[0]) : datetime.datetime.now().time()})
		  tabelaServidores = OrderedDict(sorted(tabelaServidores.items(), key=lambda x: x[0]))
		  print(tabelaServidores.items())

      elif(data[:2] == 'SC') :
        if(socket.gethostbyname(socket.gethostname()) == list(tabelaServidores.items())[0]):
          print('sending acknowledgement to', address)
          sock.sendto('ack', address)
        else:
          print("I am not the chosen one")
          


  hb.join()
  print ('closing socket')
  sock.close()

if __name__ == "__main__":
  main()
