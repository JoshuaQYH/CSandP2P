import socket 
import os
import unicodedata
import hashlib
from multiprocessing import Process
from multiprocessing import Pool
import json
from time import ctime,sleep
import multiprocessing as mp
import threading
import base64

###############系统相关变量
filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task2_P2P\\Peer\\Peer3Data\\"
BUFFSIZE = 2048
PEER_IP = "127.0.0.1"
PEER_PORT = 8005
PEER_DOWNLOAD_IP = "127.0.0.1"
PEER_DOWNLOAD_PORT = 8006
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8080
cores = 4
FIEL_BLOCK_SIZE = 1024 * 1024

CAN_UPLOADSOURCE_FLAG = True  #  用户上传线程的可上传的标志，用于指示下载队列开始其中一个任务

####################################################################
#########################################文件相关函数接口#############
####################################################################

##########################计算文件MD5值
def calMD5(str):
    m = hashlib.md5()
    m.update(str)
     
    return m.hexdigest()
 
def calMD5ForFile(file):
    statinfo = os.stat(filePath + file)
     
    if int(statinfo.st_size)/(1024*1024) >= 1000 :
        print ("File size > 1000, move to big file...")
        return calMD5ForBigFile(filePath  + file)
    
    m = hashlib.md5()
    f = open(filePath + file, 'rb')
    m.update(f.read())
    f.close()
     
    return m.hexdigest()
 
def calMD5ForFolder(dir,MD5File):
    outfile = open(MD5File,'w')
    for root, subdirs, files in os.walk(dir):
        for file in files:
            filefullpath = os.path.join(root, file)
            """print filefullpath"""
             
            filerelpath = os.path.relpath(filefullpath, dir)
            md5 = calMD5ForFile(filefullpath)
            outfile.write(filerelpath+' '+md5+"\n")
    outfile.close()
 
def calMD5ForBigFile(file):
    m = hashlib.md5()
    f = open(file, 'rb')
    buffer = 8192    # why is 8192 | 8192 is fast than 2048
     
    while 1:
        chunk = f.read(buffer)
        if not chunk : break
        m.update(chunk)
         
    f.close()
    return m.hexdigest()

def calFileListMD5(FileList):
    md5List = []
    for file in FileList:
        md5List.append(calMD5ForFile(file))
    return md5List

#获取文件的大小,结果保留两位小数，单位为MB
def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    fsize = fsize/float(1024*1024)
    return round(fsize,2)

#获取文件资源列表和文件大小，返回一个列表
def getFileList():
    # 得到文件资源列表，类型为list，转为 资源1$资源2
    # 格式为 [ {jsondata1}, {jsondata2} ...]
    file_dir = filePath    
    dataFileList = [] # 文件名+文件大小
    fileSet = []
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        #print(files) #当前路径下所有非目录子文件
        fileSet = files

    for f in fileSet:
        fileSize = get_FileSize(file_dir + f)
        fileMD5 = calMD5ForFile(f)
        fileInfo = dict(fileName=f, fileSize=fileSize, fileMD5 = fileMD5)
        jsonData = json.dumps(fileInfo)
        dataFileList.append(jsonData)

    return dataFileList  

##############################################多进程分发文件
###参数：文件块起始未知，文件块大小
def process_wrapper(chunkStart, chunkSize,fileName, IP, PORT):
    with open(fileName) as f:
        f.seek(chunkStart)
        lines = f.read(chunkSize).splitlines()
        # 分块发包
        mainPeerClientSocket.sendto(lines.encode('utf-8'), (IP, PORT))


#文件分块
def chunkify(fname,size=1024*1024):
    fileEnd = os.path.getsize(fname)
    with open(fname,'r') as f:
        chunkEnd = f.tell()
        while True:
            chunkStart = chunkEnd
            f.seek(size,1)
            f.readline()
            chunkEnd = f.tell()
            yield chunkStart, chunkEnd - chunkStart
            if chunkEnd > fileEnd:
                break

