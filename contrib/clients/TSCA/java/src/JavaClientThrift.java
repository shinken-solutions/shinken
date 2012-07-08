// JavaClientThrift.java

import org.shinken_monitoring.tsca.*;
import org.apache.thrift.TException;
import org.apache.thrift.transport.TSSLTransportFactory;
import org.apache.thrift.transport.TTransport;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TSSLTransportFactory.TSSLTransportParameters;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Date;
import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;

public class JavaClientThrift{

	public static void main(String[] args) throws Exception {

	try
		{
			// Initialise Thrift:
			TTransport transport;
			transport = new TSocket("localhost", 9090);
			transport.open();

			TProtocol protocol = new  TBinaryProtocol(transport);
			StateService.Client client = new StateService.Client(protocol);
			perform(client, args);
			transport.close();
	}
	catch (TException x)
		{
	     	 	x.printStackTrace();
		}
	}

	public static void perform(StateService.Client client, String[] args) throws TException{

		Date date = new Date();
		dataArgs data = new dataArgs();
	 	List<State> list = new ArrayList();
		try{
			BufferedReader file = new BufferedReader(new FileReader(args[0]));
			try{

				String line = new String();
				line = file.readLine();
		                while (line != null){
		                        State state = new State();
                	  	      	state.timestamp = date.getTime();
                        		String[] tab = line.split(",");
                        		state.hostname = tab[0];
		                        state.serv = tab[1];
                	        	state.output = tab[2];
	                        	state.rc = ReturnCode.OK;
        		                list.add(state);
                        		line = file.readLine();
		                }
				file.close();
				data.states = list;
				client.submit_list(data);
				System.out.println();

			}catch(IOException ex){

				System.out.println("Can't read file "+ args[0] +": "+ex.getMessage());

			}


		}catch(FileNotFoundException e)
		{
			System.out.println("Can't find file "+ args[0] +": "+e.getMessage());
		}

	}
}
