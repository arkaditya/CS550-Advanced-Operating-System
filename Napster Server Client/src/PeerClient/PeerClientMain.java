package PeerClient;

import IndexingServer.IndexServerInterface;

import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.util.List;
import java.util.Scanner;

public class PeerClientMain {

    static String peerserverPort;

    public static void main(String[] args) throws MalformedURLException, RemoteException, NotBoundException {

        try {

            IndexServerInterface serverInterface = (IndexServerInterface) Naming.lookup("rmi://localhost:2000/Server");
            LocateRegistry.createRegistry(2010);
            peerserverPort = args[1];
            System.out.println("||\tREGISTERING CLIENT " + args[0] + "  TO THE P2P FILE SHARING SYSTEM\t||");
            System.out.println("||\t                                                              \t||");
            PeerClient obj = new PeerClient(args[0],args[1],serverInterface);
            new Thread(new peerClientServer()).start();


        } catch (Exception e){
            System.out.println("PeerClient.NapsterClient Exception : " + e.getCause());
        }
    }
    static class peerClientServer implements  Runnable{

        public  void run(){

            try {

                String ClientServerURL = "rmi://localhost:" + peerserverPort +"/clientServer";
                System.out.println(ClientServerURL);
                PeerClientServerInterface pServer = new PeerClientServer();
                Naming.rebind(ClientServerURL,pServer);
            } catch (RemoteException | MalformedURLException | NotBoundException e){
                System.out.println("PeerClient.peerClientServer Exception: ");
                e.printStackTrace();
            }
        }
    }
}
