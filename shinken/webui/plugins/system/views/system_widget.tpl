%helper = app.helper

%rebase widget globals()

%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]

%# %for (sat_type, sats) in types:
%#   <h5> {{sat_type.capitalize()}}: </h5>

%# 	<table class="table table-striped table-bordered table-condensed">
%# 	%for s in sats:
%# 			<!--<th> </th>-->
%# 			<th> State</th>
%# 			<th> Name</th>
%# 			<th>Alive</th>
%# 			<th>Attempts</th>
%# 			<th>Last check</th>
%# 			<th>Realm</th>
%#
%# 			<tr>
%# 			<!--<td> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>-->
%# 			<td> <div class="aroundpulse">
%#
%# 			%# " We put a 'pulse' around the elements if it's an important one "
%# 			%if not s.alive:
%#
%# 			<span class="pulse"></span>
%# 			%end
%# 			<img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" />
%# 			</div>

%# 			</td>
%# 			<td> {{s.get_name()}}</td>
%# 			<td> {{s.alive}}</td>
%# 			<td> {{s.attempt}}/{{s.max_check_attempts}}</td>
%# 			<td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
%# 			<td>{{s.realm}}</td>
%# 			</tr>
	%# End of this satellite
%# 	%end
%# 	</table>
%# %end

<table class="table table-condensed no-bottommargin topmmargin">
	
	<th class="no-border">Name</th>
	<th class="no-border">Alive</th>
	<th class="no-border">Attempts</th>
	<th class="no-border">Last check</th>
	<th class="no-border">Realm</th>
	<!--<th> </th>-->

	%for (sat_type, sats) in types:
		%for s in sats:
		<tr>
			<!--<td> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>-->
			<td> {{s.get_name()}}</td>
			<td> 
				<div class="aroundpulse">
				%# " We put a 'pulse' around the elements if it's an important one "
				%if not s.alive:
					<span class="pulse"></span>
				%end
					<img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" />
				</div>
			</td>
			<td> {{s.attempt}}/{{s.max_check_attempts}}</td>
			<td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
			<td>{{s.realm}}</td>
		</tr>
		%# End of this satellite
		%end
	%end
</table>