package NapsterPeer;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import IndexServerNew.NapsterIndexServerIF;

public class NapsterClientServer extends UnicastRemoteObject implements NapsterClientServerIF {

    private NapsterClientInterface obj;
    private String filename;

    public NapsterClientServer() throws RemoteException, MalformedURLException, NotBoundException {
        super();
    }

    String ServerUrl = "localhost:2000";
    NapsterIndexServerIF serverInterface = (NapsterIndexServerIF) Naming.lookup("rmi://" + ServerUrl + "/Server");

    public synchronized boolean SendFileToPeer(NapsterClientInterface obj, String filename) throws RemoteException{

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
            System.out.println("NapsterClientServer Exception: " + e.getCause());
        }

        return true;
    }

}