%rebase layout globals(), css=['system/css/system.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

%#  "Left Container Start"
<div id="left_container" class="grid_2">
	<div id="nav_left">
		<ul>
			<li><a href="/system">System</a></li>
			%#<li><a href="/system/log">Log</a></li>
		</ul>
	</div>
</div>
%#  "Left Container End"

<div id="system_overview" class="grid_14 item">
	<h2>System Overview</h2>
	<!-- stats overview start -->
		<table style="width: 100%">
			<tbody>
				<tr class="grid_16">
					<th class="grid_4">Program Version</th>
					<th class="grid_4">Program Start Time</th>
				</tr>							
				<tr class="grid_16">
				  <td class="grid_4"> {{VERSION}}</td>
				  <td title="{{helper.print_date(app.datamgr.get_program_start())}}" class="grid_4"> {{helper.print_duration(app.datamgr.get_program_start())}}</td>
				</tr>							
			</tbody>
		</table> 
	<!-- stats overview end -->
</div>

<!-- System Detail START -->

<div id="system_detail" class="grid_14">
	<ul>
	%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
	%for (sat_type, sats) in types:
		<li class="grid_3">
		<a  class="box_round_small">
			<div class="modul_name box_halfround_small"><h3>{{sat_type.capitalize()}} :</h3></div>
				%for s in sats:
				<dl>
				
					<dt>State</dt>
					<dd>	     
	      				%if not s.alive:
	      					<span class="pulse"></span>
	      				%end
	      				<img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(s)}}" alt="stateicon"/>
	      			</dd>
					<dt>Name</dt>
					<dd>{{s.get_name()}}</dd>
					<dt>Alive</dt>
					<dd>{{s.alive}}</dd>
					<dt>Attempts</dt>
					<dd>{{s.attempt}}/{{s.max_check_attempts}}</dd>
					<dt>Last check</dt>
					<dd title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</dd>
					<dt>Realm</dt>
					<dd>{{s.realm}}</dd>
				
				</dl>
				%# end of this satellite type
 				%end
		</a>
		</li>
	%# end of this satellite type
 	%end
	</ul>
</div>	