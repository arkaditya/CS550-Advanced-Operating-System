#!/usr/bin/python3
#imports
import socket 
import array
import os
import os.path
import sys
import pickle
import glob
import threading
import time
import csv
import params


#global variables
global host, port, hop, ttr

host='localhost'

#global variable derived from params.py

#server port
port=params.peer_8_port
#Max hop
hop=params.HOP
#TTR for a file
ttr=params.TTR
global push
#PUSH (True) or PULL (False) activation
push= params.PUSH_pull
global port_ps
#List of neighbours 
port_ps=params.peer_8_port_conn
global shared_dirPath 
#shared directory path
shared_dirPath=params.peer_8_path



#global variables
global allFile_dict
#structure to hold files and details
allFile_dict={}
#allFile_dict struct
#	{
#	string fileName: [ 
#					bool original   		True for master file. To identify master files
#					bool new        		True if master file is changed. only for master file 
#					bool valid 				True if file is valid. NA for master file   	
#					float last modified		time at file modified
#					int verNum				Version number
#					int ttr 				TTR value for downloaded file. NA for master file
#					bool expired 			True if TTR expired. NA for master file.
#					int original port 		file original location. For Master file' port
#					]
#	}
#a flag to know if query is active
global queryStat 
queryStat=False
#to hold invalidate message IDs
global invalidateIn
invalidateIn=[]
# list of incoming ports
global hitPorts
hitPorts=[]
#flag for network use 
global networkUseStat
networkUseStat=False





# Function to start server
# Each connected client uses seperate threads
# Threads returns when disconnected
def peerServer(s):
	while True:
		try:
			s.listen(5)               
			client, addr = s.accept()
		except KeyboardInterrupt:
			s.close()
			raise
			return
		#thread to handle each client
		threading.Thread(target=handleClient, args=(client,)).start()


# Function to handle each connected client to the server.
# Returns when connection closes or disconnects.
# Waits for data object to come and resonds accordingly.
def handleClient(client):
	global queryStat 
	
	while True:
		try:
			dataIn=pickle.loads(client.recv(1024))
			dataSplit=dataIn.split(':')
		except:
			client.close()
			return

		# for PING
		if dataSplit[0]=="PING":
			if not handlePING(client,dataIn):
				return	

		# handling query hit 
		if queryStat and dataSplit[0]=="QUERYHIT":
			client.sendall(pickle.dumps("OK"))
			handleQUERYHIT(dataIn)
		if (not queryStat) and dataSplit[0]=="QUERYHIT":
			client.sendall(pickle.dumps("OK"))
		
		#handling query
		if dataSplit[0]=="QUERY":
			if not handleQUERY(client,dataIn):
				return True
		#handling closing of connection
		if dataSplit[0]=="CLOSE":
			client.close()
			return
		#handling download of file
		if dataSplit[0]=="DOWNLOAD":
			if fileUpload(client, dataIn):
				print("INFO: File {} requested by a peer {} was sent.\n>>>".format(dataSplit[2],dataSplit[1]),end='')
			else:
				print("INFO: File {} requested by a peer {} could not be sent.\n>>>".format(dataSplit[2],dataSplit[1]),end='')
			
			
			try:
				client.close()
			except:
				pass
			return	
		#handling invalidate of file
		if dataSplit[0]=="INVALIDATE":
			client.sendall(pickle.dumps("OK"))
			handleInvalidate(client,dataIn)
			return
		#handling polling of a file
		if dataSplit[0]=="PULLPOLL":
			handlePULL(client,dataIn)
			return
	return

