import socket
import os

############################################ socket相关配置
# 建立UDP socket
serverAddress = ('127.0.0.1', 3100)
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mainSocket.bind(serverAddress)
clientAddress = ('127.0.0.1',3101)

############################################ socket相关功能函数
# 列出资源文件夹ServerData中的数据文件，发送给客户端
def listFile():
    print("Ready to list file")
    file_dir = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task1_CS通信\\ServerData"    
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        print(files) #当前路径下所有非目录子文件
        fileStr = str(files)
        mainSocket.sendto(fileStr.encode("utf-8"), clientAddress)
    print("Have sent files!")


#######################################相应命令部分
while True:
    #服务器接收客户端消息
    data, addr = mainSocket.recvfrom(2048)
    if not data:
        print ("client has exist")
        break

    # 收到请求文件的命令 download
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

    elif data.decode('utf-8') == 'list':
        listFile()

mainSocket.close()
