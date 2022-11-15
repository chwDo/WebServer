# Sample code for Multi-Threaded Server
# Python 3
# Usage: python3 UDPserver3.py
# coding: utf-8
import datetime as dt
import fcntl
import os
import threading
import time
from socket import *
import re
import sys
clients = []
serverSocket = None
users = dict()
serverFiles = []
onlineUsers = []
# loads users' information
def dataInit():
    global users, serverFiles
    obj = os.getcwd()+ "/credentials.txt"
    serverFiles.append(obj)
    file = open(obj, 'r')
    content = file.readlines()
    users = dict([c.split() for c in content])
    file.close()

#  save new users password and account to file
def dataUPD():
    global users
    path = os.getcwd()
    file = open(path + "/credentials.txt", 'w')
    fcntl.flock(file, fcntl.LOCK_EX)
    for k, v in users.items():
        file.write(k + ' ' + v + '\n')
    fcntl.flock(file, fcntl.LOCK_UN)
    file.close()

# authenticate loginer account
def authentication(client):
    global users,onlineUsers
    while 1:
        username = client.recv(1024).decode()
        # The different numbers indicate different status
        if username in onlineUsers:
            client.sendall("3".encode())
        elif username in users.keys():
            Message = "1"
            client.sendall(Message.encode())
            password = client.recv(1024).decode()
            if users[username] == password:
                Message = "1"
                client.sendall(Message.encode())
                onlineUsers.append(username)
                return True, username
            else:
                print("Incorrect password\n")
                client.sendall("2".encode())
        else:
            Message = "2"
            client.sendall(Message.encode())
            password = client.recv(1024).decode()
            users[username] = password
            dataUPD()
            onlineUsers.append(username)
            return True, username


def XIT(client, username):
    global clients,onlineUsers
    onlineUsers.remove(username)
    clients.remove(client)
    client.sendall("Goodbye".encode())
    print(username, "exited")
    print("waiting for clients\n")
    client.close()


# This command with write operation needs a ex lock
def CRT(client, username, threadTiitle):
    global serverFiles
    print(username, 'issued CRT command')
    if os.path.exists(threadTiitle + '_th.txt'):
        message = "Thread " + threadTiitle + " exists\n"
        print(message)
        client.sendall(message.encode())
    else:
        obj = os.getcwd() + f'/{threadTiitle}_th.txt'
        serverFiles.append(obj)
        file = open(obj, 'w')
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(username + '\n')
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
        message = "Thread " + threadTiitle + " created\n"
        print(message)
        client.sendall(message.encode())


def LST(client, username):
    print(username, 'issued LST command\n')
    message = [i[:-7] + '\n' for i in os.listdir(os.getcwd()) if i.endswith("_th.txt")]
    if len(message) == 0:
        message = 'No threads to list\n'
    else:
        message = ''.join(message)
    client.sendall(message.encode())


def SHT(client,username, password):
    global clients
    print(username, 'issued SHT command')
    if password == sys.argv[2]:
        message = "Goodbye. Server shutting down"
        for i in clients:
            i.sendall(message.encode())
            i.close()
        print("Server shutting down")
        for i in serverFiles:
            if os.path.exists(i):
                os.remove(i)
        os._exit(0)
    else:
        message = "Incorrect server password\n"
        client.sendall(message.encode())
        print(message)


def RMV(client, username, threadTitle):
    global serverFiles
    # if thread does exist
    print(username, 'issued RMV command')
    if threadTitleVerify(client, threadTitle):
        # check the thread owner
        file = open(os.getcwd() + f'/{threadTitle}_th.txt', 'r')
        fcntl.flock(file, fcntl.LOCK_SH)
        # need to strip \n
        owner = file.readline().strip('\n')
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
        if owner == username:
            files = [i for i in os.listdir(os.getcwd()) if i.startswith(threadTitle)]
            for i in files:
                os.remove(i)
            print(f"Thread {threadTitle} removed\n")
            message = "Thread has been removed\n"
        else:
            print(f"Thread {threadTitle} cannot be removed\n")
            message = "The thread was created by another user and cannot be removed\n"
        client.sendall(message.encode())


