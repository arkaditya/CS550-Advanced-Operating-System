
package PeerClient;

import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchEvent;
import java.nio.file.WatchKey;
import java.nio.file.WatchService;
/**
 NapsterDirectoryLis Implementation
 event listener that monitors the root directory of the server and gets modified if changes made it to it
 */
public class NapsterDirectoryLis implements Runnable {
	private PeerClientInterface peer_Client;
	public NapsterDirectoryLis(PeerClient peerClient) {
		// TODO Auto-generated constructor stub
		this.peer_Client = peerClient;
	}

	@Override
	public void run() {
		try {
			WatchService Filewatcher = FileSystems.getDefault().newWatchService();
			Path dir = Paths.get(peer_Client.getClientDirectory());
		    WatchKey WatcherKey = dir.register(Filewatcher, StandardWatchEventKinds.ENTRY_CREATE, 
		    			StandardWatchEventKinds.ENTRY_DELETE, StandardWatchEventKinds.ENTRY_MODIFY);
		    for (;;) {
		        try {
		        	WatcherKey = Filewatcher.take();
		        } catch (InterruptedException x) {
		            return;
		        }
		        boolean doUpdateForNewFileFlag = false;
		        for (WatchEvent<?> eventValue: WatcherKey.pollEvents()) {
		            WatchEvent.Kind<?> kind_event = eventValue.kind();				            
		            if (kind_event == StandardWatchEventKinds.OVERFLOW) {
		                continue;
		            }
		            if (kind_event==StandardWatchEventKinds.ENTRY_DELETE || kind_event==StandardWatchEventKinds.ENTRY_MODIFY){
		            	peer_Client.updateIndexServer();
		            }
		            if (kind_event == StandardWatchEventKinds.ENTRY_CREATE) {
		            	if(doUpdateForNewFileFlag)
		            		peer_Client.updateIndexServer();
		            	else
		            		doUpdateForNewFileFlag = true;
		            }
		        }
		        boolean validvalue = WatcherKey.reset();
		        if (!validvalue) {
		            break;
		        }
		    }
		} catch (IOException x) {
		    System.err.println(x);
		}
	}	
}