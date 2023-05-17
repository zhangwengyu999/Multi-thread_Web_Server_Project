#############################################################################
# COMP2322 Computer Networking                                              #
# Project: Multi-thread Web Server                                          #
#                                                                           #
# 2023-04-18                                                                #
#                                                                           #
# This program will listen the localhost (http://127.0.0.1:8000),           #
#   please use the browser to access the web page                           #
#                                                                           #
#   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   #
#   !!    Please carefully read README.md file first before running   !!   #
#   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   #
#                                                                           #
#############################################################################

import socket 
import threading
from threading import Lock
import os
import datetime

# set default server host and port
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 8000 

# define Connection class
class Connection:
    def __init__(self, conn, addr, time):
        self.conn = conn # socket connection field
        self.addr = addr # client address field
        self.time = time # access time field
        self.keepAlive = True # keep-alive flag, default is True
        self.request = None
    
    def getConnection(self):
        return self.conn
    def getAddress(self):
        return self.addr
    def getTime(self):
        return self.time
    
    """_summary_: get the request from client
    _return_: the request from client
    """
    def getRequest(self):
        # self.request = self.conn.recv(1024).decode()
        return self.request
    
    """_summary_: get the request from client
    _return_: the request from client
    """
    def acceptRequest(self):
        self.request = self.conn.recv(1024).decode()
        return self.request
    
    """_summary_: get the Method of the request
    _return_: first word of the first line of the request
    """
    def getMethod(self):
        headers = self.request.split('\n') 
        return headers[0].split()[0]
    
    """_summary_: get the Path of the request
    _return_: second word of the first line of the request
    """
    def getPath(self):
        headers = self.request.split('\n') 
        return headers[0].split()[1]
    
    """_summary_: get the Connection way of the request
    _return_: the value of the Connection in header, Keep-Alive or Close
    """
    def getConnectionWay(self):
        headers = self.request.split('\n') 
        for h in headers:
            if 'Connection' in h:
                return h.split()[1]
    
    """_summary_: get the If-Modified-Since of the request
    _return_: the value of the If-Modified-Since in header
    format: %a, %d %b %Y %H:%M:%S %Z, e.g. Sun, 09 Apr 2023 12:00:00 GMT
    """
    def getIfModifiedSince(self):
        headers = self.request.split('\n') 
        for h in headers:
            if 'if-modified-since' in h:
                header = h
        return header[19:48]