def MSG(client, username, threadTitle, message):
    print(username, 'issued MSG command')
    if threadTitleVerify(client, threadTitle):
        file = open(os.getcwd() + f'/{threadTitle}_th.txt', 'r+')
        # write operation needs ex lock
        fcntl.flock(file, fcntl.LOCK_EX)
        content = file.readlines()
        # find the last messagenumber
        for i in reversed(content):
            lengthOfNumber = re.match(r'\d*', i).span()[1]
            if lengthOfNumber != 0:
                messageNumber = int(i[:lengthOfNumber]) + 1
                break
        # if this is first message
        else:
            messageNumber = 1
        file.write(f'{messageNumber} {username}: {" ".join(message)}\n')
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
        # that is server message
        message = f'Message posted to {threadTitle} thread\n'
        print(message)
        client.sendall(message.encode())


def threadTitleVerify(client, threadTitle):
    if not os.path.exists(threadTitle + "_th.txt"):
        print(f'incorrect thread {threadTitle} specified\n')
        message = "Thread does not exist\n"
        client.sendall(message.encode())
        return False
    else:
        return True


# This command with write operation needs a share lock
def RDT(client, username, threadTitle):
    print(username, 'issued RDT command')
    if threadTitleVerify(client, threadTitle):
        file = open(os.getcwd() + f'/{threadTitle}_th.txt', 'r')
        fcntl.flock(file, fcntl.LOCK_SH)
        content = file.readlines()
        # if thread is empty
        if len(content) == 1:
            message = f'Thread {threadTitle} is empty\n'
        else:
            # first record is username of thread creator
            message = ''.join(content[1:])
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
        print(f'Thread {threadTitle} read\n')
        client.sendall(message.encode())


# Write operation needs a ex lock
def DLT(client, username, threadTitle, messageNumber):
    print(username, 'issued DLT command')
    # this is for print
    index = messageNumber
    if threadTitleVerify(client, threadTitle):
        if messageNumber.isnumeric():
            messageNumber = int(messageNumber)
            file = open(os.getcwd() + f'/{threadTitle}_th.txt', 'r+')
            fcntl.flock(file, fcntl.LOCK_EX)
            content = file.readlines()
            flag = False
            for i in range(len(content)):
                lengthOfNumber = re.match(r'\d*', content[i]).span()[1]
                if lengthOfNumber != 0:
                    if messageNumber == int(content[i][:lengthOfNumber]):
                        messageNumber = i
                        flag = True
                        break
            # Did not find match message
            if not flag:
                message = 'messagenumber invalid'
                print(message, '\n')
            elif content[messageNumber].split()[1][:-1] != username:
                message = "The message was posted by another user and cannot be removed\n"
                print(message, '\n')
            else:
                message = f'Thread {threadTitle} messagenumber {index} was deleted\n'
                print(message, '\n')
                # prevent index out of range
                if messageNumber != len(content):
                    for i in range(messageNumber + 1, len(content)):
                        lengthOfNumber = re.match(r'\d*', content[i]).span()[1]
                        # exclude file transfer record
                        if lengthOfNumber != 0:
                            content[i] = str(int(content[i][:lengthOfNumber]) - 1) + content[i][lengthOfNumber:]
                    # move file point back to start
                    del content[messageNumber]
                    file.seek(0, 0)
                    file.truncate()
                    file.writelines(content)
                    fcntl.flock(file, fcntl.LOCK_UN)
                    file.close()
        else:
            message = 'messagenumber invalid\n'
        print(message, '\n')
        client.sendall(message.encode())


def EDT(client, username, threadTitle, messageNumber, newMessage):
    print(username, 'issued EDT command\n')
    # this is for print
    index = messageNumber
    if threadTitleVerify(client, threadTitle):
        if messageNumber.isnumeric():
            messageNumber = int(messageNumber)
            file = open(os.getcwd() + f'/{threadTitle}_th.txt', 'r+')
            fcntl.flock(file, fcntl.LOCK_EX)
            content = file.readlines()
            flag = False
            for i in range(len(content)):
                lengthOfNumber = re.match(r'\d*', content[i]).span()[1]
                if lengthOfNumber != 0:
                    if messageNumber == int(content[i][:lengthOfNumber]):
                        messageNumber = i
                        flag = True
                        break
            # exclude message has no message number(the information of file transformation)
            if not flag:
                message = 'messagenumber invalid'
            elif content[messageNumber].split()[1][:-1] != username:
                print(content[messageNumber].split()[1], username)
                message = "The message was posted by another user and cannot be edited\n"
            else:
                message = f'Thread {threadTitle} messagenumber {index} was edited\n'
                # prevent index out of range
                content[messageNumber] = " ".join(content[messageNumber].split()[:2] + newMessage) + '\n'
                file.seek(0, 0)
                file.truncate()
                file.writelines(content)
                fcntl.flock(file, fcntl.LOCK_UN)
                file.close()
        else:
            message = 'messagenumber invalid\n'
        print(message)
        client.sendall(message.encode())


