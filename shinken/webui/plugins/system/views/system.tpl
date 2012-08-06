%rebase layout globals(), css=['system/css/system.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

<div id="system_overview">
	<h2>System Overview</h2>
	<!-- stats overview start -->
		<table class="table table-condensed">
			<tbody>
				<tr>
					<th>Program Version</th>
					<th>Program Start Time</th>
				</tr>
				<tr>
				  <td><a class="quickinfo" href="#">{{VERSION}}</a></td>
				  <td> <a href="#" class="quickinfo" data-original-title="{{helper.print_date(app.datamgr.get_program_start())}}">{{helper.print_duration(app.datamgr.get_program_start())}}</a></td>
				</tr>
			</tbody>
		</table>
	<!-- stats overview end -->
</div>

<!-- System Detail START -->

<div id="system_detail">
<!--
	<ul>
	%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
	%for (sat_type, sats) in types:
		<li class="span2">
		<a  class="box_round_small">
			<div class="modul_name box_halfround_small"><h3>{{sat_type.capitalize()}}:</h3></div>
				%for s in sats:
				<dl>

					<dt>State</dt>
					<dd>
	      				%if not s.alive:
	      					<span class="pulse"></span>
	      				%end
					<img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" alt="stateicon"/>
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
-->

<!--
	<div style="well span12">
		%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]

		%for (sat_type, sats) in types:
		<h3> {{sat_type.capitalize()}}: </h3>

		<table class="table table-striped table-bordered table-condensed">
		%for s in sats:
			<!--<th> </th>-->
<!--
			<th> State</th>
			<th> Name</th>
			<th>Alive</th>
			<th>Attempts</th>
			<th>Last check</th>
			<th>Realm</th>

			<tr>
<!--
			<td> <div class="aroundpulse">

			%# " We put a 'pulse' around the elements if it's an important one "
			%if not s.alive:

			<span class="pulse"></span>
			%end
			<img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" />
			</div>
			</td>
			<td> {{s.get_name()}}</td>
			<td> {{s.alive}}</td>
			<td> {{s.attempt}}/{{s.max_check_attempts}}</td>
			<td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
			<td>{{s.realm}}</td>
			</tr>

			%# End of this satellite
			%end
		</table>
%# end of this satellite type
%end

</div>
-->


    <div style="well span12">
		<table class="table table-bordered table-condensed">
    		%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
	    	%for (sat_type, sats) in types:
            <tr><th class="header" colspan="6">{{sat_type.capitalize()}}:</th></tr>

                %for s in sats:
		        <tr class="odd"><th> State</th><th> Name</th><th>Alive</th><th>Attempts</th><th>Last check</th><th>Realm</th></tr>
    			<tr>
			        <td>
        			<!--<td> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>-->
			        <div class="aroundpulse">
	    		        %# " We put a 'pulse' around the elements if it's an important one "
            			%if not s.alive:
		                	<span class="pulse"></span>
        		    	%end
		        	    <img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" />
        			</div></td>
        			<td> {{s.get_name()}}</td>
        			<td> {{s.alive}}</td>
        			<td> {{s.attempt}}/{{s.max_check_attempts}}</td>
		        	<td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
        			<td>{{s.realm}}</td>
		    	</tr>
                %end
            %end
        </table>
    </div>
</div>
