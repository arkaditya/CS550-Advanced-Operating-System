package IndexingServer;
import java.lang.Exception;
import java.rmi.*;
import java.rmi.server.UnicastRemoteObject;
import java.util.*;

public class NapsterIndexServer extends UnicastRemoteObject implements NapsterIndexServerIF
{
	NapsterIndexServer() throws RemoteException {
		super();
	}
	private ArrayList<String>  peerList = new ArrayList<String>();
	//public Hashtable<String,ArrayList<String>> PeerMap = new Hashtable<String,ArrayList<String>>();
    private Enumeration peerlist;

	public synchronized Hashtable<String,ArrayList<String>> PeerRegistry(String peer, ArrayList<String> fileList) throws RemoteException {

		peerList.add(peer);
		PeerMap.put(peer,fileList);
		System.out.println("Peer Name: " + peer + "\nFiles: " + PeerMap.get(peer));
		ClientRegistered();
		return PeerMap;
	}

	public void UpdateRegistry() {
    }

	private void ClientRegistered() {

		System.out.println("\t*****  INDEX SERVER PEER LIST  *****\t\t");
		try {
            peerlist = PeerMap.keys();
            String name;
            while (peerlist.hasMoreElements()) {
                name = (String) peerlist.nextElement();
                System.out.println(name + " : " + PeerMap.get(name));
            }
            System.out.println("=====================================================\t");
        } catch (Exception e) {
            System.out.println("PeerClient.NapsterClient Registration Exception : " + e.getMessage());
		}
	}

	public synchronized List<String> Search(String requestPeerId, String filename) throws RemoteException {

	    List<String> ClientList = new ArrayList<String>(PeerMap.size());
        int count = 0;
        boolean fileFoundFlag = false;
        peerlist = PeerMap.keys();
        String peerName = new String();

        System.out.println("Peer : " + requestPeerId + " requested files '" + filename + "'");
        while (peerlist.hasMoreElements()) {

            peerName = (String)peerlist.nextElement();
            ArrayList<String> files = PeerMap.get(peerName);
            for (String f : files)
                if (filename.equalsIgnoreCase(f))
                    fileFoundFlag = true;
                    ClientList.add(count,peerName);
                    count++;
        }
        if ( fileFoundFlag){
            System.out.println("FOUND Clients...  " + ClientList);
            return ClientList;
        } else {
            return null;
        }
    }
}