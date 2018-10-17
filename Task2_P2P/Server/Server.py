import socket 
import os
import sqlite3
import pandas as pd

################## 系统相关变量
BUFFSIZE = 2048
filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task2_P2P\\Server\\"
dataBaseName = 'peerInfo.sqlite' 

###############通信命令
REGISTER = "register"                        # 请求服务器注册peer
REQUEST = "request"                          # 请求服务器返回资源对应的peer列表
UPDATE = "update"                            # 更新peer资源信息
DOWNLOAD = "download"                        # 请求peer下载资源命令
UPLOAD = "upload"                            # 上传资源给其他peer
EXIT = "exit"                                # 退出客户端
REGISTER_SUCESSFULLY = "register OK"         # 注册成功
REGISTER_FAILED = "register failed"          # 注册失败


###############服务端socket配置
serverAddress = ('127.0.0.1', 3131)
mainServerSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainServerSocket.bind(serverAddress)


##############接收peer客户端的注册 
def registerPeer(peerAddr):
    data, addr = mainServerSocket.recvfrom(BUFFSIZE)
    df = pd.DataFrame(data)
    # 注册，上线
    # 打开数据库，检查有该IP端口的记录，有则更新，无则添加记录
   # with sqlite3.connect('peerInfo.sqlite') as db:
       # sql = "selcet * from peerInfo where IP"

    return 0

##############接收客户端资源请求，返回对应资源peer列表
def requestPeer(peerClientAddress, requestSource):
    return 0
    
#############peer发出更新
def updatePeer(peerClientAddress, peerSource):
    return 0

#############保存peer点的地址+资源列表 
def savePeerRecord(peerSocket, peerSourceList):
    return 0



while True:
    # 服务端接收peer消息
    peerData, peerAddr = mainServerSocket.recvfrom(BUFFSIZE)
    if not peerData:
        print ("client has stop.")
    # 开始解析客户端命令
    cmd = peerData("utf-8")
    text = cmd.spilt()

    if text[0] == REGISTER:
        registerPeer(peerAddr)

    elif text[0] == REQUEST:
        requestPeer(peerAddr, peerData)

    elif text[0] == UPDATE:
        updatePeer(peerAddr, peerData)


    
    