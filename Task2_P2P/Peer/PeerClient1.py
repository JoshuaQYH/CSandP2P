import socket 
import os

###############系统相关变量
filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task2_P2P\\Peer\\Peer1Data\\"
BUFFSIZE = 2048

###############通信命令
REGISTER = "register"                        # 请求服务器注册peer
REQUEST = "request"                          # 请求服务器返回资源对应的peer列表
UPDATE = "update"                            # 更新peer资源信息
DOWNLOAD = "download"                        # 请求peer下载资源命令
UPLOAD = "upload"                            # 上传资源给其他peer
EXIT = "exit"                                # 退出客户端
REGISTER_SUCESSFULLY = "register OK"         # 注册成功
REGISTER_FAILED = "register failed"          # 注册失败
DOWNLOAD_SUCESSFULLY = "download OK"         # 下载成功
DOWNLOAD_FAILED = "download failed"          # 下载失败
HAVE_REGISTERED = "have registered"          # 重复注册

###############客户端socket配置
peerClientAddress = ('127.0.0.1', 3132)
mainPeerClientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainPeerClientSocket.bind(peerClientAddress)
serverAddress = ('127.0.0.1', 3131)

############## 向服务器注册peer信息
def registerOnServer():
    """
        发送peer的IP+port，以及已有的资源列表,返回注册状态
    """
    # 得到 IP+PORT的string形式，分隔符为'$' 格式为127.0.0.1$3132$filelist
    ClientAddress_list = list(peerClientAddress)
    dataAddress = '$'.join(ClientAddress_list) 
    # 得到文件资源列表，类型为list，转为 资源1$资源2
    file_dir = filePath    
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        #print(files) #当前路径下所有非目录子文件
        dataFileList = '$'.join(files)
    
    peerData = dataAddress + dataFileList
    mainPeerClientSocket.sendto(peerData.encode('utf-8'), serverAddress)

    # 接收注册状态
    registerData, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
    print(registerData)
    if registerData.decode('utf-8') == REGISTER_SUCESSFULLY:
        print (REGISTER_SUCESSFULLY)
    elif registerData.decode('utf-8') == REGISTER_FAILED:
        print (REGISTER_FAILED)
    elif registerData.decode('uff-8') == HAVE_REGISTERED:
        print (HAVE_REGISTERED)
    return 0

############## 请求服务器返回资源列表
def requestPeerSource(fileName):
    with open(fileName, 'wb') as f:
        while True:
            data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)
            
            if data.decode('utf-8') == DOWNLOAD_SUCESSFULLY:
                print(DOWNLOAD_SUCESSFULLY)
                break
            elif data.decode('utf-8') == DOWNLOAD_FAILED:
                print(DOWNLOAD_FAILED)
                break
            else:
                f.write(data)
    return 0

############## 发出对其他peer的下载,并接收
def downloadSourceFromPeer(FILE,IP,PORT):
    goalAddr = []
    goalAddr.append(IP)
    goalAddr.append(PORT)
    goalAddressTuple = tuple(goalAddr)
    source = DOWNLOAD + " " + FILE  
    mainPeerClientSocket.sendto(source.encode("utf-8"), goalAddressTuple)

    data, addr = mainPeerClientSocket.recvfrom(BUFFSIZE)

    if not data:
        print(DOWNLOAD_FAILED)
    else:
        with open(FILE,'wb') as f:
            while True:
                da, ad = mainPeerClientSocket.recvfrom(BUFFSIZE)
                if da.decode('utf-8') != DOWNLOAD_SUCESSFULLY:
                    f.write(da)
                else:
                    break
    
    return 0

############## 向服务器更新peer信息
def updatePeer():
    # 得到文件资源列表，类型为list，转为 资源1$资源2
    file_dir = filePath 
    dataFileList = []   
    for root, dirs, files in os.walk(file_dir):  
        #print(root) #当前目录路径  
        #print(dirs) #当前路径下所有子目录  
        #print(files) #当前路径下所有非目录子文件
        dataFileList = '$'.join(files)
    
    peerData =  dataFileList
    mainPeerClientSocket.sendto(peerData.encode('utf-8'), serverAddress)
    return 0

############## 接收其他节点的下载请求，发送资源
def uploadSourceToPeer(Address, FILE):
    with open(FILE, 'wb') as f:
        while True:
            data = f.read(BUFFSIZE)
            if not data:
                break
            mainPeerClientSocket.sendto(data.encode('utf-8'), Address)
    return 0

############## 退出客户端，告知服务器关闭本peer资源列表，防止向下线的peer请求
def exitPeerClient():
    mainPeerClientSocket.sendto(EXIT.encode('utf-8'), serverAddress)
    return 0


while True:
     # 发送命令，传给服务器或者其他peer
    msg = input('''Input one of the following command:\n 
                    1. register  -----------------------------register a peer to server\n
                    2. request [filename] ---------------request server for the peers info which have the requested file \n
                    3. download [filename] IP:PORT---------------------download file on the peers \n
                    4. update ------------------------------------------- update this peer to server\n 
                    5. exit  ---------------------------------------- exit the client ''')
    
    if not msg:
        break
    cmd = msg.split()

    if cmd[0] == REGISTER:    #向服务器注册
        registerOnServer()

    elif cmd[0] == DOWNLOAD:  #向其他peer节点下载资源
        fileName = cmd[1]
        IP_DOWNLOAD = cmd[2].split(":")[0]
        PORT_DOWNLOAD = cmd[2].split(":")[1]
        downloadSourceFromPeer(fileName, IP_DOWNLOAD, PORT_DOWNLOAD)

    elif cmd[0] == UPDATE:  # 请求服务器更新节点
        updatePeer()

    elif cmd[0] == REQUEST: # 请求服务器返回文件资源列表
        requestPeerSource(cmd[1])

    elif cmd[0] == EXIT: # 退出客户端，从服务器上注销
        exitPeerClient()
        exit(0)

    # 此处侦听其他节点的资源下载请求
    mainPeerClientSocket.settimeout(0.1)
    try:
        while True:
            data_upload, addr_upload = mainPeerClientSocket.recvfrom(BUFFSIZE)
            if data_upload.decode("utf-8").split(' ')[0] == DOWNLOAD:
                uploadSourceToPeer(addr_upload,data_upload.decode("utf-8").split(' ')[1])
            else:
                break
    except:
        print("no peer asks for source.")   # ---------------------------------

