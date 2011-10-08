%rebase layout globals(), css=['system/css/system.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

<div id="system_overview" class="grid_16 item">
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
	<!--
	<ul>
		<li> <a href="#">Arbiter</a></li>
		<li> <a href="#">State</a> </li>
		<li> <a href="#">Name</a> </li>
		<li> <a href="#">Alive</a> </li>
		<li> <a href="#">Attempts</a> </li>
		<li> <a href="#">Last Check</a> </li>
		<li> <a href="#">Realm</a> </li>
	</ul>
	-->
</div>


<div id="system_detail" class="grid_16">
  %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]

  %for (sat_type, sats) in types:
    <h2> {{sat_type.capitalize()}} : </h2>
    <table>
    %for s in sats:


	<th class="grid_2"> </th>
	<th class="grid_2"> State</th>
	<th class="grid_2"> Name</th>
	<th class="grid_2">Alive</th>
	<th class="grid_2">Attempts</th>
	<th class="grid_2">Last check</th>
	<th class="grid_2">Realm</th>

	<tr class="tabledesc">
	  <td class="grid_2"> <img src="/static/images/untick.png" alt="untick" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>
	  <td class="grid_2">
	  	<div class="aroundpulse">
	      %# " We put a 'pulse' around the elements if it's an important one "
	      %if not s.alive:
	      <span class="pulse"></span>
	      %end
	      <img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(s)}}" alt="stateicon"/>
	    </div>
	  </td>
	  <td class="grid_2"> {{s.get_name()}}</td>
	  <td class="grid_2"> {{s.alive}}</td>
	  <td class="grid_2"> {{s.attempt}}/{{s.max_check_attempts}}</td>
	  <td class="grid_2" title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
	  <td class="grid_2">{{s.realm}}</td>
	</tr>

    %# End of this satellite
    %end
    </table> 
 %# end of this satellite type
 %end

	   
</div>

<!-- System Detail START -->

<div id="system_detail" class="grid_16">

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