#  文件分块，并实现多进程发包
def sendFIleWithMultiprocess(fileName, IP, PORT):
    pool = Pool(cores)
    jobs = []
    for chunkStart, chunkSize in chunkify(fileName):
        jobs.append(pool.apply_async(process_wrapper, (chunkStart,chunkSize, fileName,IP, PORT)))


###########################################################################
############### 通信命令 ###################################################
###########################################################################
REGISTER = "register"                        # 请求服务器注册peer
REQUEST = "request"                          # 请求服务器返回资源对应的peer列表
UPDATE = "update"                            # 更新peer资源信息
DOWNLOAD = "download"                        # 请求peer下载资源命令
UPLOAD = "upload"                            # 上传资源给其他peer
EXIT = "exit"                                # 退出客户端
REGISTER_SUCESSFULLY = "register OK"         # 注册成功
REGISTER_FAILED = "register failed"          # 注册失败
HAVE_REGISTERED = "have registered"          # 重复注册
UPDATE_SUCESSFULLY = "update OK"             # 更新成功
UPDATE_FAILED = "update failed"              # 更新失败
SEND_SUCESSFULLY = "send OK"                 # 发送成功
SEND_FAILED = "send failed"                  # 发送失败
DELETE_PEER = "delete peer OK"               # 删除节点信息
DOWNLOAD_SUCESSFULLY = "download OK"         # 下载成功
DOWNLOAD_FAILED = "download failed"          # 下载失败
DOWNLOAD_PREPARE = "prepare to download"     # 准备下载
 
###############socket配置
peerClientAddress = (PEER_IP, PEER_PORT)
mainPeerClientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainPeerClientSocket.bind(peerClientAddress)
serverAddress = (SERVER_IP,SERVER_PORT)

peerClientDownloadAddress = (PEER_IP, PEER_DOWNLOAD_PORT)
DownloadSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
DownloadSocket.bind(peerClientDownloadAddress)

##################################################################################
################ 交互函数 #########################################################
##################################################################################


############## 向服务器注册peer信息
def registerOnServer():
    mainPeerClientSocket.sendto(REGISTER.encode('utf-8'), serverAddress)
    """
        发送peer的IP+port，以及已有的资源列表,返回注册状态
    """
    # 将下载端口附加在下载文件列表的首部
    peerData = []
    peerData.append(str(PEER_DOWNLOAD_PORT))
    peerData += getFileList()  
    # 将列表元素分割，分隔符为$，转换为str传输
    mainPeerClientSocket.sendto('$'.join(peerData).encode('utf-8'), serverAddress)
    
    # 接收注册状态
    try:
        registerData, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
        if registerData.decode('utf-8') == REGISTER_SUCESSFULLY:
            print (REGISTER_SUCESSFULLY)
        elif registerData.decode('utf-8') == REGISTER_FAILED:
            print (REGISTER_FAILED)
        elif registerData.decode('utf-8') == HAVE_REGISTERED:
            print (HAVE_REGISTERED)
        else:
            print("其他未知错误")
    except:
        print("超时未响应")
    return 0

############## 请求服务器返回资源列表
def requestPeerSource(fileName):
    cmd = REQUEST+ ' ' + fileName
    mainPeerClientSocket.settimeout(10)
    mainPeerClientSocket.sendto(cmd.encode('utf-8'), serverAddress)
    data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
    print("资源列表：" + data.decode("utf-8"))
    return 0

