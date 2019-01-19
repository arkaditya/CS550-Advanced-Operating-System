package NapsterPeer;

import IndexServerNew.NapsterIndexServerIF;

import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.util.Scanner;

public class NapsterClientDriver {

    static String peerserverPort;

    public static void main(String[] args) throws MalformedURLException, RemoteException, NotBoundException {

        try {

            NapsterIndexServerIF serverInterface = (NapsterIndexServerIF) Naming.lookup("rmi://localhost:2000/Server");
            peerserverPort = args[2];
            Client obj = new Client(args[0],args[1],serverInterface);
            new Thread(new peerClientServer()).start();
            Scanner inputScanner = new Scanner(System.in);

            if ( inputScanner.nextLine().equals("YES")){
                System.out.println("File Name to be searched for : ");
                Scanner sc = new Scanner(System.in);
                String inputFile = sc.nextLine();
                SearchPeer getInfo = new SearchPeer(args[0],inputFile,serverInterface);
                Thread searchThread = new Thread(getInfo);
                searchThread.start();
            }

        } catch (Exception e){
            System.out.println("PeerClient.NapsterClient Exception : " + e.getCause());
        }
    }
    static class peerClientServer implements  Runnable{

        public  void run(){

            try {

                String ClientServerURL = "rmi://localhost:" + peerserverPort +"/clientServer";
                System.out.println(ClientServerURL);
                PeerClient.PeerAsServerInterface pServer = new NapsterClientServer();
                Naming.rebind(ClientServerURL,pServer);
            } catch (RemoteException | MalformedURLException | NotBoundException e){
                System.out.println("PeerClient.peerClientServer Exception: ");
                e.printStackTrace();
            }
        }
    }
}
