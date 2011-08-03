package org.projectsin.client.impl;

import org.json.JSONObject;
import org.projectsin.client.search.SinSenseiRequest;

/**
 * Low-level rest API binding
 * @author john
 * @since 1.0.0
 */
public class SinService {

	public static JSONObject newStore(String host,int port,String store){
		return null;
	}
	
	public static JSONObject openStore(String host,int port,String store){
		return null;
	}
	
	public static JSONObject deleteStore(String host,int port,String store){
		return null;
	}
	
	public static JSONObject addDocs(String host,int port,String store,JSONObject[] docs){
		return null;
	}
	
	public static JSONObject updateDoc(String host,int port,String store,JSONObject doc){
		return null;
	}
	
	public static JSONObject deleteDocs(String host,int port,String store,long[] deletedIds){
		return null;
	}
	
	public static JSONObject search(String senseiHost,int senseiPort,SinSenseiRequest req){
		return null;
	}
}
