package PeerClient;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.*;

import IndexingServer.IndexServerInterface;

class ClientRequest implements  Runnable {

    private String clientName = null;
    private String port = null;
    private String dirPath = null;
    private IndexServerInterface peerServer;
    private ArrayList<String> clientFiles = new ArrayList<String>();

    ClientRequest(String peername, String port_nbr, IndexServerInterface Server) {
        this.clientName = peername;
        this.port = port_nbr;
        this.peerServer = Server;

    }
    public void run(){

        try {
            this.dirPath = System.getProperty("user.dir");
            System.out.println(" Creating Index for " + clientName + " and files at folder : " + dirPath.toString() );
            File[] files = new File(dirPath).listFiles();
            for ( File f : files) {
                this.clientFiles.add(f.getName());
            }
            peerServer.PeerRegistry(clientName,port,clientFiles);

        } catch ( Exception e){
            System.out.println(e.getMessage());
        }
    }
}

public class PeerClient extends UnicastRemoteObject implements PeerClientInterface, Runnable {

    private String peerName = null;
    private String portNo = null;
    private IndexServerInterface server;

    protected PeerClient() throws RemoteException{
        super();
    }

    protected PeerClient(String peer, String port, IndexServerInterface indexServer) throws RemoteException{

        this.peerName = peer;
        this.portNo = port;
        this.server = indexServer;
        Thread t = new Thread(new ClientRequest(this.peerName,this.portNo,server));
        t.start();
    }

    public String getPort(){
        return portNo;
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
        System.out.println(" Ready to Download the file?: " + filename);
        List<String> peerClient;	//peer client list that contains file
        try {
            peerClient = server.Search(filename,peerName);
            if (peerClient != null) {
                //list peers with file
                System.out.println("The List of Peers with the specified file : ");
                for (int i=0; i<peerClient.size(); i++) {
                    if (peerClient.get(i) != null)
                        System.out.println((i+1)+". " +peerClient.get(i));
                }

                System.out.println("Enter the Peer name to download the file from :");
                return peerClient;
            } else {
                System.out.println("There is No such Peer with your file.");
            }
        } catch (RemoteException e1) {
            e1.printStackTrace();
        }
        return null;
    }

    private void downloadFile(PeerClientServerInterface peerWithFile, String filename) {

        try {
            if(peerWithFile.SendFileToPeer(this,filename)){
                System.out.println("File Downloaded !!!");
            } else {
                System.out.println(" File could not be downloaded... ");
            }
        } catch (RemoteException e) {
            e.printStackTrace();
        }
    }

    public String getPeerName(){

        return peerName;
    }

    public void run(){

        Scanner inputScanner = new Scanner(System.in);

        while(true) {

            System.out.println("Please Enter File Name to be searched for : ");
            String inputFile = inputScanner.nextLine();
            List<String> peerList = findFile(inputFile);
            String peerSelected = inputScanner.nextLine();
            PeerClientServerInterface pcsInterface = null;
            String peerAsServerURL;
            try{
                peerAsServerURL = "rmi://localhost:" + server.PortMap().get(peerSelected) + "/clientServer";
                pcsInterface = (PeerClientServer) Naming.lookup(peerAsServerURL);
            } catch (RemoteException e){
                e.printStackTrace();
            } catch (NotBoundException e){
                e.printStackTrace();
            } catch (MalformedURLException e){
                e.printStackTrace();
            }
            downloadFile(pcsInterface,inputFile);
        }
    }
}
