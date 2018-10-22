import socket 
import os
import sqlite3
import pandas as pd

################## 系统相关变量 ######################################
BUFFSIZE = 2048
filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task2_P2P\\Server\\"
dataBaseName = 'peerInfo.sqlite' 

############### 通信命令 ############################################
REGISTER = "register"                        # 请求服务器注册peer
REQUEST = "request"                          # 请求服务器返回资源对应的peer列表
UPDATE = "update"                            # 更新peer资源信息
DOWNLOAD = "download"                        # 请求peer下载资源命令
UPLOAD = "upload"                            # 上传资源给其他peer
EXIT = "exit"                                # 退出客户端
REGISTER_SUCESSFULLY = "register OK"         # 注册成功
REGISTER_FAILED = "register failed"          # 注册失败
HAVE_REGISTERED = "have registered"          # 重复注册

###################### 连接数据库 ###########################################
conn = sqlite3.connect("peerInfo.sqlite")
cur = conn.cursor()
cur.execute('''create table PEERINFO if not exist
               (IP text, PORT integer, FILELIST MEMO)''') # MEMO支持更长的字符串


###############  服务端socket配置  ###########################################
serverAddress = ('127.0.0.1', 3131)
mainServerSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainServerSocket.bind(serverAddress)

################  SQL语句生成  ##################################################

def updateSQL(IPAddress, Port, FileList):
    sql = "update PEERINFO set FILELIST = " + FileList + " where IP =" + IPAddress +" AND PORT = " + Port
    return sql

##################### 根据资源名称寻找资源所在的IP列表
# def requestSQL(FileSourceName):
   

def checkIPSQL(IPAddress, Port):
    sql = "select * from PEERINFO where " + "IP = " + IPAddress + " AND PORT = " + Port
    return sql


################ 交互函数 #########################################################

##############接收peer客户端的注册 
def registerPeer(peerAddr):
    data, addr = mainServerSocket.recvfrom(BUFFSIZE)
    fileList = ' '.join((data.split("$"))[2:])  
    checkAddrSql = checkIPSQL(addr[0], addr[1])
    registerFlag = cur.execute(checkAddrSql).fetchall()
    try:
        if not registerFlag:
            cur.execute("insert info PEERINFO values (?,?,?)", addr[0], addr[1], fileList)
            mainServerSocket.sendto(REGISTER_SUCESSFULLY.encode('utf-8'), addr)
            conn.commit()
        else:
            mainServerSocket.sendto(HAVE_REGISTERED.encode('utf-8'), addr)
    except:
        mainServerSocket.sendto(REGISTER_FAILED.encode('utf-8'),addr)

    return 0

##############接收客户端资源请求，返回对应资源peer列表
def requestPeer(FileSourceName):
    sqlDataFrame = pd.read_sql_query("select * from PEERINFO")
    IPANDPORT = []
    for index, row in sqlDataFrame.iterrows():
        fileList = (row["FILELIST"]).split("$")
        ipAndPort = []
        for file in fileList:
            if file == FileSourceName:
                ipAndPort.append(row["IP"])
                ipAndPort.append(row["PORT"])
                break
    return IPANDPORT     
  
    
#############peer发出更新
def updatePeer(peerClientAddress, peerSource):
    updateSql = updateSQL(peerClientAddress[0],peerClientAddress[1], peerSource)
    cur.execute(updateSql)
    conn.commit()
    return 0


############################## 命令处理 ####################################

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
        requestPeer(text[1])

    elif text[0] == UPDATE:
        peerSource = ((text[1].decode('utf-8')).split("$"))[2:]
        updatePeer(peerAddr, ' '.join(peerSource))
    