# Function to handle incoming PING.
# Returns True on success otherwise False.
# Adds incoming connection port number to the list.
# Responds by sending PONG.
def handlePING(fromPeer,dataIn):
	global port_ps	
	dataSplit=dataIn.split(':')
	if dataSplit[0]=="PING" and sendPONG(fromPeer):
		#adds port to list only if its not availble.
		if not int(dataSplit[1]) in port_ps:
			port_ps.append(int(dataSplit[1]))
		
		print("INFO: A new peer with port {} PINGed you.\n>>>".format(dataSplit[1]),end='')

		return True
	#in the event of invalid protocol
	print("###WARNING: A peer requested an invalid protocol. Disconnecting...\n>>>",end='')
	
	#closes the connection
	try:
		fromPeer.close()
	except:
		pass
	return False

# Function to send PONG on receiving PING.
# Returns True on success otherwise False.
def sendPONG(toPeer):
	dataOut="PONG:{}".format(port)
	try:
		toPeer.sendall(pickle.dumps(dataOut))	
	except:
		print("###WARNING: Peer could not be PONGed ...Disconnecting the peer.")
		print('>>>',end='')
		return False
	print("INFO: The new peer is PONGed")
	print('>>>',end='')

	return True

# Function to handle incoming Query of a file.
# Returns True on success otherwise False.
# Check for the file in the file list.
# if availble, send QueryHit.
# Also, Forward the request to other peers.
def handleQUERY(fromPeer,dataIn):
	fromPeer.sendall(pickle.dumps("OK"))

	global allFile_dict
	global port_ps,port
	#extracting information from data object
	try:
		dataSplit=dataIn.split(':')
		fileName=dataSplit[4]
		for i in range(5,len(dataSplit)):
			fileName+=":"
			fileName+=data_split[i]
	except:
		print("###WARNING: A peer requested unknown service.\n>>>",end='')
		return False


	# if valid protocol
	if dataSplit[0]=="QUERY":
		#if Query came from itself.
		if int(dataSplit[1])==port or int(dataSplit[2])==port:
			return True
		#otherwise
		print("INFO: A peer requested a file named {}\n>>>".format(fileName),end='')
		#if file is available
		if fileName in allFile_dict:
			#send Query HIT
			if not sendQUERYHIT(int(dataSplit[1]),fileName)[0]:
				print("INFO: Requested file \"{}\" is available but Query Hit could not be sent.\n>>>".format(fileName),end='')
				
			else:
				print("INFO: Requested file \"{}\" is available and Query Hit is sent.\n>>>".format(fileName),end='')
				
		#if file is not available		
		else:
			print("INFO:The file named {} is NOT available. Forwarding...\n>>>".format(fileName),end='')
			
		#checking HOP value
		if int(dataSplit[2])==1:
			return True
		print("INFO:The file {} request is Forwarded.\n>>>".format(fileName),end='')
		
		#forwarding to others if HOP>1
		fwdQUERYToAll(dataSplit[1], (int(dataSplit[3])-1), fileName)
					
		return True	
	else:
		print("###WARNING: Peer sent invalid protocol\n>>>",end='')
		
		return False

# Function to handle incoming Query HIT
# Returns True on success otherwise False.
# Add port of the file holding peer to the list
def handleQUERYHIT(dataIn):

	dataSplit=dataIn.split(':')
	if not dataSplit[0]=="QUERYHIT":
		print("###WARNING: Peer sent invalid protocol.\n>>>",end='')
		
		return False
	if not int(dataSplit[1])==port:
		hitPorts.append(int(dataSplit[1]))
	return True

