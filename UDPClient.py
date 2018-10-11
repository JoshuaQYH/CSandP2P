import socket

savedFileName = "saveData.txt"

def sockClient():
    serverAddress = ('127.0.0.1', 31500)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientAddress = ('127.0.0.1', 31501)
    s.bind(clientAddress)
    while True:
        # 发送请求，传给服务器
        msg = input("Input the command:")
        
        if not msg:
            break

        s.sendto(msg.encode(), serverAddress)
        
        # 接受服务器的消息
        data, addr = s.recvfrom(2048)
        if not data:
            print("no data from server")
            continue

        # 捕获接收文件的信号 START
        if data == b'START':
            # 打开文件，开始写入数据保存
            print("开始接收文件")
            with open(savedFileName, 'wb') as fw:
                while True:
                    data, addr = s.recvfrom(1024)
                    if data == b'END':
                        print("结束接收文件")
                        break
                    else:
                        fw.write(data)
                        print("正在写入文件")
                fw.close()
       
     # 关闭socket    
    s.close()

if __name__ == "__main__":
    sockClient()