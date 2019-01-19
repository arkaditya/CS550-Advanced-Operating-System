package PeerClient;

import java.io.*;
import java.net.MalformedURLException;
import java.rmi.*;
import java.rmi.server.UnicastRemoteObject;
import IndexingServer.IndexServerInterface;

public class PeerClientServer extends UnicastRemoteObject implements PeerClientServerInterface {

    private PeerClientInterface obj;
    private String filename;

    public PeerClientServer() throws RemoteException, MalformedURLException, NotBoundException {
        super();
    }

    public synchronized boolean SendFileToPeer(PeerClientInterface obj, String filename) throws RemoteException{

        try {
            File requestedFile = new File(filename);
            FileInputStream inputStream = new FileInputStream(requestedFile);
            byte[] dataStream = new byte[2048*1024];
            while(inputStream.read(dataStream)!= -1){
                if (obj.acceptPeerConnection(requestedFile.getName(),dataStream,inputStream.read(dataStream)) > 0){
                    System.out.println("Sending File " + filename + " to PEER " + obj.getPeerName());
                } else{
                    System.out.println("Failed to send the file  ...");
                }
            }

        } catch (IOException e){
            System.out.println("PeerClientServer Exception: " + e.getCause());
        }

        return true;
    }

}