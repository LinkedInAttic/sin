package org.projectsin.client;

import org.json.JSONObject;
import org.projectsin.client.impl.SinService;
import org.projectsin.client.search.SinSenseiRequest;
import org.projectsin.client.search.SinSenseiResult;

public class SinStore {
	
	private final String _sinHost;
	private final int _sinPort;
	private final String _senseiHost;
	private final int _senseiPort;
	
	public SinStore(String sinHost,int sinPort,String senseiHost,int senseiPort){
		_sinHost = sinHost;
		_sinPort = sinPort;
		_senseiHost = senseiHost;
		_senseiPort = senseiPort;
	}

	public void addDocs(JSONObject[] docs){
		
	}
	
	public void updateDoc(JSONObject doc){
		
	}
	
	public void deleteDocs(long[] deletedIds){
		
	}
	
	public SinSenseiResult search(SinSenseiRequest req){
		JSONObject resp = SinService.search(_senseiHost, _senseiPort, req);
		return null;
	}
}
