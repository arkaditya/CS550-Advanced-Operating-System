#!/usr/bin/python3
import socket
import array
import sys
import pickle
import threading
import collections
import time
import os
import params

global host, port
global port_ps
global push

# host and port for server
host = 'localhost'
port = params.portSuperPeerNums[0]
port2 = 7010

# list to maintain peerID to its port list
global peer_port_list
peer_port_list = collections.defaultdict(int)  # index=peerID : port ;;;int pair

# dictionary to hold filelist (values) and peerID (key)
global fileDict
fileDict = {}  # "peerID":file1,file2...

hop=params.HOPS
#TTR for a file
ttr=params.TTR

#PUSH (True) or PULL (False) activation
push= params.PUSH_pull

#List of neighbours
port_ps=params.peer0_conn

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

# Initial setup to allot peerID to the new client
# retuns -1 if connection breaks
# otherwise returns the alloted peerID
# if peerID already exists then, that ID is returned
def do_handshake(client):
    try:
        data_in = pickle.loads(client.recv(1024))
    except:
        return -1
    peerID = data_in[0]
    peer_port = data_in[1]
    # new peerID allotment
    """""
    if peerID == -1:
        peer_port_list.append(peer_port)
        try:
            client.sendall(pickle.dumps((len(peer_port_list) - 1)))
        except:
            return -1
        return (len(peer_port_list) - 1)
    # old connection, peerID from list
    else:
    """
    peer_port_list[peerID] = peer_port
    try:
        client.sendall(pickle.dumps(peerID))
    except:
        return -1
    return peerID


# function to save file list of a particular peer against peerID (as key)
# temp is used to control print statements
# returns False if connection breaks or invalid response
# otherwise true
def filelistRegister(client, data_in, temp):

    data_split = data_in.split(':')
    peerID = data_split[1]
    fileName = data_split[2]
    for i in range(3, len(data_split)):
        fileName += ":"
        fileName += data_split[i]

    # create new key value pair
    if peerID not in fileDict:
        fileDict[peerID] = []
    # append value list if file is not already there
    if fileName not in fileDict[peerID]:
        fileDict[peerID].append(fileName)

    if temp:
        print(">>Client {} is adding file to its file list".format(peerID))
    if fileName != "":
        print("   >File:", fileName)
    # reply to client
    try:
        client.sendall(pickle.dumps("DONE"))
    except:
        return False
    return True


# function to delete the file list against the supplied peer ID
def file_DEregister(peerID):
    # check if key is available
    if str(peerID) in fileDict:
        del fileDict[str(peerID)]
        print("->File list of Client {} removed.".format(peerID))


# function to a search file from dictionary
# returns false if connection breaks or invalid response
# otherwise returns true
# sends peerID of client having file
def fileSearch(client, data_in):
    global fileDict
    data_split = data_in.split(':')
    peerID = data_split[1]
    fileName = data_split[2]
    for i in range(3, len(data_split)):
        fileName += ":"
        fileName += data_split[i]
    print(">>Client {} queried file named {}.".format(peerID, fileName))

    fileFound = []
    # finding file and appending peerID and port of file holder to a list
    for pID, files in fileDict.items():
        for file in files:
            if file == fileName and pID != peerID:
                fileFound.append((pID, str(peer_port_list[int(pID)])))

    # if file is not found
    if fileFound == []:
        print(">>File {} queried by client {} is not available at any of the peers.".format(fileName, peerID))
        try:
            client.sendall(pickle.dumps("-1"))
        except:
            return False
    # if found the each peerID and Port pair is sent to client indivisually.
    else:
        print(">>Queried file {} by Client {} is available.".format(fileName, peerID))
        for pID, portpID in fileFound:
            print("   > @", pID)
            data_out = pID + ":" + portpID
            try:
                client.sendall(pickle.dumps(data_out))
            except:
                return False

            try:
                if pickle.loads(client.recv(4096)) != "DONE":
                    return False
            except:
                return False

        # To mark end of list
        try:
            client.sendall(pickle.dumps("-2"))
        except:
            return False
    return True


