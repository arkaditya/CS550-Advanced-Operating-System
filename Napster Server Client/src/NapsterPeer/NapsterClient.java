package PeerClient;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.*;

import IndexServerNew.NapsterIndexServerIF;

class ClientRequest implements  Runnable {

    private String clientName = null;
    private String port = null;
    private String dirPath = null;
    private NapsterIndexServerIF peerServer;
    private ArrayList<String> clientFiles = new ArrayList<String>();

    ClientRequest(String peername, String port_nbr, NapsterIndexServerIF Server) {
        this.clientName = peername;
        this.port = port_nbr;
        this.peerServer = Server;
    }
    public void run(){

        try {
            this.dirPath = System.getProperty("user.dir");
            System.out.print(" Creating Index for " + clientName + " and files at folder " + dirPath.toString() );
            System.out.println("\t*****  INDEX SERVER PEER LIST  *****\t\t");
            File[] files = new File(dirPath).listFiles();
            for ( File f : files) {
                this.clientFiles.add(f.getName());
            }
            peerServer.PeerRegistry(clientName,clientFiles);

        } catch ( Exception e){
            System.out.println(e.getMessage());
        }
    }
}

class SearchPeer implements  Runnable {

    private String clientName = null;
    private String fileToSearch = null;
    private NapsterIndexServerIF peerServer;

    SearchPeer(String client, String file, NapsterIndexServerIF Server){
        this.clientName = client;
        this.fileToSearch = file;
        this.peerServer = Server;
    }

    public void run() {

        List<String> filePeerList = null;
        try {
            filePeerList = peerServer.Search(clientName, fileToSearch);
            System.out.println("CLIENTS found by peer  " + filePeerList);
        } catch (RemoteException e) {
            System.out.println("Peer.NapsterClient.SearchPeer Exception : " + e.getMessage());
        }
    }
}
public class NapsterClient extends UnicastRemoteObject implements ClientInterface {

    private String peerName = null;
    private String portNo = null;
    private NapsterIndexServerIF server;


    protected NapsterClient() throws RemoteException{
        super();
    }

    protected NapsterClient(String peer, String port, NapsterIndexServerIF indexServer) throws RemoteException{

        this.peerName = peer;
        this.portNo = port;
        this.server = indexServer;
        Thread t = new Thread(new ClientRequest(this.peerName,this.portNo,server));
        t.start();
    }

    public int acceptPeerConnection(String filename,byte[] stream, int bytes){

        try {
            File newFile = new File(filename);
            newFile.createNewFile();
            FileOutputStream outStream = new FileOutputStream(newFile,true);
            outStream.write(stream,0,bytes);
            outStream.flush();
            outStream.close();
        } catch (IOException e){
                System.out.println("acceptPeerConnection Exception: " + e.getCause());
        }

        return bytes;
    }

    public synchronized List<String> findFile(String filename) {
        System.out.println("Do you want to download the file?: "+filename);
        List<String> peerClient;	//peer client that contains file
        try {
            //returns a peer with file
            peerClient = server.Search(filename,peerName);
            if (peerClient != null) {
                //list peers with file
                System.out.println("Following Peers have your file.:");
                for (int i=0; i<peerClient.size(); i++) {
                    if (peerClient.get(i) != null)
                        System.out.println((i+1)+". "+peerClient.get(i));
                }

                System.out.println("Enter the number matching the Peer you will like to download from");
                return peerClient;
            } else {
                System.out.println("No Peer has your file.");
            }
        } catch (RemoteException e1) {
            e1.printStackTrace();
        }
        return null;
    }

    private void downloadFile(NapsterClientServerIF peerWithFile, String filename) {

        try {
            if(peerWithFile.sendFilefromOnePeertoOther(this,filename)){
                System.out.println("File Downloaded");
                //updateServer();
            } else {
                System.out.println(" File could not be downloaded");
            }
        } catch (RemoteException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

    public String getPeerName(){

        return peerName;
    }
}
