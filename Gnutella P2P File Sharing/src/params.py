#!/usr/bin/python3

# PUSH is set by default					 		  #
# To enable PULL, set PUSH_pull variable to False.    #
PUSH_pull=True

# Configure the ports statically
portSuperPeerNums=[xx for xx in range(2001,2005)]
portClientNums=[6010,6011,6012,6013,6014,6015,6016]
# Configure the number of hops a query should propagate to
HOPS=10
# To Configure TTR value in seconds.					  #
TTR=40  #seconds
# Each set corresponds to a peer portNum and the shared path

#SuperPeer1
peer0_port=portSuperPeerNums[0]
peer0_conn=[portSuperPeerNums[1]]

#Client1-1
peer1_id = 1
peer1_port=portClientNums[0]
#peer1_conn=[portSuperPeerNums[0]]
peer1_path='peer_1_sharedFolder/*'

#Client1-2
peer2_id = 2
peer2_port=portClientNums[1]
#peer2_conn=[portSuperPeerNums[0]]
peer2_path='peer_2_sharedFolder/*'

#Client1-3
peer3_id = 3
peer3_port=portClientNums[2]
#peer3_conn=[portSuperPeerNums[0]]
peer3_path='peer_3_sharedFolder/*'

#SuperPeer2
peer10_port=portSuperPeerNums[1]
peer10_conn=[portSuperPeerNums[0]]

#Client2-1
peer4_port=portClientNums[3]
peer4_conn=[portSuperPeerNums[1]]
peer4_path='peer_4_sharedFolder/*'

#Client2-2
peer5_port=portClientNums[4]
peer5_conn=[portSuperPeerNums[1]]
peer5_path='peer_5_sharedFolder/*'

#Clinet2-3
peer6_port=portClientNums[5]
peer6_conn=[portSuperPeerNums[1]]
peer6_path='peer_6_sharedFolder/*'

#SuperPeer3
peer20_port=portSuperPeerNums[2]
peer20_conn=[portSuperPeerNums[1]]