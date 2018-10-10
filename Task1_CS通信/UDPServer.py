import socket


############################################ socket相关配置
# 建立UDP socket
serverAddress = ('127.0.0.1', 31500)
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mainSocket.bind(serverAddress)
clientAddress = ('127.0.0.1',31501)

############################################ socket相关功能函数


while True:
    #服务器接收客户端消息
    data, addr = mainSocket.recvfrom(2048)
    if not data:
        print ("client has exist")
        break

    # 收到请求文件的命令 file
    if data.decode('utf-8') == 'download':
        data1, addr1 = mainSocket.recvfrom(2048)
        fileName = data1.decode()
        # 打开要传输的文件
        with open(fileName, 'rb') as fs:
            mainSocket.sendto(b'START', clientAddress)
            print("Start to send file")
            while True:
                fileData = fs.read(1024 * 8)
                if not fileData:
                    print("breaking from sending data")
                    break
                else:
                    mainSocket.sendto(fileData, clientAddress)
                    print ("reading the file")
            mainSocket.sendto(b'END', clientAddress)   
            print("End the sending file")
            fs.close()     

s.close()
