package IndexingServer;
import java.rmi.*;
import java.util.*;

public interface IndexServerInterface extends Remote{

	Hashtable<String,ArrayList<String>> PeerMap = new Hashtable<String,ArrayList<String>>();
	HashMap<String,String> ClientPortMapper = new HashMap<String, String>();
	Hashtable<String,ArrayList<String>> PeerRegistry(String peerId, String portNo, ArrayList<String> fileList) throws RemoteException;
	HashMap<String, String> PortMap() throws RemoteException;
	List<String> Search(String peerId, String filename) throws RemoteException;
}