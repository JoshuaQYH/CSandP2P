import socket
import sys
import os
import struct

# 变量初始化
# 服务端下载的文件的的存放路径
filePath = "F:\\Github\\ComNetProject1\\Task1_CS\\Client\\clientData\\"
BUFFSIZE = 1024
# 加密解密函数

# socket配置相关
# 服务端地址
serverAddress = ('127.0.0.1', 3100)
# 创建客户端socket
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ('127.0.0.1', 3101)
# 绑定客户端 端口
mainSocket.bind(clientAddress)


# socket相关功能函数
# 发送请求给服务器，请求服务器返回文件资源列表
def listFile():
    print("Ready to list the files on Server.")

    try:
        clientData, clientAddr = mainSocket.recvfrom(51200)
    except ConnectionResetError:
        print("[Error]: Port is wrong")
    except:
        print("Timeout or some other errors")

    fileList = clientData.decode('utf-8')
    print(fileList)

    print("All Files on server are here.")
    return 0


def judgeFileName(fileName):
    return False

# 发送下载命令，请求服务端返回该文件并接收保存，接收服务端消息提示


def downloadFile(fileName):
    print("Ready to download file from server")
    data, addr = mainSocket.recvfrom(BUFFSIZE)
    fsize = int(data,10)
    if fsize:
        file = filePath + fileName
        fs = open(file, 'wb')
        recvd_size = 0  # 定义已接收文件的大小
        print("start receiving...")
        while not recvd_size == fsize:
            if fsize - recvd_size > BUFFSIZE:
                data, addr = mainSocket.recvfrom(BUFFSIZE)
                recvd_size += len(data)
                fs.write(data)
            else:
                data, addr = mainSocket.recvfrom(fsize - recvd_size)
                recvd_size = fsize
                fs.write(data)
            
        print("end receive...")
        fs.close()
    return 0

# 发送文件给服务端，上传命令后发送文件，最后接收服务端消息提示do


def uploadFile(fileName):
     # 检测当前目录是否存在该文件
    file = filePath + fileName
    print("send " + file)
    if os.path.isfile(file):
        fsize = str(os.path.getsize(file))
        mainSocket.sendto(fsize.encode('utf-8'), serverAddress)

        fs = open(file, 'rb')
        print("Start to upload file")
        while True:
            fileData = fs.read(BUFFSIZE)
            if not fileData:
                print("breaking from uploading data")
                break
            mainSocket.sendto(fileData, serverAddress)
            print("reading the file")
        print("End the sending file")
        fs.close()
    else:
        fileName = input("Input the exsitig file")
    return 0


# 请求命令部分
while True:
    # 发送命令，传给服务器
    msg = input('''Input one of the following command:\n 
                    * list  ----------------------------- list the files on server \n
                    * download [filename] ---------------download file from server\n
                    * upload [filename] ---------------------upload file to server \n
                    * exit -------------------------------------------close socket\n ''')

    if not msg:
        break
    mainSocket.sendto(msg.encode('utf-8'), serverAddress)
    # 将消息按空格进行分割，比如command[0] = upload command[1] = filename
    command = msg.split()

    if command[0] == "list":
        listFile()

    elif command[0] == "download":
        downloadFile(command[1])

    elif command[0] == "upload":
        uploadFile(command[1])

    elif command[0] == "exit":
        mainSocket.close()
        sys.exit()

    else:
        print("Please input the correct command.")
