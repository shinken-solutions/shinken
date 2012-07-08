#!/usr/bin/env ruby

$:.push('../../../../thrift/gen-rb')
$:.unshift '../../../lib/rb/lib'

require 'csv'
require 'thrift'
require 'state_service'

begin
 port = 9090
 transport = Thrift::BufferedTransport.new(Thrift::Socket.new('localhost', port))
 protocol = Thrift::BinaryProtocol.new(transport)
 client = Org::Shinken_monitoring::TSCA::StateService::Client.new(protocol)
 transport.open()
 list = Array.new
 data = Org::Shinken_monitoring::TSCA::DataArgs.new()

 CSV.open(ARGV[0], 'r', ',') do |row|
   trace = Org::Shinken_monitoring::TSCA::State.new()
   trace.timestamp = Time.now.to_i
   trace.hostname = row[0]
   trace.serv = row[1]
   trace.output = row[2]
   trace.rc = Org::Shinken_monitoring::TSCA::ReturnCode::OK
   list.push(trace)
 end
 data.states = list
 client.submit_list(data)
 transport.close()
rescue Thrift::Exception => tx
  print 'Thrift::Exception: ', tx.message, "\n"
end
