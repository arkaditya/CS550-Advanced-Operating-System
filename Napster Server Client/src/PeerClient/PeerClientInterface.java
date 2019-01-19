package PeerClient;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface PeerClientInterface extends Remote {

    int acceptPeerConnection(String filename,byte[] stream, int bytes) throws RemoteException;
    String getPeerName() throws RemoteException;
}