# Function to handle file upload request.
# Returns True on success otherwise False.
# closes connection if connection breaks or  protocol violation
# uploads file upon the request from peer
def fileUpload(client, dataIn):

	global allFile_dict
	#extract from data object
	dataSplit=dataIn.split(':')
	fileName=dataSplit[2]
	for i in range(3,len(dataSplit)):
		fileName+=":"
		fileName+=dataSplit[i]
	#respond false if file not available
	if not fileName in allFile_dict:
		try:
		#send data object
			client.sendall(pickle.dumps("False:"))
		except:
			return False
		return False

	else:
		#respond false if file is in stale condition
		if allFile_dict[fileName][6] or not allFile_dict[fileName][2]:
			print("###WARNING: Peer requested a stale copy of file.\n>>>",end='')
			
			try:
		#send data object
				client.sendall(pickle.dumps("False:"))
			except:
				return False
	
			return False

		
		#otherwise create data object containing details and send it
		dataOut="True:"+str(allFile_dict[fileName][4])+":"+str(allFile_dict[fileName][3])+":"+str(allFile_dict[fileName][5])+":"+str(allFile_dict[fileName][6])+":"+str(allFile_dict[fileName][7])
		try:	
			client.sendall(pickle.dumps(dataOut))
		except:
			return False
	print("INFO: Requested file \"{}\" is being uploaded.\n>>>".format(fileName),end='')


	#get file path
	filePath=shared_dirPath[:-1]+"/"+fileName
	#open file
	f = open(filePath,'rb')
	#read file and send over the network
	l = f.read(1024)
	while l:
			try:
				client.sendall(l)
			except:
				return False
				break
			l = f.read(1024)
	f.close()

	return True


# Function to check TTR value perodically
# It only changes for downloaded file 
def monitorTTR():
	global allFile_dict, ttr
	x=1 #sec
	while True:
		#check all files 
		for file in allFile_dict:
			# if not master file
			if not allFile_dict[file][0]:
				#if TTR is not 0 and TTR is not Expired
				if (not allFile_dict[file][6]) and allFile_dict[file][5]>0:
					allFile_dict[file][5]-=x
				#if TTR not expired and TTR is 0
				elif (not allFile_dict[file][6]) and allFile_dict[file][5]==0:
					print("###WARNING: TTR of File {} reached 0. File marked as invalid.\n>>>".format(file),end='')
					allFile_dict[file][6]=True
		#to save processing 
		time.sleep(x)

# Function to update TTR value perodically
# It only changes for downloaded file 
# Sends the request when TTR expires.
def updateTTR():
	global allFile_dict, ttr
	while True:
		#check all file
		for file in allFile_dict:
			#if TTR expired
			if allFile_dict[file][6] and allFile_dict[file][2]:
				print("INFO: Polling new TTR value of file {}.\n>>>".format(file),end='')
				
				dataOut="PULLPOLL:"+str(allFile_dict[file][4])+":"+file
				#request new TTR value
				dataIn=fwdMessageToOne(allFile_dict[file][7],dataOut)
				#if server responds
				if dataIn[0]:
					dataIns=dataIn[1].split(":")
					#if server says file copy is valid
					if dataIns[0]=="True":
						allFile_dict[file][6]=False
						allFile_dict[file][5]=int(dataIns[1])
						print("INFO: TTR of File {} is updated.\n>>>".format(file),end='')
					#otherwise
					else:
						print("###WARNING: File {} is invalid. Use REFRESH to download the new copy.\n>>>".format(file),end='')
						allFile_dict[file][2]=False

				#if server doesn't respond
				else:
					print("INFO: TTR of File {} could not be updated. Will try again later.\n>>>".format(file),end='')
					
					time.sleep(5)
		time.sleep(1)

# Function to handle PULL requests
# It only changes for downloaded file 
# Sends the file validity information to a peer
def handlePULL(fromPeer,dataIn):
	global allFile_dict
	#extract data from object
	dataSplit=dataIn.split(':')
	fileName=dataSplit[2]
	for i in range(3,len(dataSplit)):
		fileName+=":"
		fileName+=dataSplit[i]
	#if file is in directory
	if fileName in allFile_dict:
		print("INFO: PULL request received for a file named {}.\n>>>".format(fileName),end='')
		
		# if version matches
		if allFile_dict[fileName][4]== int(dataSplit[1]):
			
			dataTemp="True:"+str(allFile_dict[fileName][5])
			try:
			#send data object
				fromPeer.sendall(pickle.dumps(dataTemp))
			except:
				return False
		# if version does not match
		else:
			dataTemp="False:"
			try:
			#send data object
				fromPeer.sendall(pickle.dumps(dataTemp))
			except:
				return False

