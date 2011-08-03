package org.projectsin.client;

public class SinClient {

	private SinClient(String host,int port){
		
	}
	
	public static SinClient getInstance(String host,int port){
		return new SinClient(host,port);
	}
	
	public SinStore openStore(String name){
		return null;
	}
	
	public SinStore newStore(String name){
		return null;
	}
	
	public void deleteStore(String name){
		
	}
}