def UPD(client, username, threadTitle, filename):
    global serverFiles
    print(username, 'issued UPD command')
    # verify threadTitle
    client.sendall('UPD'.encode())
    if threadTitleVerify(client, threadTitle):
        filesize = int(client.recv(1024).decode())
        obj = f'{os.getcwd()}/{threadTitle}-{filename}'
        serverFiles.append(obj)
        with open(obj, 'wb') as file:
            recvSize = 0
            while recvSize < filesize:
                line = client.recv(1024)
                file.write(line)
                recvSize += len(line)
            message = f'{username} uploaded file {filename} to {threadTitle} thread\n'
            print(message)
            client.sendall(f'{filename} uploaded to {threadTitle} thread\n'.encode())
        with open(os.getcwd() + f'/{threadTitle}_th.txt', 'a') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            message = f"{username} uploaded {filename}\n"
            file.write(message)
            fcntl.flock(file, fcntl.LOCK_UN)


def DWN(client, username, threadTitle, filename):
    print(username, 'issued DWN command\n')
    client.sendall('DWN'.encode())
    time.sleep(0.1)
    if threadTitleVerify(client, threadTitle):
        obj = f'{os.getcwd()}/{threadTitle}-{filename}'
        if os.path.exists(obj):
            message = f'{filename} downloaded from Thread {threadTitle}\n'
            client.sendall(message.encode())
            print(message)
            time.sleep(0.2)
            client.recv(1024)
            filesize = str(os.path.getsize(obj))
            client.sendall(filesize.encode())
            with open(obj, 'rb') as file:
                fcntl.flock(file, fcntl.LOCK_SH)
                for line in file:
                    client.sendall(line)
                fcntl.flock(file, fcntl.LOCK_UN)
        else:
            print(f'{filename} does not exist in Thread {threadTitle}\n')
            client.sendall("File does not exists\n".encode())


# command Handler
def commandHandle(client, username):
    commandList = [XIT, CRT, LST, RMV, MSG, RDT, DLT, EDT, UPD, DWN, SHT]
    commandName = [i.__name__ for i in commandList]
    while 1:
        op = client.recv(1024).decode().split()
        if len(op) != 0 and op[0] in commandName:
            message = 'incorrect syntax for ' + op[0] + '\n'
            # One argument commands
            if op[0] == 'XIT' or op[0] == 'LST':
                if len(op) != 1:
                    client.sendall(message.encode())
                else:
                    commandList[commandName.index(op[0])](client, username)
                if op[0] == 'XIT':
                    break
            #  Two argument commands
            elif op[0] in ['CRT', 'RMV', 'RDT', 'SHT']:
                if len(op) != 2:
                    client.sendall(message.encode())
                else:
                    commandList[commandName.index(op[0])](client, username, op[1])
            # Three argument commands
            elif op[0] in ['MSG']:
                if len(op) < 3:
                    client.sendall(message.encode())
                else:
                    commandList[commandName.index(op[0])](client, username, op[1], op[2:])
            elif op[0] in ['EDT']:
                if len(op) < 4:
                    client.sendall(message.encode())
                else:
                    commandList[commandName.index(op[0])](client, username, op[1], op[2], op[3:])
            else:
                if len(op) != 3:
                    client.sendall(message.encode())
                else:
                    commandList[commandName.index(op[0])](client, username, op[1], op[2])
        else:
            message = "Invalid command\n"
            client.sendall(message.encode())

# message Handler
def messageHandle(client, addr):
    global clients
    print("Client connected")
    result, username = authentication(client)
    if result:
        print(username, 'successful login')
        # store client information (IP and Port No) in list
        clients.append(client)
        commandHandle(client, username)
    else:
        print("login unsuccessful")
        client.close()


def accept_client():
    global serverSocket
    global clients
    print('Server is ready for service')
    while 1:
        client, addr = serverSocket.accept()
        thread = threading.Thread(target=messageHandle, args=(client, addr))
        thread.setDaemon(True)
        thread.start()


def init():
    # we will use two sockets, one for sending and one for receiving
    global clientSocket
    global serverSocket
    ADDRESS = ('localhost', int(sys.argv[1]))
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind(ADDRESS)
    serverSocket.listen(5)
    # read users from credentials.txt
    dataInit()

    acceptThread = threading.Thread(name="accept_thread", target=accept_client)
    acceptThread.daemon = True
    acceptThread.start()

    while True:
        time.sleep(0.1)


if __name__ == '__main__':
    init()
