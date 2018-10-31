import socket 
import os
import sqlite3
import pandas as pd
import time
import json
try:
    import cPickle as pickle
except ImportError:
    import pickle
################## 系统相关变量 ######################################
BUFFSIZE = 2048
filePath = "C:\\Users\\Qiuyh\\Desktop\\ComNetProject1\\Task2_P2P\\Server\\"
dataBaseName = 'peerInfo.sqlite' 
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8080


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
DOWNLOAD_FAILED = "download OK"              # 下载失败
 
#### 通信状态码
SERVER_ERROR = "服务器发生错误"



#############################################################################
###############  服务端socket配置  ###########################################
#############################################################################
serverAddress = (SERVER_IP, SERVER_PORT)
mainServerSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainServerSocket.bind(serverAddress)
print("服务器地址绑定成功")



############################################################################
###################### 数据库相关 ###########################################
############################################################################

##################peer信息表格设计
"""
           Table PeerInfo 表格记录节点IP端口，以及是否注册
 |   IP |   PORT  | REGISTER_TIMESTAMP | DOWNLOAD_PORT
 --------------------------------------------------------------------
 节点地址| 节点端口 |   注册时间戳       | 下载端口

       Table PeerSource 每一项记录一个文件即源IP和端口
 |   IP |   DOWNLOAD_PORT  |  FILE    |     SIZE    | FILEMD5 |  REGISTER_FLAG | UPDATE_TIMESTAMP
--------------------------------------------------------------------------------------------------
   下载IP| 下载端口         | 文件资源名|文件大小（MB）| 文件MD5值 | 节点注册标志   |  资源更新时间戳
                            
"""
####################连接数据库###########################
conn = sqlite3.connect(filePath + dataBaseName)
print ("连接数据库成功！")
cur = conn.cursor()
try:
    cur.execute('''Create TABLE PeerInfo 
                (IP text, PORT integer, REGISTER_TIMESTAMP timestamp, DOWNLOAD_PORT);''') # MEMO支持更长的字符串
    cur.execute('''Create TABLE PeerSource(IP text, DOWNLOAD_PORT integer, FILE VARCHAR(20), SIZE FLOAT(2), 
            FILEMD5 text,REGISTER_FLAG BOOLEAN, UPDATE_TIMESTAMP timestamp);
            ''')
    print ("创建表格成功！")
except:
    print("表格已存在")
conn.commit()

##############################################################
#############################执行SQL语句#######################
############################################################### 

###############更新资源表
# 2. 插入新的资源记录
# 3. 更新成功返回true
def updatePeerSourceSQL(IPAddress, DOWNLOAD_Port, File, FileSize, FileMD5):
   registerFlag = True
   update_timeStamp =  time.strftime('%Y-%m-%d %H:%M:%S')
   updateSql = "insert into PeerSource values (?, ?, ?, ?, ?, ?, ?);"
   cur.execute(updateSql, (IPAddress, DOWNLOAD_Port, File, FileSize, FileMD5, registerFlag, update_timeStamp)) 
   print("更新资源ing：" + File)
   conn.commit()
   return True

##############查找语句，根据资源名称寻找资源所在的IP列表
# 1. 按资源名称查找，返回查询的列表
def requestSQL(FileSourceName):
    sql = "select * from PeerSource where FILE = ?"
    sourceList = cur.execute(sql, (FileSourceName,)).fetchall()
    return sourceList
   
###############查询语句，查询是否注册过，防止重复注册
# 1. 查询信息表
# 2. 注册了返回真
def checkIPSQL(IPAddress, Port):
    sql = "select * from PeerInfo where " + "IP = \'" + IPAddress + "\' AND PORT = \'" + str(Port) + "\';"
    registerList = cur.execute(sql).fetchall()
    if not registerList:
        return False
    else:
        return True

###############删除语句，用户退出时对应信息表记录和资源表记录
def deletePeerInfoAndSource(IPAddress, Port):
    deleteInfoSql = "delete from PeerInfo where IP = \'" + IPAddress + "\' AND PORT = \'" + str(Port) + "\';"
    cur.execute(deleteInfoSql)
    deleteSourceSql = "delete from PeerSource where IP = \'" + IPAddress + "\' AND DOWNLOAD_PORT = \'" + str(Port) + "\';"
    cur.execute(deleteSourceSql)
    conn.commit()
    return False

###############插入节点信息到信息表中
def registerPeerInfo(IPAddress, Port, DOWNLOAD_PORT):
    sql = "insert into PeerInfo values(?,?,?,?)"
    register_timeStamp =  time.strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql, (IPAddress, Port, register_timeStamp, DOWNLOAD_PORT))
    conn.commit()


