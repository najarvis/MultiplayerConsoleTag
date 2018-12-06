import socket

PORT = 3210

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', PORT))
while True:
	command = input(">>> ")
	s.send(command.encode())
	data = s.recv(1024)
	print("Recieved:", data)
	if data == b'GOODBYE':
		break
s.close()