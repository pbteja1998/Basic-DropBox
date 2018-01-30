from socket import *
import os
import signal
import time

tcp_socket = socket(AF_INET, SOCK_STREAM)
udp_socket = socket(AF_INET, SOCK_DGRAM)

host = gethostname()
tcp_port = 60003
udp_port = 60004

tcp_socket.connect((host, tcp_port))
udp_socket.bind((host, udp_port))


class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

def nonBlockingRawInput(prompt='', timeout=5):
    signal.signal(signal.SIGALRM, alarmHandler)
    signal.alarm(timeout)
    try:
        text = raw_input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        print '\nPrompt timeout. Continuing...'
        prompt_flag = 0
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''

def list_of_files():
	return os.popen("ls User2").read()

def sync():
	print "Started Syncing"
	tcp_socket.send("index list")
	files = tcp_socket.recv(1024)
	if files == "empty":
		return
	else:
		files = files.split()
	for file in files:
		tcp_socket.send("download UDP " + file)
		print "trying to download " + file
		os.chdir("User1")
		intermediate_download_from_server()
		os.chdir("..")

initial_time = time.time()

def download_udp(filename):
	print "downloading files"
	file_content = ''
	
	while True: 
		data, addr = udp_socket.recvfrom(1024)
		if data == "DONE":
			break
		file_content = file_content + data
	

	f = open( filename, 'w')
	f.write(file_content)
	f.close()

	perm = tcp_socket.recv(1024) 

	print "permissions of file " + filename + " in user2 folder is " + str(perm)
	# a = os.popen("chmod " + str(perm) + " " + filename).read()
	os.chmod(filename, int(perm,8))
	print "set the permissions of file " + filename + " in user1 folder to " + str(perm)

	print os.popen("ls -l " + filename).read()

	md5sum2 = tcp_socket.recv(1024)

	md5sum1 = os.popen("md5sum " + filename).read().split()
	md5sum2 = md5sum2.split()
	
	if md5sum1[0] == md5sum2[0]:
		print "File is successfully recieved"
		tcp_socket.send("Success")
		time.sleep(2)
		file_info = tcp_socket.recv(1024)
		print filename
		print file_info
	else:
		tcp_socket.send("Failure")
		time.sleep(2)
		print "File is broken"
		download_udp(filename)

def download_tcp(filename):
	print "downloading using tcp"
	print "downloading files"
	file_content = ''
	
	while True: 
		data = tcp_socket.recv(1024)
		if data == "DONE":
			break
		file_content = file_content + data
	
	print file_content
	f = open(filename, 'w')
	f.write(file_content)
	f.close()

	perm = tcp_socket.recv(1024)
	print "permissions of file " + filename + " in user2 folder is " + str(perm)
	os.chmod(filename, int(perm,8))
	print "set the permissions of file " + filename + " in user1 folder to " + str(perm)


	file_info = tcp_socket.recv(1024)
	print filename
	print file_info

def intermediate_download_from_server ( protocol = "UDP" ):
	print ""
	print ""
	recievingFile = tcp_socket.recv ( 1024 )
	print "found that it is a " + recievingFile

	if recievingFile == "directory":
		directory = tcp_socket.recv ( 1024 )
		
		print "name of the directory is " + directory 

		try:
			os.chdir(directory)
			print "Changed to directory " + directory

		except:
			os.mkdir ( directory )
			os.chdir ( directory )
			print "Created and changed to directory " + directory

		files = tcp_socket.recv ( 1024 )
		print "directory " + directory + " has " + files + " files"
		for i in range ( int ( files ) ):
			intermediate_download_from_server ( protocol )
		os.chdir ( ".." )
	else:
		filename = tcp_socket.recv ( 1024 )
		print "name of the file is " + filename

		if os.path.exists(filename):
			print "file " + filename + " exists in user1 folder"

			tcp_socket.send("exists")
			time.sleep(2)
			md5sum1 = tcp_socket.recv(1024).split()

			print "md5sum of file " + filename + " in user2 folder is " + md5sum1[0]

			md5sum2 = os.popen("md5sum " + filename).read().split()

			print "md5sum of file " + filename + " in user1 folder is " + md5sum2[0]

			if md5sum1[0] != md5sum2[0]:
				tcp_socket.send("continue")
				print "file contents of both files are not same"

				mtime1 = tcp_socket.recv(1024)
				print "modified time of file "+ filename +" in user2 folder is " + mtime1

				mtime2 = os.path.getmtime(filename)
				print "modified time of file "+ filename +" in user1 folder is " + str(mtime2)

				if float(mtime1) > float(mtime2):
					print "file in user2 folder is latest"
					tcp_socket.send("continue")
					time.sleep(2)
					print "downloading file " + filename
					if protocol == "UDP":
						download_udp (  filename )
					else:
						download_tcp(filename)

				else:
					print "file in user1 folder is latest"
					print "stopped downloading"
					tcp_socket.send("stop")
					time.sleep(2)
					# intermediate_upload_to_server(filename,"TCP")
			else:
				print "contents of file " + filename + " in both user2 folder and user1 folder are same"
				tcp_socket.send("stop")
				print "stopped downloading"
				time.sleep(2)
		else:
			print "file " + filename + " does not exists in user1 folder"
			tcp_socket.send("notexists")
			time.sleep(2)
			print "downloading " + filename

			if protocol == "UDP":
				download_udp(filename)
			else:
				download_tcp(filename)


prompt_flag = 1

while True:
	
	command = ''
	
	if time.time() - initial_time >= 120 or prompt_flag == 0:
		sync()
		command = nonBlockingRawInput("Do you want to use command line?(y or n)", 5)
		if command == "n" or command == '':
			initial_time = time.time()
			prompt_flag = 0
			continue
		else:
			command = nonBlockingRawInput("prompt> ",60)

	elif prompt_flag == 1:
		command = nonBlockingRawInput("prompt> ", 60)
		
	if command == '':
		continue

	if command == 'exit':
		prompt_flag = 0
		print "Exiting from the command line"
		continue

	if command == 'quit':
		tcp_socket.send(command)
		break

	tcp_socket.send(command)

	if command != '':
		f = open("user1_log.txt",'a+')
		f.write(command + "\n" + time.ctime() + '\n'+ '\n')
		f.close()

	args = command.split()
	if args[0] == "download":
		prompt_flag = 1
	
		if args[1] == "UDP":
			os.chdir("User1")
			status = tcp_socket.recv(1024)
			if status == "continue":
				intermediate_download_from_server("UDP")
			else:
				print "Requested file does not exist"
			os.chdir("..")

		elif args[1] == "TCP":
			os.chdir("User1")
			status = tcp_socket.recv(1024)
			if status == "continue":
				intermediate_download_from_server("TCP")
			else:
				print "Requested file does not exist"
			os.chdir("..")



	elif args[0] == "hash":
		prompt_flag = 1
		if args[1] == "verify":
			status = tcp_socket.recv(1024)
			if status == "continue":
				info = tcp_socket.recv(4096)
				print info		
			else:
				print "Requested file does not exist"
		elif args[1] == "checkall":
			info = tcp_socket.recv(4096)
			print info

	elif args[0] == "index":
		prompt_flag = 1
		message = tcp_socket.recv(1024)
		print message
	
	else:
		message = tcp_socket.recv(1024)
		print message	