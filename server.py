#!/usr/bin/python3
import socket
import struct
import sys
import threading
from time import sleep
# Biblioteca usada para detecar o tempo
from datetime import datetime, date
# Biblioteca usada para a tabela de servidores, 
# pois deve estar sempre ordenada pelos enderecos IP
from collections import OrderedDict

#Definindo as operacoes matematicas permitidas
ops = {
  "+": (lambda a, b: a + b),
  "-": (lambda a, b: a - b),
  "*": (lambda a, b: a * b),
  "/": (lambda a, b: a / b)
}

#Funcao que avalia a expressao matematica em formato RPN
def eval(expression):
  tokens = expression.split()
  stack = []

  for token in tokens:
    if token in ops:
      arg2 = stack.pop()
      try:
          arg1 = stack.pop()
      except Exception as e:
          return "ERROR: The math expression should be in RPN."

      result = ops[token](arg1, arg2)
      stack.append(result)
    else:
        try:
            stack.append(int(token))
        except:
            return "ERROR: The numbers should be integers"


  return stack.pop()

#Funcao usada pelo servidor para enviar mensagem de heartbeat ao grupo multicast
def send_hearbeat(sockhp):

    print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Heartbeat started.")
    message = 'SM-Heartbeat'

    multicast_group1 = ('224.3.29.71', 10000)

    while True:
        try:
           #Enviando o heartbeat ao grupo multicast
            print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Sending heartbeat.")
            sent = sockhp.sendto(message.encode(), multicast_group1)

        except:
            print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: ERROR: Could not send heartbeat.")
            pass
	#O servidor espera 10 segundos antes de enviar o proximo heartbeat
        sleep(10)

#Funcao que checa quais servidores ainda estao ativos baseando-se 
#no ultimo hearbeat recebido de cada servidor do grupo 
def is_active(tabelaServidores):
    timenow = datetime.now().time()
    print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Checking if some server should be removed from the table.") 
    keys = []
    #Para cada servidor em tabelaServidores, checa quais estao inativos 
    #e salva seus IPs no array keys
    for key in tabelaServidores:
        timedelta = datetime.combine(
            date.today(), timenow) - datetime.combine(date.today(), tabelaServidores[key])
        print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Server with IP "+ key + " last heartbeat was: " +
              str(timedelta.seconds) + " seconds ago.")
        if(timedelta.total_seconds() > 40):
            keys.append(key)
        else:
            print(key + " still able to run")
    #Para cada servidor anteriormente salvo em keys, deleta ele da tabelaServidores
    for key in keys:
        print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Removing " + key + " from table, because it has been 40 seconds I did not receive a heartbeat from it.")
        del tabelaServidores[key]

    return tabelaServidores

#Funcao usada pelo servidor quando ele recebe um heartbeat do grupo 
#multicast, ela serve para atualizar o horario do ultimo heartbeat
#recebido e para adicionar um novo servidor na tabelaServidores caso
#este tenha sido o primeiro heartbeat recebido de um determinado servidor. 
def update_heartbeat(address, tabelaServidores):
    if(str(address) in tabelaServidores):
        print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Updating Heartbeat table of server: " +
              str(address) + " at " + str(datetime.now().time()))
        tabelaServidores.update({str(address): datetime.now().time()})
    else:
        print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Adding new server to table: ", address)
        tabelaServidores.update({str(address): datetime.now().time()})
        tabelaServidores = OrderedDict(
            sorted(tabelaServidores.items(), key=lambda x: x[0]))
    return tabelaServidores

#Programa principal
def main():

    # Cria um socket exclusivo para envio de heartbeat para o grupo multicast
    sockhp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Define time-to-live 
    ttl = struct.pack('b', 2)

    # Define as opcoes do socket de heartbeat
    sockhp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    # Iniciando tabela de servidores e ja inclui este servidor na tabela
    tabelaServidores = OrderedDict(
        {socket.gethostbyname(socket.gethostname()): datetime.now().time()})
    print(str(datetime.now().time())+" Server "+str(socket.gethostbyname(socket.gethostname()))+" created tabelaServidores, and included itself in it.")
    # Inicia a thread que enviara os heartbeats via o socket 'sockhp'
    hb = threading.Thread(target=send_hearbeat, args=(sockhp,))
    hb.start()

    #### SERVIDOR ####
    # Define o endereco do grupo multicast
    multicast_group = '224.3.29.71'
    server_address = ('', 10000)

    # Cria o socket que recebera as mensagens do grupo multicast
    # e que sera usado para comunicacao com o cliente
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Operacao de bind
    sock.bind(server_address)

    # Avisa o sistema operacional para adicionar o socket ao grupo 
    # multicast em todas as interfaces
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    # Define outras opcoes do socket
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Loop de recebimento de mensagens e envio de respostas
    while True:
        print(str(datetime.now().time())+' Server '+socket.gethostbyname(socket.gethostname())+' says: Waiting to receive message')
        # Aguarda recebimento de mensagem
        data, address = sock.recvfrom(1024)
        print(str(datetime.now().time())+' Server '+socket.gethostbyname(socket.gethostname())+' says: Received message: ' + data.decode('utf-8')[2:] + ' from ' + str(address))
        # Se a mensagem comeca com um 'SM', ela eh uma mensagem que vem de servidor
        # E portanto eh um heartbeat, a tabela de servidores deve ser atualizada
        if(data[:2].decode('utf-8') == 'SM'):
            tabelaServidores = update_heartbeat(address[0], tabelaServidores)
        # Se a mensagem comeca com um 'CM' ela eh uma mensagem que vem de um cliente
        # E portanto, deve ser uma mensagem de operacao matematica
        elif(data[:2].decode('utf-8') == 'CM'):
            # Checa se algum servidor esta inativo 
            tabelaServidores = is_active(tabelaServidores)
            # Checa se este servidor eh o primeiro da tabelaServidores, 
            # se sim, faz operacao matematica e responde o cliente
            if(socket.gethostbyname(socket.gethostname()) == list(tabelaServidores.items())[0][0]):
                print(str(datetime.now().time())+" Server "+str(socket.gethostbyname(socket.gethostname()))+" says: message from client, it is the expression: " + str(data[2:].decode('utf-8')))
                # Realiza operacao matematica
                result = eval(data[2:].decode('utf-8'))
                print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" got result: " + str(result))
                print(str(datetime.now().time())+" Server "+str(socket.gethostbyname(socket.gethostname()))+" is sending result to "+ str(address))
                # Responde o cliente com o resultado da operacao 
                sock.sendto(str(result).encode(), address)
            # Se este servidor nao eh o primeiro da tabela, ele nao eh o lider
            else:
                print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: I am not the chosen one")
        # A mensagem que chegou esta em um formato nao previsto
        # Servidor responde com mensagem de erro
        else:
            print(str(datetime.now().time())+" Server "+socket.gethostbyname(socket.gethostname())+" says: Message not recognized, answering with error message.")
            sock.sendto(("ERROR: Message not recognized by the server.").encode(), address)

    # Junta as threads	
    hb.join()
    # Fecha os sockets
    print('closing Heartbeat')
    sockhp.close()
    print('closing socket')
    sock.close()

# Chama a funcao main
if __name__ == "__main__":
    main()