# define HTTPServer class
class HTTPServer:
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT):
        self.host = host # server host
        self.port = port # server port
        
        self.lock = Lock() # lock for log file
        self.logFile = open('log.txt', 'a') # opened log txt file

    def runServer(self):
        # Create socket 
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.serverSocket.bind((self.host, self.port)) 
        self.serverSocket.listen(10) # listen for 10 connections at most
        print('#'*89)
        print('#','\t\t\tWelcome to the Multi-thread Web Server!\t\t\t\t#')
        print('# > The server now is running at http://%s:%s, press <Control+C> to shutdown\t#' % (self.host, self.port))
        print('# > The log file is log.txt\t\t\t\t\t\t\t\t#')
        print('# > Received requests and corresponding responses will be displayed below:\t\t#')
        
        while True:
            try:
                clientConnection, clientAddress = self.serverSocket.accept()
                nowTime = datetime.datetime.now()
                conn = Connection(clientConnection, clientAddress, nowTime) # create a Connection object
                thread = threading.Thread(target=self.listenRequest, args=(conn,)) # create a thread on listenRequest function
                thread.start() # start the thread
                thread.join() # wait for the thread to finish
            
            # listen Ctrl+C to shutdown the server
            except KeyboardInterrupt:
                self.logFile.close() # close the log file
                for thread in threading.enumerate():
                    if thread is not threading.currentThread():
                        thread.join()
                print('\n> The server is shutdown, thank you and bye.')
                print('#'*89)
                return
 
    """_summary_: map the request to corresponding handler
    _param_: conn, a Connection object
    """
    def listenRequest(self, conn):
        
        while True:
            try:
                conn.acceptRequest()
                request = conn.getRequest()
                if not request:
                    continue
                clientConnection = conn.getConnection()
                clientAddress = conn.getAddress()
                nowTime = conn.getTime()

                print(request) 
                
                # Parse HTTP headers 
                requestCommand = conn.getMethod()
                path = conn.getPath()
                isAlive = conn.getConnectionWay()
                
                # Handle the Connection header
                if isAlive != 'keep-alive' and isAlive != 'Keep-Alive':
                    conn.keepAlive = False # set keep-alive flag to False
                else:
                    conn.keepAlive = True # set keep-alive flag to True
                
                if requestCommand == 'GET':
                    self.GETHandler(conn) # handle GET request
                if requestCommand == 'HEAD':
                    self.HEADHandler(conn) # handle HEAD request
                elif (requestCommand == 'POST' or requestCommand == 'DELETE' or requestCommand == 'PUT'):
                    self.BadRequestHandler(clientConnection) # handle other unsupported requests
                    self.writeToLogSafely(clientAddress, nowTime, path, 400) # write to log file with lock
                
                # Close client socket if keep-alive is False
                if conn.keepAlive == False:
                    clientConnection.close()
                    print('Client %s Connection closed' % str(clientAddress))
                    break
            except KeyboardInterrupt:
                clientConnection.close()
                break

    """_summary_: handle GET request
    _param_: conn, a Connection object
    """
    def GETHandler(self, conn):
        
        request = conn.getRequest()
        path = conn.getPath()
        inConn = conn.getConnection()
        hostName = conn.getAddress()
        nowTime = conn.getTime()
        # Handle the path
        if path == '/': 
                path = '/index.html'
        fileType = self.getFileType(path)
        
        try:
            if (fileType == 'text/html'):
                fin = open('htdocs'+path)
                content = fin.read() # Get the content of the file 
                fin.close() 
            else:
                with open('htdocs'+path, 'rb') as f:
                    content = f.read()
            
            # handle the If-Modified-Since header
            if 'if-modified-since' in request:
                timeStr = conn.getIfModifiedSince()
                modified_since = datetime.datetime.strptime(timeStr, '%a, %d %b %Y %H:%M:%S %Z')
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path))
                if modified_since >= last_modified:
                    # the file is up to date
                    response = 'HTTP/1.1 304 Not Modified\r\n'
                    response+='Last-Modified: '+str(datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path)))+'\r\n'
                    response+='Content-Length: '+str(len(content))+'\r\n'
                    response+='Content-Type: '+fileType+'\r\n\r\n'
                    inConn.sendall(response.encode()) # send the response without content
                    print(response)
                    self.writeToLogSafely(hostName, nowTime, path, 304) # write to log file with lock
                    return
            
            # no If-Modified-Since header or the file is not up to date
            response = 'HTTP/1.1 200 OK\r\n'
            response+='Last-Modified: '+str(datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path)))+'\r\n'
            response+='Content-Length: '+str(len(content))+'\r\n'
            response+='Content-Type: '+fileType+'\r\n\r\n'
            print(response)
            inConn.sendall(response.encode()) 
            if (fileType == 'text/html'):
                inConn.send(content.encode()) # send the response with text content
            else:
                inConn.send(content) # send the response with image content
            self.writeToLogSafely(hostName, nowTime, path, 200) # write to log file with lock
        except FileNotFoundError: # file not found
            self.NotFoundHandler(inConn) # handle 404 Not Found
            self.writeToLogSafely(hostName, nowTime, path, 404) # write to log file with lock

    """_summary_: handle HEAD request
    _param_: conn, a Connection object
    very similar to GETHandler, except that it does not send the content of the file, only the headers
    """
    def HEADHandler(self, conn):
        path = conn.getPath()
        inConn = conn.getConnection()
        request = conn.getRequest()
        hostName = conn.getAddress()
        nowTime = conn.getTime()
        # Get the content of the file 
        if path == '/': 
            path = '/index.html'
        fileType = self.getFileType(path)
        try:
            if (fileType == 'text/html'):
                fin = open('htdocs'+path)
                content = fin.read() 
                fin.close() 
            else:
                with open('htdocs'+path, 'rb') as f:
                    content = f.read()
            
            if 'if-modified-since' in request:
                timeStr = conn.getIfModifiedSince()
                modified_since = datetime.datetime.strptime(timeStr, '%a, %d %b %Y %H:%M:%S %Z')
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path))
                if modified_since >= last_modified:
                    response = 'HTTP/1.1 304 Not Modified\r\n'
                    response+='Last-Modified: '+str(datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path)))+'\r\n'
                    response+='Content-Length: '+str(len(content))+'\r\n'
                    response+='Content-Type: '+fileType+'\r\n\r\n'
                    inConn.sendall(response.encode()) 
                    print(response)
                    self.writeToLogSafely(hostName, nowTime, path, 304)
                    return
            
            response = 'HTTP/1.1 200 OK\r\n'
            response+='Last-Modified: '+str(datetime.datetime.fromtimestamp(os.path.getmtime('htdocs'+path)))+'\r\n'
            response+='Content-Length: '+str(len(content))+'\r\n'
            response+='Content-Type: '+fileType+'\r\n\r\n'
            inConn.sendall(response.encode()) 
            print(response)
            self.writeToLogSafely(hostName, nowTime, path, 200)
        except FileNotFoundError:
            self.NotFoundHandler(inConn)
            self.writeToLogSafely(hostName, nowTime, path, 400)
        
    """_summary_: handle 404 Not Found response
    _param_: conn, a Connection object
    """
    def NotFoundHandler(self, inConn):
        response = 'HTTP/1.1 404 Not Found\r\n'
        response+='Content-Length: 0\r\n'
        response+='Content-Type: text/plain\r\n\r\n'
        print(response)
        inConn.sendall(response.encode())
    
    """_summary_: handle 400 Bad Request response
    _param_: conn, a Connection object
    """
    def BadRequestHandler(self, inConn):
        response = 'HTTP/1.1 400 Bad Request\r\n'
        response+='Content-Length: 0\r\n'
        response+='Content-Type: text/plain\r\n\r\n'
        print(response)
        inConn.sendall(response.encode())

    """_summary_: get the file type of the file
    _param_: conn, a Connection object
    _return_: fileType, a string of the file type
    """
    def getFileType(self, path):
        _, ext = os.path.splitext(path)
        if ext == '.html':
            fileType = 'text/html'
        elif ext == '.png':
            fileType = 'image/png'
        elif ext == '.jpg':
            fileType = 'image/jpg'
        elif ext == 'jpeg':
            fileType = 'image/jpeg'
        else:
            fileType = 'text/plain'
        return fileType
    
    """_summary_: write to log file safely with lock
    _param_:    inIP: IP address of the client
                inTime: time of the request
                inFileName: file name of the request file
                inResponseType: response type of the request
    """
    def writeToLogSafely(self, inIP, inTime, inFileName, inResponseType):
        with self.lock: # lock the log file
            self.logFile.write('[IP]:'+str(inIP)+' [Time]:'+str(inTime)+' [File]:'+inFileName+' [Response]:'+str(inResponseType)+'\n')

if __name__ == '__main__':
    httpServer = HTTPServer() # create a HTTPServer object
    httpServer.runServer() # run the server
    