package PeerClient;
import java.rmi.*;

public interface PeerClientServerInterface extends Remote{

    boolean SendFileToPeer(PeerClientInterface c, String file) throws RemoteException;

}