############## 发出对其他peer的下载,并接收
def downloadSourceFromPeer(FILE,IP_LIST,PORT_LIST):
    # 单点传输
    if len(IP_LIST) == 1:
        goalAddr = []
        goalAddr.append(IP_LIST[0])
        goalAddr.append(PORT_LIST[0])
        goalAddressTuple = tuple(goalAddr)
        source = DOWNLOAD + " " + FILE + " "+ "0"
        mainPeerClientSocket.sendto(source.encode("utf-8"), goalAddressTuple)
        data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)

        if not data:
            print(DOWNLOAD_FAILED)
        elif data.decode('utf-8') == DOWNLOAD_PREPARE:
            try:
                with open( filePath +"Received-" + FILE,'wb') as f:
                    while True:
                        da, ad = mainPeerClientSocket.recvfrom(BUFFSIZE * 2)
                        if da.decode("utf-8") == DOWNLOAD_SUCESSFULLY:
                            print("文件接收成功")
                            break
                        f.write(da)
            except:
                    print("文件接收失败")
                    
    # 双点传输    
    elif len(IP_LIST) == 2:
        goalAddr1 = []
        goalAddr1.append(IP_LIST[0])
        goalAddr1.append(PORT_LIST[0])
        goalAddr1Tuple = tuple(goalAddr1)
        sourceBlock1_CMD = DOWNLOAD + " " + FILE + " " + "1"

        goalAddr2 = []
        goalAddr2.append(IP_LIST[1])
        goalAddr2.append(PORT_LIST[1])
        goalAddr2Tuple = tuple(goalAddr2)
        sourceBlock2_CMD = DOWNLOAD + " " + FILE + " " + "2"

        mainPeerClientSocket.sendto(sourceBlock1_CMD.encode('utf-8'), goalAddr1Tuple)
        mainPeerClientSocket.sendto(sourceBlock2_CMD.encode('utf-8'), goalAddr2Tuple)

        data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
        data1, addr1 = mainPeerClientSocket.recvfrom(BUFFSIZE)

        if not data:
            print(DOWNLOAD_FAILED)
        elif data.decode('utf-8') == DOWNLOAD_PREPARE:
            # 接收两个分组的数据
            # 使用一个列表 dataList 来维护接收的无序的消息队列
            # 当找到有序的消息时就写入文件。
            dataQueue = []  # 该列表会接收暂时无法构成有序分组的消息
            requestNum = 0      # 该数字表示当前文件需要的分组序号
            download1_sucess_flag = False
            download2_sucess_flag = False
            try:
                with open(filePath +"Received-" + FILE,'wb') as f:
                    while True:
                        data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE * 2)
                        if data.decode('utf-8') == DOWNLOAD_SUCESSFULLY + "-1":
                            download1_sucess_flag = True
                        if data.decode('utf-8') == DOWNLOAD_SUCESSFULLY + "-2":
                            download2_sucess_flag = True
                        if download1_sucess_flag == True and download2_sucess_flag == True:
                            break

                        if download1_sucess_flag != True and download2_sucess_flag != True:
                            raw_data = json.loads(data.decode('utf-8')) # 将字符串转为dict(Num , fileData_base64)
                            packetNum = raw_data["Num"]
                            file_block_data = base64.b64decode(raw_data["Data"]) # base4字符串解码成文件字节码
                            # 当前消息是需要的序号分组，那么就会读入文件
                            if packetNum == requestNum:
                                f.write(file_block_data)
                                requestNum += 1
                            else:
                                # 当前消息不是需要的序号分组，那么会加入队列
                                packet = dict(Num = packetNum, Data = file_block_data)
                                dataQueue.append(packet)
                                # 查找队列中有无需要的序号有则添加
                                index = 0
                                while True:
                                    if index >= len(dataQueue):
                                        break
                                    if dataQueue[index]["Num"] == requestNum:
                                        f.write(dataQueue[index]["Data"])
                                        dataQueue.pop(index)
                                        index -= 1
                                        requestNum+= 1       
                                    index += 1

                        
                    #socket 接收完毕，清除队列里的信息。    
                    if len(dataQueue) != 0:
                        index = 0
                        while True:
                            if index >= len(dataQueue):
                                break
                            if dataQueue[index]["Num"] == requestNum:
                                f.write(dataQueue[index]["Data"])
                                dataQueue.pop(index)
                                index -= 1
                                requestNum+= 1       
                            index += 1
                    print("接收文件成功")
            except:
                print("接收文件失败")
    return 0