# function called by the thread to handle incoming cnnections
def handleClient(client):
    # get peerID of the new client
    peerID = do_handshake(client)
    if peerID == -1:
        print("###Problem with request from a new Client...Disconnecting the client.")
        client.close()
        return

    print("***New client connected with peer ID = {}".format(peerID))
    temp = True
    while True:
        # get command
        try:
            data_in = pickle.loads(client.recv(4096))
            datasplit = data_in.split(':')
        except:
            break
        # case when client wants to disconnect.
        if datasplit[0] == "EXIT":
            break
        # case when client to register file list
        elif datasplit[0] == "REGISTER":
            if filelistRegister(client, data_in, temp) == False:
                print(fileDict.items())
                break
            temp = False

        # case when client wants to lookup
        #elif data_in[0:6] == "SEARCH":
        elif datasplit[0] == "SEARCH":
            if fileSearch(client, data_in) == False:
                break
            temp = True
        # incase of protocol violation
        else:
            break

    print("***Client with ID {} requested unknown service...Disconnecting the client.".format(peerID))
    # removing file list from dictionary
    file_DEregister(peerID)
    client.close()
    return

""""
# Function to check TTR value perodically
# It only changes for downloaded file
def monitorTTR():
    global allFile_dict, ttr
    x = 1  # sec
    while True:
        # check all files
        for file in allFile_dict:
            # if not master file
            if not allFile_dict[file][0]:
                # if TTR is not 0 and TTR is not Expired
                if (not allFile_dict[file][6]) and allFile_dict[file][5] > 0:
                    allFile_dict[file][5] -= x
                # if TTR not expired and TTR is 0
                elif (not allFile_dict[file][6]) and allFile_dict[file][5] == 0:
                    print("###WARNING: TTR of File {} reached 0. File marked as invalid.\n>>>".format(file), end='')
                    allFile_dict[file][6] = True
        # to save processing
        time.sleep(x)


# Function to update TTR value perodically
# It only changes for downloaded file
# Sends the request when TTR expires.
def updateTTR():
    global allFile_dict, ttr
    while True:
        # check all file
        for file in allFile_dict:
            # if TTR expired
            if allFile_dict[file][6] and allFile_dict[file][2]:
                print("INFO: Polling new TTR value of file {}.\n>>>".format(file), end='')

                dataOut = "PULLPOLL:" + str(allFile_dict[file][4]) + ":" + file
                # request new TTR value
                dataIn = fwdMessageToOne(allFile_dict[file][7], dataOut)
                # if server responds
                if dataIn[0]:
                    dataIns = dataIn[1].split(":")
                    # if server says file copy is valid
                    if dataIns[0] == "True":
                        allFile_dict[file][6] = False
                        allFile_dict[file][5] = int(dataIns[1])
                        print("INFO: TTR of File {} is updated.\n>>>".format(file), end='')
                    # otherwise
                    else:
                        print("###WARNING: File {} is invalid. Use REFRESH to download the new copy.\n>>>".format(file),
                              end='')
                        allFile_dict[file][2] = False

                # if server doesn't respond
                else:
                    print("INFO: TTR of File {} could not be updated. Will try again later.\n>>>".format(file), end='')

                    time.sleep(5)
        time.sleep(1)


# Function to handle PULL requests
# It only changes for downloaded file
# Sends the file validity information to a peer
def handlePULL(fromPeer, dataIn):
    global allFile_dict
    # extract data from object
    dataSplit = dataIn.split(':')
    fileName = dataSplit[2]
    for i in range(3, len(dataSplit)):
        fileName += ":"
        fileName += dataSplit[i]
    # if file is in directory
    if fileName in allFile_dict:
        print("INFO: PULL request received for a file named {}.\n>>>".format(fileName), end='')

        # if version matches
        if allFile_dict[fileName][4] == int(dataSplit[1]):

            dataTemp = "True:" + str(allFile_dict[fileName][5])
            try:
                # send data object
                fromPeer.sendall(pickle.dumps(dataTemp))
            except:
                return False
        # if version does not match
        else:
            dataTemp = "False:"
            try:
                # send data object
                fromPeer.sendall(pickle.dumps(dataTemp))
            except:
                return False

# Function to handle Invalidate requests
# Returns True on success otherwise False.
# checks file validity of downloaded file in the directory.
# deleted the file from system, if validity fails
def handleInvalidate(client, dataIn):
    global invalidateIn
    # extraxt data from object

    try:
        dataSplit = dataIn.split(':')
        fileName = dataSplit[6]
        for i in range(7, len(dataSplit)):
            fileName += ":"
            fileName += data_split[i]
    except:
        print("###WARNING: A peer requested unknown service.\n>>>", end='')

        return False
    if dataSplit[5] in invalidateIn:
        return True
    # if request came form itself
    if int(dataSplit[1]) == port or int(dataSplit[2]) == port:
        return True
    invalidateIn.append(dataSplit[5])
    print(
        'INFO: Invalidation message received from {} about a file {} with version number {}.\n>>>'.format(dataSplit[1],
                                                                                                          fileName,
                                                                                                          dataSplit[4]),
        end='')

    global allFile_dict

    # if file is in directory and version number doesnot match
    if fileName in allFile_dict and allFile_dict[fileName][4] < int(dataSplit[4]):
        print("###WARNING: Invalid file, {} found. Deleting from the system and updating the file list.\n>>>".format(
            fileName), end='')

        # delete file from directory
        del allFile_dict[fileName]
        os.remove(shared_dirPath[:-1] + "/" + fileName)

    print("INFO: Forwarding invalidation message..\n>>>", end='')

    # if hop reaches 1, it doesn't forward
    if int(dataSplit[3]) <= 1:
        return True
    # forward information to other peer

    fwdPush(dataSplit[1], (int(dataSplit[3]) - 1), dataSplit[4], fileName, dataSplit[5])

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
        dataIn = pickle.loads(peerNode.recv(1024))
    except:
        return (False, "")

    return (True, dataIn)


# Function to forward message to a peer
# Returns structure of data and if data was sent
def fwdMessageToOne(portPeer, msgObject):
    dataIn = (False, "")
    try:
        sNode = socket.socket()
        sNode.connect((host, portPeer))
    except:
        pass
    sendMessage(sNode, msgObject)
    dataIn = recvMessage(sNode)
    sendMessage(sNode, "CLOSE:")
    try:
        sNode.close()
    except:
        pass
    return dataIn  # (True, dataIn) or (False, "")


# Function to forward message to all known peers
# Returns structure of data and if data was sent
def fwdMessageToAll(msgObject):
    global port_ps
    dataIn_dict = {}
    for port_p in port_ps:
        dataIn_dict[port_p] = fwdMessageToOne(port_p, msgObject)
    return dataIn_dict  # {port:[(True, dataIn) or (False, "")]}


# Function to send PING to a peer
# Returns structure of received data and if PING was sent
def sendPINGToOne(portPeer):
    global port
    dataOut = "PING:" + str(port)
    return fwdMessageToOne(portPeer, dataOut)


# Function to send PING to all known peer
# Returns structure of received data and if PING was sent
def sendPINGToAll():
    global port
    dataOut = "PING:" + str(port)
    return fwdMessageToAll(dataOut)


# Function to send QUERY to all known peer
# Returns structure of received data and if Query was sent
def sendQUERYToAll(fileName):
    global hop, port
    dataOut = "QUERY:{}:{}:{}:{}".format(port, port, hop, fileName)
    return fwdMessageToAll(dataOut)


# Function to forward an incoming QUERY to all known peer
# Returns structure of received data and if Query was sent
def fwdQUERYToAll(originalPort, numhop, fileName):
    global port
    dataOut = "QUERY:{}:{}:{}:{}".format(originalPort, port, numhop, fileName)
    return fwdMessageToAll(dataOut)


# Function to send QUERYHIT to a peer
# Returns structure of received data and if QueryHIT was sent
def sendQUERYHIT(QH_ID, origin, origin_port, to_port, fileTimestamp, hops, fileName):
    global port
    dataOut = "QUERYHIT:{}:{}:{}:{}:{}:{}:{}".format(QH_ID, origin, origin_port, to_port, fileTimestamp, hops, fileName)
    return fwdMessageToOne(dataOut)


# Function to send/forward PUSH to all known peer
# Returns structure of received data and if PUSH was sent
def fwdPush(O_port, numHop, verNum, fileName, pushID):
    global port
    dataOut = "INVALIDATE:{}:{}:{}:{}:{}:{}".format(O_port, port, numHop, verNum, pushID, fileName)
    return fwdMessageToAll(dataOut)


# Function to handle downloading of a file.
# Returns True on success otherwise False.
def downloadFile(downloadPort, fileName):
    global port_ps, allFile_dict
    # create a connection with the peer
    try:
        s = socket.socket()
        s.connect((host, downloadPort))
    except:
        return False
    # sends the download request object
    dataOut = "DOWNLOAD:" + str(port) + ":" + fileName
    try:
        # send data object
        s.sendall(pickle.dumps(dataOut))
    except:
        return False
    try:
        # check the response for data availability
        dataIn = pickle.loads(s.recv(1024))
        dataSplit = dataIn.split(':')
        # returns if file is not available
        if "False" == dataSplit[0]:
            return False
    except:
        return False

    print("INFO: Downloading file {}.".format(fileName))
    print('>>>', end='')
    # get path
    filePath_f = shared_dirPath[:-1] + fileName
    # open file
    try:
        os.remove(filePath_f)
    except:
        pass
    fileNew = open(filePath_f, 'wb')
    # get the file from peer server and write to it
    try:
        filePart = s.recv(1024)
        while filePart:
            fileNew.write(filePart)
            filePart = s.recv(1024)
    except:
        return False
    # update file list structure
    varTemp = True
    if dataSplit[4] == "False":
        varTemp = False
    allFile_dict[fileName] = [False, False, True, float(dataSplit[2]), int(dataSplit[1]), int(dataSplit[3]), varTemp,
                              int(dataSplit[5])]
    # close file
    fileNew.close()
    # close connection
    try:
        s.close()
    except:
        pass
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
        dataIn = pickle.loads(peerNode.recv(1024))
    except:
        return (False, "")

    return (True, dataIn)


# Function to forward message to a peer
# Returns structure of data and if data was sent
def fwdMessageToOne(portPeer, msgObject):
    dataIn = (False, "")
    try:
        sNode = socket.socket()
        sNode.connect((host, portPeer))
    except:
        pass
    sendMessage(sNode, msgObject)
    dataIn = recvMessage(sNode)
    sendMessage(sNode, "CLOSE:")
    try:
        sNode.close()
    except:
        pass
    return dataIn  # (True, dataIn) or (False, "")


# Function to forward message to all known peers
# Returns structure of data and if data was sent
def fwdMessageToAll(msgObject):
    global port_ps
    dataIn_dict = {}
    for port_p in port_ps:
        dataIn_dict[port_p] = fwdMessageToOne(port_p, msgObject)
    return dataIn_dict  # {port:[(True, dataIn) or (False, "")]}


# Function to send PING to a peer
# Returns structure of received data and if PING was sent
def sendPINGToOne(portPeer):
    global port
    dataOut = "PING:" + str(port)
    return fwdMessageToOne(portPeer, dataOut)


# Function to send PING to all known peer
# Returns structure of received data and if PING was sent
def sendPINGToAll():
    global port
    dataOut = "PING:" + str(port)
    return fwdMessageToAll(dataOut)


# Function to send QUERY to all known peer
# Returns structure of received data and if Query was sent
def sendQUERYToAll(fileName):
    global hop, port
    dataOut = "QUERY:{}:{}:{}:{}".format(port, port, hop, fileName)
    return fwdMessageToAll(dataOut)


# Function to forward an incoming QUERY to all known peer
# Returns structure of received data and if Query was sent
def fwdQUERYToAll(originalPort, numhop, fileName):
    global port
    dataOut = "QUERY:{}:{}:{}:{}".format(originalPort, port, numhop, fileName)
    return fwdMessageToAll(dataOut)


# Function to send QUERYHIT to a peer
# Returns structure of received data and if QueryHIT was sent
def sendQUERYHIT(QH_ID, origin, origin_port, to_port, fileTimestamp, hops, fileName):
    global port
    dataOut = "QUERYHIT:{}:{}:{}:{}:{}:{}:{}".format(QH_ID, origin, origin_port, to_port, fileTimestamp, hops, fileName)
    return fwdMessageToOne(dataOut)


# Function to send/forward PUSH to all known peer
# Returns structure of received data and if PUSH was sent
def fwdPush(O_port, numHop, verNum, fileName, pushID):
    global port
    dataOut = "INVALIDATE:{}:{}:{}:{}:{}:{}".format(O_port, port, numHop, verNum, pushID, fileName)
    return fwdMessageToAll(dataOut)
"""

# main function
def main():
    s = socket.socket()
    try:
        s.bind((host, port))
        print("->Server up.")
    except:
        raise SystemExit('->Server cannot start. Please check port.')
    while True:
        s.listen(5)
        client, addr = s.accept()
        # new thread for every connection
        threading.Thread(target=handleClient, args=(client,)).start()


if __name__ == '__main__':
    main()