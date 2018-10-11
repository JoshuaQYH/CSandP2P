import socket
import os

filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task1_CS\\Server\\serverData\\"

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
    file_dir = filePath    
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        print(files) #当前路径下所有非目录子文件
        files.remove("UDPServer.py")
        fileStr = str(files)
        mainSocket.sendto(fileStr.encode("utf-8"), clientAddress)
    print("Have sent files!")

# 响应客户端下载文件的请求,先满足小型文件传输
def downloadFile(fileName):
    # 打开要传输的文件
    file = filePath + fileName
    print ("send " + file)
    with open(file, 'rb') as fs:
        print("Start to send file")
        while True:
            fileData = fs.read(1024 * 8)
            if not fileData:
                print("breaking from sending data")
                break
            else:
                mainSocket.sendto(fileData, clientAddress)
                print ("reading the file")
        print("End the sending file")
        fs.close()     


# 接收客户端上传的文件
def upload(fileName):
    return 0

#######################################命令部响应客户端请求部分
while True:
    #服务器接收客户端消息
    data, addr = mainSocket.recvfrom(2048)
    if not data:
        print ("client has exist")
        break
    tmp = data.decode('utf-8')
    text = tmp.split()
    print(text[0] + "---")
    # 收到请求文件的命令 download
    if text[0] == "download":
        downloadFile(text[1])

    elif text[0] == "list":
        listFile()

    elif text[0] == "upload":
        upload(text[1])

mainSocket.close()