############## 向服务器更新peer信息
def updatePeer():
    mainPeerClientSocket.sendto(UPDATE.encode('utf-8'), serverAddress)
    peerData = []
    peerData.append(str(PEER_DOWNLOAD_PORT))
    peerData += getFileList()  
    mainPeerClientSocket.sendto('$'.join(peerData).encode('utf-8'), serverAddress)
    data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
    if data.decode("utf-8") == UPDATE_SUCESSFULLY:
        print(UPDATE_SUCESSFULLY)
    else:
        print(UPDATE_FAILED)
    return 0


############## 退出客户端，告知服务器关闭本peer资源列表，防止向下线的peer请求
def exitPeerClient():
    mainPeerClientSocket.sendto(EXIT.encode('utf-8'), serverAddress)
    return 0

############## 接收其他节点的下载请求，发送资源
def uploadSourceToPeer(Address, FILE, FLAG):
    CAN_UPLOADSOURCE_FLAG = False
    # FLAG = 0直接发送； FLAG = 1分包，发送第奇数个包 FLAG = 2分包，发送第偶数个包
    DownloadSocket.sendto(DOWNLOAD_PREPARE.encode('utf-8'), Address)
    if FLAG == "0":  # 直接分组打包发送
        print("发送文件给其他节点中~")
        try:
            print("待发送的文件是：" + filePath + FILE)
            with open(filePath + FILE, 'rb') as f:
                while True:
                    data = f.read(BUFFSIZE)
                    if not data:
                        DownloadSocket.sendto(DOWNLOAD_SUCESSFULLY.encode("utf-8"), Address)
                        break
                    DownloadSocket.sendto(data, Address)
        except:
            DownloadSocket.sendto(DOWNLOAD_FAILED.encode('utf-8'), Address)
            print("0-发送文件失败")
        print("发送文件完毕")
    elif FLAG == "1":  # 分组，将数据装在json数据中发送， 数据格式 {Num： Data：}
        num = 0  
        print("1-发送文件给其他节点中~")
        try:
            with open(filePath + FILE, 'rb') as f:
                while True:
                    data = f.read(BUFFSIZE)
                    if num % 2 == 0:
                        num += 1
                        continue
                    
                    if not data:
                        break
                    # 将数据转换为base64字节码,便于在json文本中存储
                    base64_data_bytes = base64.b64encode(data)
                    # 字节码转换为字符串
                    base64_data_string = base64_data_bytes.decode('utf-8')
                    data_dict = dict(Num = num, Data = base64_data_string)
                    jsonData = json.dumps(data_dict)
                    print("1-" + jsonData)
                    DownloadSocket.sendto(jsonData.encode('utf-8'), Address)
                    num += 1  # 分组序号+1
            DownloadSocket.sendto((DOWNLOAD_SUCESSFULLY + "-1").encode("utf-8"), Address)
            print("发送文件完毕")
        except:
            DownloadSocket.sendto(DOWNLOAD_FAILED.encode('utf-8'), Address)
            print("0-发送文件失败")
        
    elif FLAG == "2":
        num = 0
        print("2-发送文件给其他节点中~")
        try:
            with open(filePath + FILE, 'rb') as f:
                while True:
                    data = f.read(BUFFSIZE)
                    if num % 2 == 1:
                        num += 1
                        continue
                    if not data:
                        break
                    # 将数据转换为base64字节码,便于在json文本中存储
                    base64_data_bytes = base64.b64encode(data)
                    # 字节码转换为字符串
                    base64_data_string = base64_data_bytes.decode('utf-8')
                    data_dict = dict(Num = num, Data = base64_data_string)
                    jsonData = json.dumps(data_dict)
                    print("2-" + jsonData)
                    DownloadSocket.sendto(jsonData.encode('utf-8'), Address)
                    num += 1
            DownloadSocket.sendto((DOWNLOAD_SUCESSFULLY + "-2").encode("utf-8"), Address)
            print("发送文件完毕")
        except:
            DownloadSocket.sendto(DOWNLOAD_FAILED.encode('utf-8'), Address)
            print("0-发送文件失败")
        
    CAN_UPLOADSOURCE_FLAG = True
    return 0

