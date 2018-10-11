import socket
import sys

####################################### 变量初始化
# 服务端下载的文件的文件名
savedFileName = ""

#######################################  加密解密函数


########################################  socket配置相关
# 服务端地址
serverAddress = ('127.0.0.1', 3100)
# 创建客户端socket 
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ('127.0.0.1', 3101)
# 绑定客户端 端口
mainSocket.bind(clientAddress)


####################################### socket相关功能函数
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
    return False;

# 发送下载命令，请求服务端返回该文件并接收保存，接收服务端消息提示
def downloadFile(fileName):
    print("Ready to download file from server")
    # 发送请求的文件名，此处假设文件名正确
    mainSocket.sendto(fileName, serverAddress)

    while True:
        data1, addr1 = mainSocket.recvfrom(2048)
        if data1 == b'START':
            print("开始接收文件!\n")
            with open(fileName, 'wb') as fw:
                while True:
                    data2, addr2 = mainSocket.recvfrom(1024 * 8)
                    if data2 == b'END':
                        print("结束接收文件")
                    else:
                        fw.write(data2)
                        print("正在写入文件")
                fw.close()

    print("download done!")
    return 0

# 发送文件给服务端，上传命令后发送文件，最后接收服务端消息提示
def uploadFile(fileName):
     # 检测当前目录是否存在该文件
    while not judgeFileName(fileName):
        fileName = input("Input the exsitig file")

    print("Ready to upload file to server")
    print("upload done!")
    return 0

##########################################请求命令部分
while True:
    # 发送命令，传给服务器
    msg = input('''Input one of the following command:\n 
                    1. list  ----------------------------- list the files on server \n
                    2. download [filename] ---------------download file from server\n
                    3. upload [filename] ---------------------upload file to server \n
                    4. exit -------------------------------------------close socket\n ''')
        
    if not msg:
        break

    # 将消息按空格进行分割，比如command[0] = upload command[1] = filename
    command = msg.split()
    
    if command[0] == "list":
        mainSocket.sendto(b'list', serverAddress)
        listFile()

    elif command[0] == "download":
        mainSocket.sendto(b'download', serverAddress)
        downloadFile(command[1])
       
    elif command[0] == "upload":
        uploadFile(command[1])
        
    elif command[0] == "exit":
        mainSocket.close()
        sys.exit()

    else:
        print("Please input the correct command.")
      