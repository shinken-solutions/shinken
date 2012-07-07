%rebase layout_mobile globals(), css=['mobile/css/system.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

<div id="system_overview">
	<h2>System Overview</h2>
	<!-- stats overview start -->
		Program Version: {{VERSION}}
		Program Start Time: {{helper.print_duration(app.datamgr.get_program_start())}}
	<!-- stats overview end -->
</div>

<!-- System Detail START -->

<div id="system_detail">
<!--
	<ul>
	%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
	<div data-role="collapsible-set" data-iconpos="right">
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



%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
<div data-role="collapsible-set" data-iconpos="right">
	%for (sat_type, sats) in types:
	<div data-role="collapsible"  >
		<h3> {{sat_type.capitalize()}}: </h3>
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

			%# End of this satellite
			%end

	</div>
	%end
</div>
</div>
