from socket import *
import os
import time


tcp_socket = socket(AF_INET, SOCK_STREAM)
udp_socket = socket(AF_INET, SOCK_DGRAM)

tcp_port = 60008
udp_port = 60009
host = gethostname()

tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcp_socket.bind((host, tcp_port))
tcp_socket.listen(1)

conn, addr = tcp_socket.accept()
#print conn, addr

def long_list(file):
	return os.popen("ls -l " + file).read()

def list_of_files(dir):
	return os.popen("ls " + dir).read()

def short_list(start_timestamp = "2000-01-01 00:00:00.000000000 +0530", end_timestamp = "3000-01-01 00:00:00.000000000 +0530"):
	command = "find User1 -type f -newermt '" + start_timestamp + "' ! -newermt '"+ end_timestamp + "'"
	return os.popen(command).read()

def hash_verify(file):
	return os.popen("md5sum " + file).read()

def download_tcp(file):
	#print "downloading using tcp"
	f = open(file,'rb')
	data = f.read(1024)
	while data:
		conn.send(data)
		time.sleep(2)
		data = f.read(1024)
	f.close()

	conn.send("DONE")
	time.sleep(2)

	perm = os.popen("stat -c '%a' " + file).read()
	conn.send(str(perm))
	time.sleep(2)
	
	file_info = "last_modified_timestamp: " + os.popen("stat --printf '%y\n' " + file).read()
	file_info += "file_size: " + os.popen("ls -lah " + file + " | cut -d' ' -f 5").read()
	file_info += "MD5 hash: " + os.popen("md5sum " + file).read()
	conn.send(file_info)
	time.sleep(2)

def download_udp(file):
	f = open(file,'rb')
	data = f.read(1024)
	while data:
		udp_socket.sendto(data, (host, udp_port))
		data = f.read(1024)
	udp_socket.sendto("DONE", (host, udp_port))
	f.close()
	
	perm = os.popen("stat -c '%a' " + file).read()
	conn.send(str(perm))
	time.sleep(2)

	md5sum = os.popen("md5sum " + file).read()
	conn.send(md5sum)

	status = conn.recv(7)
	#print status
	if str(status) == "Success":
		#print "File "+ file + " Succesfully sent"
		# conn.send("OK")
		file_info = "last_modified_timestamp: " + os.popen("stat --printf '%y\n' " + file).read()
		file_info += "file_size: " + os.popen("ls -lah " + file + " | cut -d' ' -f 5").read()
		file_info += "MD5 hash: " + os.popen("md5sum " + file).read()
		conn.send(file_info)
	else:
		#print "failed to send the File "+ file
		#print "Resending file"
		download_udp(file)

def intermediate_download_from_server(filename, protocol = "UDP"):
	#print ""
	#print ""
	time.sleep(2)
	if os.path.isdir ( filename):
		#print filename + " is a directory"
		conn.send ( "directory")
		time.sleep(2)
		conn.send ( filename)
		os.chdir ( filename )
		#print "Changed to directory " + filename

		files = os.popen ( "ls" ).read ( )
		files = files.split ( "\n" )

		#print "directory " + filename + " has " + str(len(files)-1) + " files"

		conn.send ( str ( len ( files ) - 1 ))
		time.sleep(2)
		for file in files:
			if not file == '':
				intermediate_download_from_server (  file, protocol )
		os.chdir ( ".." )
	else:
		#print filename + " is a file"
		conn.send ( "file")
		time.sleep(2)
		conn.send ( filename)
		#print filename

		existence = conn.recv(1024)
		
		if existence == "exists":
			#print "file " + filename + " exists in user folder" 

			md5sum = os.popen("md5sum " + filename).read()
			conn.send(md5sum)
			#print "Sending md5sum of " + filename + " which is " + md5sum

			status = conn.recv(1024)

			if status == "continue":
				#print "contents of file " + filename + " in both user and shared folder are not same"
				mtime = os.path.getmtime(filename)
				#print "sending modified unix timestamp of " + filename + " which is " + str(mtime)
				conn.send(str(mtime))
				status = conn.recv(1024)

				if status == "continue":
					#print "file " + filename + " in shared folder is latest"
					#print "Hence sending the file"
					if protocol == "UDP":
						download_udp ( filename )
					else:
						download_tcp(filename)
				# else:
					#print "file " + filename + " in shared folder is not latest"
					
			# else:
				#print "contents of file " + filename + " in both user and shared folder are same"

		else:
			#print "file " + filename + " does not exists in user folder"
			#print "Hence sending the file"
			if protocol == "UDP":
				download_udp(filename)
			else:
				download_tcp(filename)


## stat --printf '%y\n' file           		gives last modified timestamp
# ls -lah server.py | cut -d' ' -f 5  		gives filesize
# stat -c "%a" Assgn1.py                    gives octal permissions of a file
def checkall(file):

	info = ''

	if os.path.isdir(file):
		files = list_of_files(file).split()
		# os.chdir(file)
		for f in files:
			info += checkall(file + "/" + f)
		# os.chdir("..")

	else:
		info += file + '\n'
		info += "MD5_hash: " + hash_verify(file)
		info += "last_modified_timestamp: " + os.popen("stat --printf '%y\n' " + file).read() + '\n'

	return info

while True:
	
	command = conn.recv(1024)
	#print command

	if command == 'quit':
		break

	
	args = command.split()

	if args[0] == "index":
		if args[1] == "longlist":
			longlist = long_list("User1")
			conn.send(longlist)

		elif args[1] == "list":
			files = os.popen("ls User1").read()
			if files == '':
				files = "empty"
			conn.send(files)

		elif args[1] == "shortlist":
			start_timestamp = args[2] + " " + args[3] + " " + args[4]
			end_timestamp   = args[5] + " " + args[6] + " " + args[7]
			
			shortlist = short_list(start_timestamp, end_timestamp).split()
			info = ''
			for file in shortlist:
				info = info + long_list(file) + '\n'
			conn.send(info)
			#index shortlist 2016-03-19 19:02:48.512380000 +0530 2018-03-19 19:02:48.512380000 +0530
		elif args[1] == "regex":
			try:
				info = long_list("User1/" + args[2])
			except:
				info = long_list(args[2])
			conn.send(info)

		else:
			conn.send("INVALID COMMAND")

	elif args[0] == "hash":
		if args[1] == "verify":
			info = args[2] + '\n'
			os.chdir("User1")
			if os.path.exists(args[2]):
				conn.send("continue")
				time.sleep(2)
				info += "MD5_hash: " + hash_verify(args[2])
				info += "last_modified_timestamp: " + os.popen("stat --printf '%y\n' " + args[2]).read()
				conn.send(info)
			else:
				conn.send("stop")
			os.chdir("..")
			

		elif args[1] == "checkall":
			info = checkall("User1")
			# info += checkall("User2")
			if info == '':
				info = "No files in the directory"
			conn.send(info)

		else:
			conn.send("INVALID COMMAND")

	elif args[0] == "download":

		if args[1] == "TCP":
			os.chdir("User1")
			if os.path.exists(args[2]):
				conn.send("continue")
				intermediate_download_from_server(args[2],"TCP")
			else:
				conn.send("stop")
			os.chdir("..")
			

		elif args[1] == "UDP":	
			os.chdir("User1")
			if os.path.exists(args[2]):
				conn.send("continue")
				intermediate_download_from_server(args[2],"UDP")
			else:
				conn.send("stop")
			os.chdir("..")
				
		else:
			conn.send("INVALID COMMAND")