############新开一个线程 等待其他节点的下载请求
def waitPeerToDownLoadSource():
    print("此处侦听其他节点的资源下载请求")
    DownloadSocket.settimeout(10)  # 每隔0.2 秒监听一下资源请求
    requestPeerQueue = []
    while True:
        try:
            data_upload, addr_upload = DownloadSocket.recvfrom(BUFFSIZE)    
            if data_upload.decode("utf-8").split(' ')[0] == DOWNLOAD:
                print("其他节点请求资源中")
                temp_addr_upload = addr_upload
                temp_fileName_upload = data_upload.decode("utf-8").split(' ')[1]
                temp_flag_upload = data_upload.decode("utf-8").split(' ')[2]
                # 加入队列中
                requestPeerQueue.append(dict(addr = temp_addr_upload, fileName = temp_fileName_upload,
                                        flag = temp_flag_upload))
                if CAN_UPLOADSOURCE_FLAG == False:
                    print("加入资源请求队列中")
                elif len(requestPeerQueue) != 0:
                    uploadThread = threading.Thread(target=uploadSourceToPeer, 
                    args=(requestPeerQueue[0]["addr"], requestPeerQueue[0]["fileName"], requestPeerQueue[0]["flag"]))
                    uploadThread.start()
            else:
                print("非上传请求")
        except:
            if closeFlag == True:
                exit(0)
            pass

###########################################################################
############################## 命令处理 ####################################
###########################################################################
## 处理输入的线程
def cmdFuncThread():
    while True:
        mainPeerClientSocket.settimeout(10)
        # 发送命令，传给服务器或者其他peer
        msg = input('''Input one of the following command:\n 
                            1. register  -----------------------------register a peer to server\n
                            2. request [filename] ---------------request server for the peers info which have the requested file \n
                            3. download [filename] IP:PORT---------------------download file on the peers \n
                            4. update ------------------------------------------- update this peer to server\n 
                            5. exit  ---------------------------------------- exit the client \n''')
        if not msg:
            break
        cmd = msg.split()

        if cmd[0] == REGISTER:    #向服务器注册
            registerOnServer()

        elif cmd[0] == DOWNLOAD:  #向其他peer节点下载资源
            fileName = cmd[1]
            IP_DOWNLOAD_LIST = []
            PORT_DOWNLOAD_LIST = []
            IP_DOWNLOAD1 = cmd[2].split(":")[0]
            IP_DOWNLOAD_LIST.append(IP_DOWNLOAD1)
            PORT_DOWNLOAD1 = int(cmd[2].split(":")[1])
            PORT_DOWNLOAD_LIST.append(PORT_DOWNLOAD1)
            if len(cmd) == 4:
                IP_DOWNLOAD2 = cmd[3].split(":")[0]
                PORT_DOWNLOAD2 = int(cmd[3].split(":")[1])
                IP_DOWNLOAD_LIST.append(IP_DOWNLOAD2)
                PORT_DOWNLOAD_LIST.append(PORT_DOWNLOAD2)
            downloadSourceFromPeer(fileName, IP_DOWNLOAD_LIST, PORT_DOWNLOAD_LIST)

        elif cmd[0] == UPDATE:  # 请求服务器更新节点
            updatePeer()

        elif cmd[0] == REQUEST: # 请求服务器返回文件资源列表
            requestPeerSource(cmd[1])

        elif cmd[0] == EXIT: # 退出客户端，从服务器上注销
            exitPeerClient()
            exit(0)
            closeFlag = True
        else:
            print("收到未知命令，忽略")

# 等待节点下载的线程
def waitPeerThread():
    waitPeerToDownLoadSource()
    return 0

if __name__=='__main__': 
   closeFlag = False      
   t1 = threading.Thread(target = cmdFuncThread)
   t2 = threading.Thread(target = waitPeerThread)
   t1.start()
   t2.start()
   t1.join()
   t2.join()
   
