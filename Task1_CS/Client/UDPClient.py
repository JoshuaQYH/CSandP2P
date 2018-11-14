import socket
import sys
import os
import struct
import hashlib
import time


# 变量初始化
# 服务端下载的文件的的存放路径
filePath = "C:\\Users\\Administrator\\Desktop\\ComNetProject1\\Task1_CS\\Client\\clientData\\"
codepath = "C:\\Users\\Administrator\\Desktop\\ComNetProject1\\Task1_CS\\Client\\Chiper.txt"
BUFFSIZE = 51200
CODESIZE = 64
CODE = "utf-8"



# socket配置相关
# 服务端地址
serverAddress = ('172.18.32.213', 3100)
# 创建客户端socket
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ('172.18.35.237', 3101)
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
    #mainSocket.settimeout(1)
    try:
        clientData, clientAddr = mainSocket.recvfrom(BUFFSIZE)
        clientData = chiperCode(clientData)
        check=hashlib.md5()
        check.update(clientData)
        checkResult=check.hexdigest()
        fileList = clientData.decode('utf-8')
        checkData, addr = mainSocket.recvfrom(32)
        if not (checkData==checkResult.encode(CODE)):
            print("[Error]:The package from server may be broken\n")
        else:
            fileList = clientData.decode('utf-8')
            print(fileList)
            print("All Files on server are here.")
            end=time.time()
            log("Ask for the file list from server",'OK',end-start)
    except ConnectionResetError:
        print("[Error]: Port is wrong")
        end=time.time()
        log("Ask for the file list from server",'Fail:an connection error happened',end-start)
    except:
        end=time.time()
        log("Ask for the file list from server",'Fail:an unkown error happened',end-start)
        print("Timeout or some other errors")   
    print("**********************************************************************\n")
    return 0




def judgeFileName(fileName):
    return False



# 发送下载命令，请求服务端返回该文件并接收保存，接收服务端消息提示

def downloadFile(fileName):
    print("\n**********************************************************************")
    print("Ready to download file from server")
    start=time.time()
    mainSocket.settimeout(10)
    try:
        data, addr = mainSocket.recvfrom(BUFFSIZE)
        fsize = int(data, 10)
        if fsize>0:
            file = filePath + fileName
            fs = open(file, 'wb')
            recvd_size = 0  # 定义已接收文件的大小
            check=hashlib.md5()
            print("start downloading...")
            while not (recvd_size == fsize):
                if fsize - recvd_size > BUFFSIZE:
                    data, addr = mainSocket.recvfrom(BUFFSIZE)
                    recvd_size += len(data)
                    check.update(data)
                    fs.write(data)
                    progress_bar(recvd_size,fsize)
                    
                else:
                    data, addr = mainSocket.recvfrom(fsize - recvd_size)
                    check.update(data)
                    recvd_size = fsize
                    fs.write(data)
                    progress_bar(recvd_size,fsize)
            fs.close()
            checkData, addr = mainSocket.recvfrom(32)
            if not (checkData == check.hexdigest().encode('utf-8')):
                end=time.time()
                log("Request for the file \'"+fileName+"\' from server",'Fail:file has been broken',end-start)
                print("Error：the file may be broken")

            end=time.time()
            log("Request for the file \'"+fileName+"\' from server",'OK',end-start)
            print("\nDownload successfully")
            return 0
        else:
            end=time.time()
            log("Request for the file \'"+fileName+"\' from server",'Fail:file not found',end-start)
            print("ERROR:can't find file")
    except:
        end=time.time()
        log("Request for the file \'"+fileName+"\' from server",'Fail:timeout when get the file',end-start)
        print("ERROR:download timeout")   
    print("**********************************************************************\n")    
    return 0



# 发送文件给服务端，上传命令后发送文件，最后接收服务端消息提示do

def uploadFile(fileName):
     # 检测当前目录是否存在该文件
    print("\n**********************************************************************")
    file = filePath + fileName
    start=time.time()
    print("send " + file)
    if os.path.isfile(file):
        fsize = str(os.path.getsize(file))
        send_size = 0  # 定义已发送文件的大小
        mainSocket.sendto(fsize.encode('utf-8'), serverAddress)

        fs = open(file, 'rb')
        print("Start uploading")
        check=hashlib.md5()
        while True:
            fileData = fs.read(BUFFSIZE)
            if not fileData:
                break
            check.update(fileData)
            time.sleep(0.1)
            mainSocket.sendto(fileData, serverAddress)
            send_size += len(fileData)
            progress_bar(send_size,int(fsize,10))
        print("\nUpload successfully")
        fs.close()
        checkData=check.hexdigest().encode('utf-8')
        mainSocket.sendto(checkData, serverAddress)
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
    msg = input('''\nInput one of the following command:\n 
                    * list  ------------------- list the files on server \n
                    * download [filename] -----download file from server\n
                    * upload [filename] -----------upload file to server \n
                    * exit ---------------------------------close socket\n ''')

    if not msg:
        break
    mainSocket.sendto(msg.encode('utf-8'), serverAddress)
    # 将消息按空格进行分割，比如command[0] = upload command[1] = filename
    command = msg.split()

    if command[0] == "list" and len(command) == 1:
        listFile()

    elif (command[0] == "download" and len(command) == 2):
        downloadFile(command[1])


    elif command[0] == "upload" and len(command) == 2:
        if (not command[1]  == "" ):
            uploadFile(command[1])

    elif command[0] == "exit" and len(command) == 1:
        mainSocket.close()
        break

    else:
        print("Please input the correct command.")
end=time.time()
log('The client quit','OK',end-start)