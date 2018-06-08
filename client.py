import socket
import struct
import sys
from datetime import datetime, date
from time import sleep

# Define o endereco do grupo multicast
multicast_group = ('224.3.29.71', 10000)

# Cria um socket para se comunicar com o grupo
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define um timeout para que o socket nao seja bloqueado
# indefinidamente ao tentar receber dados
sock.settimeout(0.2)

# Define o time to live das mensagens do cliente 
ttl = struct.pack('b', 1)
# Define outras opcoes do socket
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

# String usada para armazenar o input do usuario
message = "start"

# Enquanto a mensagem nao eh 'quit', o programa continua a enviar
# operacoes aritmeticas ao grupo multicast
while(message != "quit"):
    print("-----------------------------//--------------------------------")
    print("Welcome to the calculator Client! Type 'quit' to quit the program.")
    print("To make a calculation, type a reverse polish math expression,\nfor example 5+3 becomes 5 3 +")
    print("-----------------------------//--------------------------------") 
    # Le input do usuario
    message = input("Please write your expression(or quit): ")
    if(message != "quit"):
        # testa se o input foi vazio
        if(message == ""):
            print(str(datetime.now().time())+" Client "+socket.gethostbyname(socket.gethostname())+" says: ERROR: The message can not be empty.")
        # Se o input do usuario nao foi vazio, envia ao servidor
        else:  
                # Adiciona prefixo CM a mensagem para que o servidor saiba 
                # que esta eh uma mensagem que vem do cliente
                message = "CM" + message
                
                # Envia mensagem ao grupo multicast
                sent = sock.sendto(message.encode(), multicast_group)
                print(str(datetime.now().time())+" Client "+socket.gethostbyname(socket.gethostname())+" says: Sending math expression: ", message)

                # Espera por respostas de todos os recebedores
                while True:
                    print(str(datetime.now().time())+" Client "+socket.gethostbyname(socket.gethostname())+" says: Waiting to receive answer")
                    
                    try:
                        # Tenta receber mensagem de resposta
                        data, server = sock.recvfrom(64)
                    except socket.timeout:
                        # Caso nao tenha recebido nada ate o tempo do timeout, avisa timeout
                        print(str(datetime.now().time())+" Client "+socket.gethostbyname(socket.gethostname())+" says: ERROR: timed out, no more responses")
                        break
                    else:
                        # Caso tenha recebido uma resposta, imprime resposta e o remetente
                        print(str(datetime.now().time())+" Client "+str(socket.gethostbyname(socket.gethostname()))+" says: Received answer from server: "+ str(server))
                        print("Resulting answer of the server from the math request: \n"+message[2:]+" = "+data.decode('utf-8'))
                        break

print(str(datetime.now().time())+" Client "+socket.gethostbyname(socket.gethostname())+" says: Closing client socket.")
# Termina/fecha o socket
sock.close()