# Function to handle Invalidate requests
# Returns True on success otherwise False.
# checks file validity of downloaded file in the directory.
# deleted the file from system, if validity fails
def handleInvalidate(client, dataIn):	
	global invalidateIn
	#extraxt data from object

	try:
		dataSplit=dataIn.split(':')
		fileName=dataSplit[6]
		for i in range(7,len(dataSplit)):
			fileName+=":"
			fileName+=data_split[i]
	except:
		print("###WARNING: A peer requested unknown service.\n>>>",end='')	
		
		return False
	if dataSplit[5] in invalidateIn:
		return True
	#if request came form itself
	if int(dataSplit[1])==port or int(dataSplit[2])==port:
		return True
	invalidateIn.append(dataSplit[5])
	print('INFO: Invalidation message received from {} about a file {} with version number {}.\n>>>'.format(dataSplit[1], fileName, dataSplit[4]),end='')
	
	global allFile_dict

	#if file is in directory and version number doesnot match
	if fileName in allFile_dict and allFile_dict[fileName][4]<int(dataSplit[4]):
		print("###WARNING: Invalid file, {} found. Deleting from the system and updating the file list.\n>>>".format(fileName),end='')	
		
		#delete file from directory
		del allFile_dict[fileName]
		os.remove(shared_dirPath[:-1]+"/"+fileName)

	print("INFO: Forwarding invalidation message..\n>>>",end='')

	#if hop reaches 1, it doesn't forward
	if int(dataSplit[3])<=1:
		return True
	#forward information to other peer
	
	fwdPush(dataSplit[1], (int(dataSplit[3])-1),dataSplit[4], fileName, dataSplit[5])
	
	
	return True



# Function to send message to a peer 
# Returns True on success otherwise False.
def sendMessage(peerNode, msgObject):
	try:
		peerNode.sendall(pickle.dumps(msgObject))
	except:
		return False 
	return True

# Function to receive message from a peer 
# Returns True on success otherwise False.
# if success, returns data object also.
def recvMessage(peerNode):
	try:
		dataIn=pickle.loads(peerNode.recv(1024))
	except:
		return (False,"")

	return (True,dataIn)

# Function to forward message to a peer
# Returns structure of data and if data was sent 
def fwdMessageToOne(portPeer,msgObject):
	dataIn=(False,"")
	try:  
		sNode=socket.socket()
		sNode.connect((host, portPeer))
	except:
		pass
	sendMessage(sNode, msgObject)
	dataIn=recvMessage(sNode)
	sendMessage(sNode, "CLOSE:")
	try:  
		sNode.close()
	except:
		pass
	return dataIn #(True, dataIn) or (False, "") 

# Function to forward message to all known peers
# Returns structure of data and if data was sent 
def fwdMessageToAll(msgObject):
	global port_ps
	dataIn_dict={}
	for port_p in port_ps:	
		dataIn_dict[port_p]=fwdMessageToOne(port_p,msgObject)
	return dataIn_dict #{port:[(True, dataIn) or (False, "")]}

# Function to send PING to a peer
# Returns structure of received data and if PING was sent 
def sendPINGToOne(portPeer):
	global port
	dataOut="PING:"+str(port)
	return fwdMessageToOne(portPeer,dataOut)
	
# Function to send PING to all known peer
# Returns structure of received data and if PING was sent 
def sendPINGToAll():
	global port
	dataOut="PING:"+str(port)
	return fwdMessageToAll(dataOut)

# Function to send QUERY to all known peer
# Returns structure of received data and if Query was sent 
def sendQUERYToAll(fileName):
	global hop,port
	dataOut="QUERY:{}:{}:{}:{}".format(port, port, hop, fileName)
	return fwdMessageToAll(dataOut)

