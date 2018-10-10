import socket

serverAddress = ('127.0.0.1', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(serverAddress)

clientAddress = ('127.0.0.1',31501)
while True:
    #服务器接收客户端消息
    data, addr = s.recvfrom(2048)
    if not data:
        print ("client has exist")
        break
    print (data.decode())
    # 同时发送消息
    s.sendto(data, clientAddress)
s.close()
