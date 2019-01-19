package NapsterPeer;
import java.rmi.*;

public interface NapsterClientServerIF extends Remote{

    boolean SendFileToPeer(NapsterClientInterface c, String file) throws RemoteException;

}
