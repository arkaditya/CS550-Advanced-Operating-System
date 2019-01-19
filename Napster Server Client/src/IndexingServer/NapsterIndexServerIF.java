package IndexingServer;
import java.rmi.*;
import java.util.*;

public interface NapsterIndexServerIF extends Remote{

	Hashtable<String,ArrayList<String>> PeerMap = new Hashtable<String,ArrayList<String>>();
	Hashtable<String,ArrayList<String>> PeerRegistry(String peerId, ArrayList<String> fileList) throws RemoteException;
	List<String> Search(String peerId, String filename) throws RemoteException;
}