##################################################################################
################ 交互函数 #########################################################
##################################################################################

##############接收peer客户端的注册 
def registerPeer(peerAddr):
    data, addr = mainServerSocket.recvfrom(BUFFSIZE)
    fileList = ((data.decode('utf-8')).split("$"))  # 转换为json列表
    register_flag =  checkIPSQL(addr[0], str(addr[1]))
    try:
        if not register_flag:
            print("---"+"准备注册")
            registerPeerInfo(addr[0], addr[1], fileList[0])
            for fileJson in fileList[1:]:
                jsonDict = json.loads(fileJson)
                updatePeerSourceSQL(addr[0], int(fileList[0]), jsonDict["fileName"], float(jsonDict["fileSize"]), jsonDict["fileMD5"])
            conn.commit()
            mainServerSocket.sendto(REGISTER_SUCESSFULLY.encode('utf-8'),addr)
            print(str(peerAddr) + "---注册成功")
        else:
            print(str(peerAddr) + "---"+"该IP端口已注册")
            mainServerSocket.sendto(HAVE_REGISTERED.encode('utf-8'),addr) 
    except:
        mainServerSocket.sendto(REGISTER_FAILED.encode('utf-8'),addr)
        print(str(peerAddr) + "---"+"注册过程发生错误")

   

##############接收客户端资源请求，返回对应资源peer列表

def requestPeer(FileSourceName, PeerAddr):
    try:
        List = requestSQL(FileSourceName)
        mainServerSocket.sendto(str(List).encode('utf-8'), PeerAddr) 
        print("资源列表为" + str(List))  
        print("---"+"To peer:" +  str(PeerAddr) +"发送资源列表成功")     
    except:
        mainServerSocket.sendto(SEND_FAILED.encode('utf-8'), PeerAddr)
        print("---"+"To peer:" +  str(PeerAddr) +"发送资源列表失败")     
  
    
#############peer发出更新
def updatePeer(peerClientAddress):
    data, addr = mainServerSocket.recvfrom(BUFFSIZE) 
    fileList = (((data.decode('utf-8')).split("$"))) 
    deleteSql = "delete from PeerSource  where IP =  \'" + addr[0] + "\' AND DOWNLOAD_PORT = \'" + fileList[0] + "\';"
    cur.execute(deleteSql)
    try:
        for fileJson in fileList[1:]:
            jsonDict = json.loads(fileJson)
            updatePeerSourceSQL(addr[0], int(fileList[0]), jsonDict["fileName"], float(jsonDict["fileSize"]), jsonDict["fileMD5"])
        
        mainServerSocket.sendto(UPDATE_SUCESSFULLY.encode('utf-8'),addr)
        print("---"+str(peerClientAddress) + " 节点更新成功")
    except:
        mainServerSocket.sendto(UPDATE_FAILED.encode('utf-8'),addr)
        print("---"+str(peerClientAddress) + "节点更新失败")
    return 0

#############节点退出，删除节点任何记录
def exitPeer(IPAddress, Port):
    try:
        deletePeerInfoAndSource(IPAddress, Port)
        mainServerSocket.sendto(DELETE_PEER.encode('utf-8'), (IPAddress, Port))
        print("---删除节点 for" + str(IPAddress) + ":" + str(Port))
    except:
        print("---节点删除失败 for" + str(IPAddress) + ":" + str(Port))


###########################################################################
############################## 命令处理 ####################################
###########################################################################
if __name__=='__main__':
    text = []
    while True:
        # 服务端接收peer消息
        print("默默等待节点信息....")
        peerData, peerAddr = mainServerSocket.recvfrom(BUFFSIZE)
        if not peerData:
            print ("client has stop.")
        # 开始解析客户端命令
        cmd = peerData.decode('utf-8')
        text = cmd.split()
        print("节点命令：" + str(cmd))
        #print(SERVER_ERROR)
        #mainServerSocket.sendto(SERVER_ERROR.encode('utf-8'), peerAddr
        if text[0] == REGISTER:
            print("---------------------")
            registerPeer(peerAddr)

        elif text[0] == REQUEST:
            print("---------------------")
            requestPeer(text[1],peerAddr)

        elif text[0] == UPDATE:
            print("---------------------")
            if checkIPSQL(peerAddr[0], peerAddr[1]):
                updatePeer(peerAddr)
            else:
                print(str(peerAddr) + " 该节点为注册")
                info = "请先注册"
                mainServerSocket.sendto(info.encode('utf-8'), peerAddr)

        elif text[0] == EXIT:
            print("---------------------")
            exitPeer(peerAddr[0], peerAddr[1])
            
        else:
            print("收到未知命令，忽略")

