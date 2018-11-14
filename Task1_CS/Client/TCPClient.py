import socket
import sys
import os
import struct
import hashlib
import time
import base64
# 变量初始化
# 服务端下载的文件的的存放路径
filePath = "F:\\Github\\ComNetProject1\\Task1_CS\\Client\\clientData\\"
codepath = "F:\\Github\\ComNetProject1\\Task1_CS\\Client\\Chiper.txt"
BUFFSIZE = 51200
# 加密解密函数
CODESIZE = 64
CODE = "utf-8"
# socket配置相关
# 服务端地址
serverAddress = ('192.168.199.199', 3100)
# 创建客户端socket
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientAddress = ('192.168.199.224', 3101)
clientAddresst = ('192.168.199.224',3102)
# 绑定客户端 端口
mainSocket.bind(clientAddress)


#获得加密私钥
def getTheKey():
    if not os.path.isfile(codepath):
        print("Can not find the file of the key!\n")
    f=open(codepath,'rb')
    f.seek(5)
    key=f.read(CODESIZE)
    return key

#数据内容加密解密
def chiperCode(s):
    key=getTheKey()
    realKey=key.decode(CODE)
    contest=s.decode(CODE)
    index=0
    result=""
    for i in range(0,len(contest)):
        if index>=len(realKey):
            index=0
        result+=chr(ord(realKey[index])^ord(contest[i]))
        index=index+1
    return result.encode(CODE)

#日志记录
def log(actoin,flag,exeTime):
    outFilePath= filePath+"logClient.txt"
    if os.path.isfile(outFilePath):
        fp=open(outFilePath,'a')
        date=time.asctime(time.localtime(time.time()))
        fp.write(date+'\n'+"Action: "+actoin+'\n'+'Flag: '+flag+'\n'+'Time: ')
        fp.write(str(exeTime))
        fp.write('s\n\n')
        fp.close()
    else:
        print("[Error]:can not open the client log file")
        exit(0)


#进度条打印
def progress_bar(num_cur, total):
    ratio = float(num_cur) / total
    percentage = int(ratio * 100)
    r = '\r[%s%s]%d%%' % (">"*percentage, " "*(100-percentage), percentage )
    sys.stdout.write(r)
    sys.stdout.flush()

# socket相关功能函数
# 发送请求给服务器，请求服务器返回文件资源列表
def listFile():
    print("\n**********************************************************************")
    print("Ready to list the files on Server.")
    start=time.time()
    mainSocket.settimeout(1)
    try:
        clientData = mainSocket.recv(BUFFSIZE)
        clientData = chiperCode(clientData)

        check1=hashlib.md5()
        check1.update(clientData)
        checkResult=check1.hexdigest()

        fileList = clientData.decode('utf-8')
        checkData= mainSocket.recv(32)
        if not (checkData==checkResult.encode(CODE)):
            print("[Error]:The package from server may be broken\n")
        else:
            fileList = clientData.decode('utf-8')
            print(fileList)
            print("All Files on server are here.")   
    except ConnectionResetError:
        print("[Error]: Port is wrong")
        end=time.time()
        log("Ask for the file list from server",'Fail:an connection error happened',end-start)
    except:
        print("Timeout or some other errors")
        end=time.time()
        log("Ask for the file list from server",'Fail:an unkown error happened',end-start)   
    print("**********************************************************************\n")
    return 0


def judgeFileName(fileName):
    return False

# 发送下载命令，请求服务端返回该文件并接收保存，接收服务端消息提示


def downloadFile(fileName):
    print("\n**********************************************************************")
    print("Ready to download file from server")
    mainSockett = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mainSockett.bind(clientAddresst)       
    mainSockett.connect(serverAddress)

    start=time.time()
    try:
        data = mainSockett.recv(BUFFSIZE)
        fsize = int(data, 10)
        if fsize>0:
            file = filePath + fileName
            fs = open(file, 'wb')
            recvd_size = 0  # 定义已接收文件的大小
            check2=hashlib.md5()
            print("start downloading...")
            while not recvd_size == fsize:
                if fsize - recvd_size > BUFFSIZE:
                    data = mainSockett.recv(BUFFSIZE)
                    #data=base64.b64decode(chiperCode(data))
                    check2.update(data)
                    recvd_size += len(data)
                    fs.write(data)
                    progress_bar(recvd_size,fsize)
                    
                else:
                    data = mainSockett.recv(fsize - recvd_size)
                    #Data=base64.b64decode(chiperCode(data))
                    recvd_size = fsize
                    check2.update(data)
                    progress_bar(recvd_size,fsize)
                    fs.write(data)
            checkData = mainSockett.recv(32)
            if not (checkData == check2.hexdigest().encode('utf-8')):
                print("\nError：the file may be broken")
                end=time.time()
                log("Request for the file \'"+fileName+"\' from server",'Fail:file has been broken',end-start)
            else:
                print("\nDownload successfully")
                end=time.time()
                log("Request for the file \'"+fileName+"\' from server",'OK',end-start)
            
            fs.close()
        else:
            print("ERROR:can't find file")
            end=time.time()
            log("Request for the file \'"+fileName+"\' from server",'Fail:file not found',end-start)
    except:
        print("\nERROR:download timeout")
        end=time.time()
        log("Request for the file \'"+fileName+"\' from server",'Fail:timeout when get the file',end-start)   
    mainSockett.close()
    print("**********************************************************************\n")    
    return 0

# 发送文件给服务端，上传命令后发送文件，最后接收服务端消息提示do


def uploadFile(fileName):
     # 检测当前目录是否存在该文件
    print("\n**********************************************************************")
    file = filePath + fileName
    print("send " + file)
    start=time.time()
    if os.path.isfile(file):
        fsize = str(os.path.getsize(file))
        send_size = 0  # 定义已发送文件的大小
        mainSocket.send(fsize.encode('utf-8'))

        fs = open(file, 'rb')
        print("Start uploading")
        check3=hashlib.md5()
        while True:
            fileData = fs.read(BUFFSIZE)
            if not fileData:
                break
            check3.update(fileData)
            mainSocket.send(fileData)
            send_size += len(fileData)
            progress_bar(send_size,int(fsize,10))
        print("\nUpload successfully")
        fs.close()
        checkData=check3.hexdigest().encode('utf-8')
        time.sleep(0.1)
        mainSocket.send(checkData)
        end=time.time()
        log("Request upload the file \'"+fileName+"\' to server",'OK',end-start)
    else:
        fileName = input("ERROR:can't find file")
        end=time.time()
        log("Request upload the file \'"+fileName+"\' to server",'Fail:file not found',end-start)
    print("**********************************************************************\n")
    return 0

log('The client open','OK',0)
start=time.time()
# 请求命令部分
while True:
    # 发送命令，传给服务器
    mainSocket.connect(serverAddress)
    msg = mainSocket.recv(BUFFSIZE)
    while True:     
        Command = input(msg.decode('utf-8'))
        while not Command:
            Command = input()
        mainSocket.sendall(Command.encode('utf-8'))
        # 将消息按空格进行分割，比如command[0] = upload command[1] = filename
        command = Command.split()
        Command = ""
        if command[0] == "list" and len(command) == 1:
            listFile()

        elif (command[0] == "download" and len(command) == 2):
            downloadFile(command[1])

        elif command[0] == "upload" and len(command) == 2:
            if (not command[1]  == "" ):
                uploadFile(command[1])

        elif command[0] == "exit" and len(command) == 1:
            break
        else:
            print("Please input the correct command.")
    
    break
mainSocket.close()
end=time.time()
log('The client quit','OK',end-start)