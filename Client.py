# Python 3
# Usage: python3 UDPClient3.py localhost 12000
# coding: utf-8
import sys
from socket import *
import os
import fcntl


def authentication(clientSocket):
    while 1:
        username = input("Enter username: ")
        clientSocket.sendall(username.encode())
        receivedMessage = str(clientSocket.recv(1024).decode())
        if receivedMessage == "2":
            password = input("Enter new password :")
            clientSocket.sendall(password.encode())
            return True
        elif receivedMessage == "3":
            print(f"{username} has already logged in")
        else:
            password = input("Enter password: ")
            clientSocket.sendall(password.encode())
            receivedMessage = clientSocket.recv(1024).decode()
            if receivedMessage == "1":
                return True
            elif receivedMessage == "2":
                print("Invalid password\n")


# Close the socket
def UPD(client, filename):
    filesize = os.path.getsize(f'{os.getcwd()}/{filename}')
    client.sendall(str(filesize).encode())
    with open(f'{os.getcwd()}/{filename}', 'rb') as file:
        fcntl.flock(file,fcntl.LOCK_SH)
        for line in file:
            client.send(line)
    message = client.recv(1024).decode()
    print(message)


def DWN(client, filename):
    message = client.recv(1024).decode()
    if message == "File do not exists\n" or message == "Thread does not exist\n":
        pass
    else:
        client.sendall("ready to receive files".encode())
        filesize = int(client.recv(1024).decode())
        with open(f'{os.getcwd()}/{filename}', 'wb') as file:
            recvSize = 0
            while recvSize < filesize:
                line = client.recv(1024)
                file.write(line)
                recvSize += len(line)
    print(message)

# command Handler
def commandHandle(client):
    while 1:
        op = input("Enter one of following commands: CRT, MSG, DLT, LST, RDT, UPD, DWN, RMV, XIT, SHT:")
        client.sendall(op.encode())
        message = client.recv(1024).decode()
        if message == "Goodbye" or message == "Goodbye. Server shutting down":
            print(message)
            break
        elif message == "UPD":
            UPD(client, op.split()[2])
        elif message == "DWN":
            DWN(client, op.split()[2])
        else:
            print(message)


def init():
    # Server would be running on the same host as Client
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((serverName, serverPort))
    if authentication(client):
        print("Welcome to forum")
        commandHandle(client)
    else:
        print("login unsuccessful")


if __name__ == '__main__':
    init()