# Function to forward an incoming QUERY to all known peer
# Returns structure of received data and if Query was sent 
def fwdQUERYToAll(originalPort,numhop, fileName):
	global port
	dataOut="QUERY:{}:{}:{}:{}".format(originalPort, port, numhop,fileName)
	return fwdMessageToAll(dataOut)

# Function to send QUERYHIT to a peer
# Returns structure of received data and if QueryHIT was sent 
def sendQUERYHIT(portPeer,fileName):
	global port
	dataOut="QUERYHIT:{}:{}".format(port,fileName)
	return fwdMessageToOne(portPeer,dataOut)

# Function to send/forward PUSH to all known peer
# Returns structure of received data and if PUSH was sent 
def fwdPush(O_port, numHop, verNum, fileName, pushID):
	global port
	dataOut="INVALIDATE:{}:{}:{}:{}:{}:{}".format(O_port, port, numHop,verNum, pushID, fileName)
	return fwdMessageToAll(dataOut)

# Function to handle downloading of a file.
# Returns True on success otherwise False.
def downloadFile(downloadPort,fileName):
	global port_ps, allFile_dict
	#create a connection with the peer
	try:  
		s=socket.socket()
		s.connect((host, downloadPort))
	except:
		return False
	#sends the download request object
	dataOut= "DOWNLOAD:"+str(port)+":"+fileName
	try:
		#send data object
		s.sendall(pickle.dumps(dataOut))
	except:
		return False
	try:
		#check the response for data availability
		dataIn=pickle.loads(s.recv(1024))
		dataSplit=dataIn.split(':')
		#returns if file is not available
		if "False"==dataSplit[0]:
			return False
	except:
		return False

	print("INFO: Downloading file {}.".format(fileName))
	print('>>>',end='')
	#get path
	filePath_f=shared_dirPath[:-1]+fileName
	#open file
	try:
		os.remove(filePath_f)
	except:
		pass
	fileNew = open(filePath_f,'wb')
	#get the file from peer server and write to it
	try:
		filePart = s.recv(1024)
		while filePart:
			fileNew.write(filePart)
			filePart = s.recv(1024)
	except:
		return False
	#update file list structure
	varTemp=True
	if dataSplit[4]=="False":
		varTemp=False
	allFile_dict[fileName]=[False, False, True, float(dataSplit[2]), int(dataSplit[1]), int(dataSplit[3]),varTemp, int(dataSplit[5])] 
	#close file
	fileNew.close()
	#close connection
	try:
		s.close()
	except:
		pass
	return True

# Function to monitor change in master file 
# Uses last modified information to ascertain version number
def monitorDirectory():
	global allFile_dict
	dirPath=shared_dirPath[:-1]

	new_fileList=get_fileList(shared_dirPath)

	global hop,port
	while True:
		#for every file in the current directory
		for file in new_fileList:
			filePath=dirPath+file
			#if file in file directory
			if file in allFile_dict:
				#if master file
				if allFile_dict[file][0]:
					#check if file changed from last time
					try:
						if os.path.getmtime(filePath)>allFile_dict[file][3]: #modified recently
							#if file changed
							if push:
								allFile_dict[file][1]=True	
							#updating file version number					
							allFile_dict[file][4]+=1
							#if PUSH is set
							if push:
								print("Broadcasting INVALIDATE message about the file\n>>>", file,end='')	
								pushID=str(port)+str(time.time())
								fwdPush(port,hop, allFile_dict[file][4], file, pushID)
							#updating file last modified
								allFile_dict[file][1]=False	
							allFile_dict[file][3]=os.path.getmtime(filePath)
					except:
						pass
		time.sleep(5)


