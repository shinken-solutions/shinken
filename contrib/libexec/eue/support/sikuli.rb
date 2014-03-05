require 'rubygems'
require "xmlrpc/client"
require "inifile"

class Sikuli
	
	attr_accessor :cmd, :pid, :host, :port, :client, :timeout
	
	def initialize(java,sikuli_path,project_path,project_name,host,port,redirect="/dev/null",timeout=60)
		@cmd = [ 
			java, 
			" -Dsikuli.console=true -Dsikuli.debug=0 -Xms512M -Xmx1024M -Dfile.encoding=UTF-8 -jar ",
			sikuli_path,
			"/sikuli-ide.jar -s -r ",
			project_path,
			"/",
			project_name,
			" >> #{redirect} 2>&1"
		].join

		@host = host
		@port = port
		@timeout = timeout
	end
	
	def start_server()

		listen = %x[netstat -ltn | grep -i listen | grep #{@port}]
		if listen != ""
			# puts "sikuli server already started"
			return 0			
		end

		# puts "Starting sikuli server"
		@pid = fork do
			# puts @cmd
			exec @cmd
		end
	
		listen=""		
		while listen.to_s == "" do
			listen = %x[netstat -ltn | grep -i listen | grep #{@port}]
			if listen != ""
				# puts "sikuli server Started"
			end
			sleep 2 
		end	
		Process.detach(@pid)
	end

	def stop_server()
		begin
			@client.call("quit")
		rescue

		end
	end
	
	def start_client()
		@client = XMLRPC::Client.new(host = @host, path = "/", port = @port)
		@client.timeout=@timeout
	end
	
	def call(method)
		# puts "calling %s" % method
		result = @client.call(method)
	end
	
end
