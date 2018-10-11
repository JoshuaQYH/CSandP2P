import socket

serverAddress = ('127.0.0.1', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(serverAddress)

text_file = "data.txt"

clientAddress = ('127.0.0.1',31501)

while True:
    #服务器接收客户端消息
    data, addr = s.recvfrom(2048)
    if not data:
        print ("client has exist")
        break

    # 收到请求文件的命令 file
    if data.decode('utf-8') == 'file':
        # 打开要传输的文件
        with open(text_file, 'rb') as fs:
            s.sendto(b'START', clientAddress)
            print("Start to send file")
            while True:
                textData = fs.read(1024)
                if not textData:
                    print("breaking from sending data")
                    break
                else:
                    s.sendto(textData, clientAddress)
                    print ("reading the file")
            s.sendto(b'END', clientAddress)   
            print("End the sending file")
            fs.close()     

s.close()
