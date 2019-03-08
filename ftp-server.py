import socket
import os
import subprocess

BUFF_SIZE = 1024
PASSWD = '123'
CRLF = '\x0D\x0A'
QUIT = -1
CLOSED = -2
PATH_PREF = 'D:'

def list_directory(dir):
        proc = subprocess.Popen(['ls', '-la', dir], stdout=subprocess.PIPE)
        tmp = proc.stdout.read()
        return str(tmp, 'UTF8').split('\n')[1:-1]

class FTPServer():
    sock = None
    client_encoding = 'UTF8'

    def __init__(self):
        self.cmd_sock = None
        self.client_addr = None
        self.transf_sock = None
        self.transf_mode = 'ASCII'
        self.cwd = '\\'
        FTPServer.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_and_log_bytes(self, sock, msg):
        sock.send(bytes(msg + CRLF, FTPServer.client_encoding))
        print('SENT:', msg)

    def processRequest(self, request):
        if not request:
            return CLOSED
        chunks = request.split()
        cmd = chunks[0]

        if cmd == 'USER':
            self.send_and_log_bytes(self.cmd_sock, '331 Enter Password')
            request = str(self.cmd_sock.recv(BUFF_SIZE), FTPServer.client_encoding).split()
            if request[0] == "PASS" and request[1] == PASSWD:
                self.send_and_log_bytes(self.cmd_sock, '230 Login Successful')
            else:
                self.send_and_log_bytes(self.cmd_sock, "430 Failed. Try Again")

        elif cmd == 'PWD':
            self.send_and_log_bytes(self.cmd_sock, "200 Current Directory is " + self.cwd)

        elif cmd == 'CWD':
            self.cwd = chunks[1]
            self.send_and_log_bytes(
                self.cmd_sock, "200 Directory Changed to " + self.cwd)

        elif cmd == 'TYPE':
            if chunks[1] == 'A':
                self.transf_mode = 'ASCII'
            elif chunks[1] == 'I':
                self.transf_mode = 'BYTE'
            self.send_and_log_bytes(self.cmd_sock, "200 Transfer Mode " + self.transf_mode)

        elif cmd == 'PORT':
            numers = chunks[1].split(',')
            HOST = "{0}.{1}.{2}.{3}".format(*numers[:4])
            PORT = int(numers[4])*256 + int(numers[5])
            self.transf_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transf_sock.connect((HOST, PORT))
            self.send_and_log_bytes(self.cmd_sock, "200 Connected To Client For File Transfer")

        elif cmd == 'LIST':
            self.send_and_log_bytes(self.cmd_sock, "150 Opening ASCII mode data connection for file list.")
            msg = CRLF.join(list_directory(os.path.join(PATH_PREF, self.cwd)))
            self.send_and_log_bytes(self.transf_sock, msg)
            self.transf_sock.close()
            self.send_and_log_bytes(self.cmd_sock, "226 Dir Send OK")

        elif cmd == 'RETR':
            self.send_and_log_bytes(self.cmd_sock, "150 Opening " + self.transf_mode + " mode data connection for file list.")
            file_name = chunks[1]
            file = open(os.path.join('\\', PATH_PREF, self.cwd, file_name), "rb")
            file_bytes = file.read()
            self.transf_sock.send(file_bytes)
            self.transf_sock.close()
            self.send_and_log_bytes(self.cmd_sock, "226 File Send OK")

        elif cmd == 'QUIT':
            self.send_and_log_bytes(self.cmd_sock, "221 GoodBye")
            self.cmd_sock.close()
            return QUIT

        elif cmd == 'FEAT':
            self.send_and_log_bytes(self.cmd_sock, "211 ")

        elif cmd == 'MODE':
            self.send_and_log_bytes(self.cmd_sock, "500 ")

        elif cmd == 'PASV':
            self.send_and_log_bytes(self.cmd_sock, "227 ")

        elif cmd == 'OPTS':
            self.send_and_log_bytes(self.cmd_sock, "200 ")

        elif cmd == 'ABOR':
            self.send_and_log_bytes(self.cmd_sock, "226 ")

        elif cmd == 'SYST':
            self.send_and_log_bytes(
                self.cmd_sock, "215 UNIX Type: Apache FtpServer")

        return 220

    def up(self, HOST, PORT):
        try:
            self.sock.bind((HOST, PORT))
        except:
            print("Port Busy")
            return
        while True:
            self.sock.listen(1)
            print("Listening For Clients...")
            self.cmd_sock, self.client_addr = FTPServer.sock.accept()
            print("Client Connected")
            self.send_and_log_bytes(self.cmd_sock, "220 You Are Welcome")
            while True:
                request = str(self.cmd_sock.recv(BUFF_SIZE), self.client_encoding)
                print('RECV:', request, end='')
                echo = self.processRequest(request)
                if echo == CLOSED:
                    self.cmd_sock.close()
                    break
                if echo == QUIT:
                    break


HOST = ''
PORT = 9090
ftp_server = FTPServer()
ftp_server.up(HOST, PORT)
