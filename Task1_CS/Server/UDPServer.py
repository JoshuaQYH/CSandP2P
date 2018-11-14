import socket
import os
import struct
import sys
import hashlib
import time
filePath = "C:\\Users\\Administrator\\Desktop\\ComNetProject1\\Task1_CS\\Server\\serverData\\"
codepath = "C:\\Users\\Administrator\\Desktop\\ComNetProject1\\Task1_CS\\Server\\Chiper.txt"
BUFFSIZE = 51200
CODESIZE = 64
CODE = "utf-8"


# socket相关配置
# 建立UDP socket
serverAddress = ("127.0.0.1", 3100)
mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mainSocket.bind(serverAddress)
clientAddress = ("127.0.0.1", 3101)


# socket相关功能函数
#获得加密私钥
def getTheKey():
    if not os.path.isfile(codepath):
        print("Can not find the file of the key!\n")
        exit(0)
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




#日志记录函数
def log(actoin,flag,exeTime): 
    outFilePath= filePath+"logServer.txt"
    if os.path.isfile(outFilePath):
        fp=open(outFilePath,'a')
        date=time.asctime(time.localtime(time.time()))
        fp.write(date+'\n'+"Action: "+actoin+'\n'+'Flag: '+flag+'\n'+'Time: ')
        fp.write(str(exeTime))
        fp.write('s\n\n')
        fp.close()
    else:
        print("[Error]:can not open the server log file")
        exit(0)




#进度条函数
def progress_bar(num_cur, total):
    ratio = float(num_cur) / total
    percentage = int(ratio * 100)
    r = '\r[%s%s]%d%%' % (">"*percentage, " "*(100-percentage), percentage )
    sys.stdout.write(r)
    sys.stdout.flush()




# 列出资源文件夹ServerData中的数据文件，发送给客户端
def listFile():
    print("\n**********************************************************************")
    print("Ready to list file")
    start=time.time()
    file_dir = filePath
    for root, dirs, files in os.walk(file_dir):
        # print(root) #当前目录路径
        # print(dirs) #当前路径下所有子目录
        print(files)  # 当前路径下所有非目录子文件
        check = hashlib.md5()
        # files.remove("UDPServer.py")
        fileStr = str(files)
        fileBytes = fileStr.encode(CODE)
        check.update(fileBytes)
        fileBytesChiper = chiperCode(fileBytes)
        mainSocket.sendto(fileBytesChiper, clientAddress)
        mainSocket.sendto(check.hexdigest().encode("utf-8"), clientAddress)
    print("Have sent files!")
    end=time.time()
    log('The client request for the file list','OK',end-start);
    print("**********************************************************************\n")




# 响应客户端下载文件的请求,先满足小型文件传输


def downloadFile(fileName):
    # 打开要传输的文件
    start=time.time()
    file = filePath + fileName
    print("\n**********************************************************************")
    print("send " + file)
    if os.path.isfile(file):
        fsize = str(os.path.getsize(file))
        send_size = 0  # 定义已发送文件的大小
        mainSocket.sendto(fsize.encode("utf-8"), clientAddress)

        fs = open(file, "rb")
        print("Start downloading")
        check = hashlib.md5()
        while True:
            fileData = fs.read(BUFFSIZE)
            if not fileData:
                break
            check.update(fileData)
            time.sleep(0.1)
            mainSocket.sendto(fileData, clientAddress)
            send_size += len(fileData)
            progress_bar(send_size,int(fsize,10))
        mainSocket.sendto(check.hexdigest().encode(CODE), clientAddress)
        print("\nDownload successfully")
        fs.close()
        end=time.time()
        log('The client ask for download the file \''+fileName+'\'','OK',end-start)
    else:
        print("ERROR:can't find file")
        error = "0"
        end=time.time()
        log('The client ask for download the file \''+fileName+'\'','Fail:an error happened',end-start)
        mainSocket.sendto(error.encode("utf-8"), clientAddress)
    print("**********************************************************************\n")




# 接收客户端上传的文件
def upload(fileName):
    print("\n**********************************************************************")
    print("Ready to upload file from client")
    start=time.time()
    try:
        data, addr = mainSocket.recvfrom(BUFFSIZE)
        fsize = int(data, 10)
        if fsize>0:
            file = filePath + fileName
            fs = open(file, "wb")
            recvd_size = 0  # 定义已接收文件的大小
            print("Start uploading")
            check = hashlib.md5()
            while not recvd_size == fsize:
                if fsize - recvd_size > BUFFSIZE:
                    data, addr = mainSocket.recvfrom(BUFFSIZE)
                    check.update(data)
                    recvd_size += len(data)
                    fs.write(data)
                    progress_bar(recvd_size,fsize)
                else:
                    data, addr = mainSocket.recvfrom(fsize - recvd_size)
                    recvd_size = fsize
                    check.update(data)
                    progress_bar(recvd_size,fsize)
                    fs.write(data)
            checkData, addr=mainSocket.recvfrom(32)
            if not (checkData==check.hexdigest().encode(CODE)):
                end=time.time()
                log('The client wish to upload the file \''+fileName+'\' to server','Fail:the file has been broken',end-start)
                print("[Error]:The file may be broken\n")          
            print("\nUpload successfully")
            end=time.time()
            log('The client wish to upload the file \''+fileName+'\' to server','OK',end-start)
            fs.close()
            
        else:
            end=time.time()
            log('The client wish to upload the file \''+fileName+'\' to server','Fail:an error happened',end-start)
            print("ERROR:can't find file")

    except:
        end=time.time()
        log('The client wish to upload the file \''+fileName+'\' to server','Fail:an error happened',end-start)
        print("ERROR:Upload timeout")
    print("**********************************************************************\n")        
    return 0




# 命令部响应客户端请求部分
log('The server open','OK',0)
start=time.time()




while True:
    # 服务器接收客户端消息
    data, addr = mainSocket.recvfrom(BUFFSIZE)
    print("waitting")
    if not data:
        print("Client has exist")
        break
    tmp = data.decode("utf-8")
    text = tmp.split()
    print(text[0] + "---")
    # 收到请求文件的命令 download
    if text[0] == "download" and len(text) == 2:
        downloadFile(text[1])

    elif text[0] == "list" and len(text) == 1:
        listFile()

    elif text[0] == "upload" and len(text) == 2:
        upload(text[1])
    elif text[0] == 'exit':
        break
end=time.time()
log("The server close",'OK',end-start)
mainSocket.close()