# Function to create file list structure to hold master file and later, downloaded file
# called at the begining of process.
def create_fileList(master_fileList):
	global allFile_dict, ttr, port
	dirPath=shared_dirPath[:-1]
	print("INFO: Folowing file is added from the directory \"{}\"".format(dirPath))
	for file in master_fileList:
		allFile_dict[file]=[True, False, True] #[string file::bool original, bool new, bool valid,float last modified, int verNum, int ttr, bool expired, port]	
		filePath=dirPath+file
		try:
			allFile_dict[file].append(os.path.getmtime(filePath))
		except:
			allFile_dict[file].append(time.time())
		allFile_dict[file].append(1)
		allFile_dict[file].append(ttr)
		allFile_dict[file].append(False)
		allFile_dict[file].append(port)
		print(">",file)	
	print('>>>',end='')	

# Function to Handle UPDATE command from the user
# deletes or add file to the file list structure
def update_fileList(master_fileList):
	global allFile_dict, ttr, port
	new_fileList=get_fileList(shared_dirPath)
	dirPath=shared_dirPath[:-1]
	for file in new_fileList:
		if not file in allFile_dict:
			print("INFO: File \"{}\" is added to the list.\n>>>".format(file),end='')	
			allFile_dict[file]=[True, False, True] #[string file::bool original, bool new, bool valid,float last modified, int verNum, int ttr, bool expired, port]	
			filePath=dirPath+file
			try:
				allFile_dict[file].append(os.path.getmtime(filePath))
			except:
				allFile_dict[file].append(time.time())
			allFile_dict[file].append(1)
			allFile_dict[file].append(ttr)
			allFile_dict[file].append(False)
			allFile_dict[file].append(port)
	temp_fileList=[]
	for file in allFile_dict:
		if not file in new_fileList:
			print("INFO: File \"{}\" is deleted from the list.\n>>>".format(file),end='')	
			temp_fileList.append(file)
	for file in temp_fileList:
		del allFile_dict[file]

# Funciton to get current file names from the directory
# returns the list
def get_fileList(dirPath):
	return [os.path.basename(x) for x in glob.glob(dirPath)]

