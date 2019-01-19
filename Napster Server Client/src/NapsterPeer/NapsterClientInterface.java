package NapsterPeer;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface NapsterClientInterface extends Remote {

    int acceptPeerConnection(String filename,byte[] stream, int bytes) throws RemoteException;
    String getPeerName() throws RemoteException;
}
