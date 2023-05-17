#############################################################################
# COMP2322 Computer Networking                                              #
# Project: Multi-thread Web Server                                          #
#                                                                           #
# 2023-04-08                                                                #
#                                                                           #
# This program is used to test Connection header in request                 #
#   Connection: Keep-Alive, and Connection: close will be tested            #
#                                                                           #
# Usage:                                                                    #
#        0. First, run the server by 'python3 HTTPServer.py'                #
#        1. Then, run with 'python3 ConnCloseTest.py'                       #
#        2. Input 1 in client side for testing Connection: Keep-Alive       #
#        3. Input 2 in client side for testing Connection: close            #
#        4. Error shows if more requests are sent after 'Connection: close' #
#                                                                           #
#   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   #
#   !!    Please carefully read README.md file first before running   !!   #
#   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   #
#                                                                           #
#############################################################################

import socket 
 
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 8000 
 
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client_socket.connect((SERVER_HOST, SERVER_PORT)) 
print("Client connected to server at %s:%d" % (SERVER_HOST, SERVER_PORT))
request = "HEAD /helloworld.html HTTP:/1.1\r\nConnection: Keep-Alive\r\n"
while True:
    try:
        client_socket.send(request.encode()) 
        print ('Client sent:\n'+request)
        response = client_socket.recv(1024) 
        print ('Server response:') 
        print (response.decode()) 
        print("1: Connection: Keep-Alive; 2: Connection: Close; 0: Quit")
        cmd = input("Enter command[1,2,0]:")
        if cmd == '0':
            break
        elif cmd == '1':
            request = "HEAD /helloworld.html HTTP:/1.1\r\nConnection: Keep-Alive\r\n"
        elif cmd == '2':
            request = "HEAD /helloworld.html HTTP:/1.1\r\nConnection: Close\r\n"
    except Exception as e:
        print("Error: %s" % e)
        break

client_socket.close()
print("Client closed")