# Main Function
# handles user interface
# calls other funcitons
# starts various threads
def main():
	print("""
		WW            WW  EEEEEE LL       CCCCCC  OOOOOO  MMMM    MMMM EEEEEE
		WW     WW     WW  EE     LL      CCC     OOO  OOO MM MM  MM MM EE  
		 WW  WW  WW  WW   EE     LL      CC      OO    OO MM   MM   MM EE
		 WW  WW  WW  WW   EEEEEE LL      CC      OO    OO MM        MM EEEEEE
 		  WWWW    WWWW    EE     LL      CCC     OOO  OOO MM        MM EE
 		  WWWW    WWWW    EEEEEE LLLLLLL  CCCCCC  OOO0OO  MM        MM EEEEEE
		""")
	global push
		
	# create file list structure
	global allFile_dict
	masterFile_list=get_fileList(shared_dirPath)
	create_fileList(masterFile_list)
	#start the server
	s = socket.socket()
	try:
		s.bind((host, port))
	except:
		print('###ERROR: Can not host. Exiting...')
		print('>>>',end='')
		raise
		return

	print("INFO: Server is now running at port", port)
	print('>>>',end='')
	if push:
		print("INFO: PUSH system activated.")
		print('>>>',end='')
	else:
		print("INFO: PULL system activated.")
		print('>>>',end='')

	# handle clients
	threading.Thread(target=peerServer, args=(s,)).start()
	#if push is activated
	if push:
		threading.Thread(target=monitorDirectory).start()
	#otherwise
	else:
		threading.Thread(target=monitorDirectory).start()
		threading.Thread(target=monitorTTR).start()
		threading.Thread(target=updateTTR).start()

	global queryStat,hitPorts
	

	while True:
		print("Please choose from the following Command List when prompted.")
		print("> SEARCH to update file List")
		print("> UPDATE to update file List. Delete or add new \"Master\" file in runtime.")
		if not push:
			print("> REFRESH to update a downloaded file.")
		print('>>>',end='')

		queryStat=False
		hitPorts=[]
		print("Please enter the Command.\n>>>",end='')
		
		cmd=0
		#prompt user for command
		try:
			userResponse = input() 
			print('>>>',end='')
		except KeyboardInterrupt:
			raise
			return
		#check peers
		sendPINGToAll()



		if userResponse=="SEARCH":
			print("Please enter the file name.\n>>>",end='')
		
			cmd=1
		elif userResponse=="UPDATE":	#done
			print("INFO: File list is being updated.\n>>>",end='')
			
			cmd=2
			
			
		elif userResponse=="REFRESH":
			if not push:
				print("Please enter the file name to refresh.\n>>>",end='')
				 
				cmd=3
			else:
				print("###ERROR: Wrong Command. PUSH is enabled. To use REFRESH command, change PUSH to False and try again.\n>>>",end='')
				
				continue

		else:
			print("###ERROR: Wrong Command. Try again.\n>>>",end='')
			
			continue


		if cmd==2:
			update_fileList(masterFile_list)
			print("INFO: File list is up to date.\n>>>",end='')
			
			continue


		try:
			user_fileName = input() 
			print('>>>',end='')
		except KeyboardInterrupt:
			raise
			return
		try:	
			if user_fileName=='' or user_fileName[0]==' ':
				continue
		except:
			continue

		if cmd==3:
			if not user_fileName in allFile_dict:
				print("###ERROR: Wrong Command Usage. Try again.\n>>>",end='')
				
				continue
			if allFile_dict[user_fileName][2]:
				print('INFO: File is at latest version.\n>>>',end='')
				continue
			

			portTemp2=allFile_dict[user_fileName][7]
			listTemp2=allFile_dict[user_fileName]
			try:
				del allFile_dict[user_fileName]
			except:
				pass
			if downloadFile(portTemp2, user_fileName):
				print('INFO: File version Updated.\n>>>',end='')
				
				
			else:
				print ('###ERROR: File could not be downloaded. Try later.\n>>>',end='')
				
				allFile_dict[user_fileName]=listTemp2
			continue



		if cmd==1:
			queryStat=True
			dataTemp=sendQUERYToAll(user_fileName)
			numSend=0

			print("INFO: Sending Request to...")
			for portTemp in dataTemp:
				if dataTemp[portTemp][0]:
					print(">", portTemp)

					numSend+=1
			print('>>>',end='')
			#if peers are not available
			if numSend==0:
				print('###ERROR: No peer is available. Try later.\n>>>',end='')
			
				continue



			print('Waiting for the response.\n>>>',end='')
			

			timeStamp=time.time()
			while True:
				time.sleep(2)
				if time.time()-timeStamp>1.8:
					break
			queryStat=False
			#check if any peer responded 
			if len(hitPorts)==0:
				print("###WARNING: No peer in the network has the file. Try again later.\n>>>",end='')
				continue
			print ('INFO: Following Peers have file.\n>>>',end='')
			i=1
			#show all peers holding the file
			for hitPort in hitPorts:
				print("> {}: @ {}".format(i,hitPort))
				i+=1
			print('>>>',end='')
			i=0	
			while i<3:	

				print("Select the peer to download the file from e.g. 1 if first peer:\n>>> ",end='')
				#prompt user to select ports
				try:
					sel = input()
					print('>>>',end='')
				except KeyboardInterrupt:
					raise
					return
				try:
					numSel=int(sel)
				except:
					print ('###WARNING: Invalid Response. Try again.\n>>>',end='')
					continue
				#if user selected valid port
				if numSel<=len(hitPorts):
					#download the file
					if downloadFile(hitPorts[numSel-1], user_fileName):
						print('INFO: File downloaded.\n>>>',end='')
					#if downloads fails 
					else:
						print ('###ERROR: File could not be downloaded. Try later.\n>>>',end='')
					break
				#otherwise
				else:
					print ('###WARNING: Wrong Response. Try again.\n>>>',end='')
				i+=1

# Start point of the code
if __name__ == '__main__':
	main()