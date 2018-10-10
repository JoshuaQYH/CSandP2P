import socket

serverAddress = ('127.0.0.1', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ('127.0.0.1', 31501)
s.bind(clientAddress)
while True:
    # 接受输入，传给服务器
    msg = input("input ")
    if not msg:
        break
    s.sendto(msg.encode(), serverAddress)
    data, addr = s.recvfrom(2048)
    
    # 接受服务器的消息
    if not data:
        print("no data from server")
        continue
    print (data.decode())
    
s.close()