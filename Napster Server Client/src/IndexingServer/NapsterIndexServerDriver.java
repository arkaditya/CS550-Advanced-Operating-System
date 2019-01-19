
package IndexingServer;
import java.net.MalformedURLException;
import java.rmi.*;
import java.rmi.registry.LocateRegistry;


public class NapsterIndexServerDriver {

    public static void main(String[] args) {

        try {
            NapsterIndexServer obj = new NapsterIndexServer();
            System.out.println("                                                                              ");
            System.out.println("                           PEER-TO-PEER FILE SHARING SYSTEM                 ||");
            System.out.println("                       ========================================             ||");
            System.out.println("                                                                               ");
            System.out.println("                      <CENTRAL INDEX SERVER IS UP AND RUNNING>                ");
            System.out.println("||==========================================================================||");
            System.setProperty("java.rmi.server.hostname","localhost");
            LocateRegistry.createRegistry(2000);
            Naming.rebind("rmi://localhost:2000/Server",obj);
        } catch (RemoteException e) {
            System.out.println(" Index Server Exception : " + e.getMessage());
            e.printStackTrace();
        } catch (MalformedURLException e) {
            System.out.println(" Index Server Exception : " + e.getMessage());
            e.printStackTrace();
        }
    }
}
