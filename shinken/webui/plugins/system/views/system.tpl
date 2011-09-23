%rebase layout globals(), css=['system/css/system.css'], title='Architecture state', menu_part='/system'

%helper = app.helper

<div id="system_overview" class="grid_16 item">
	<h2>System Overview</h2>
	<!-- stats overview start -->
		<table style="width: 100%">
			<tbody>
				<tr class="grid_16">
					<th class="grid_4">Program Version</th>
					<th class="grid_4">Program Start Time</th>
					<th class="grid_4">Total Running Time</th>
					<th class="grid_4">Last External Command Check</th>
				</tr>							
				<tr class="grid_16">
					<td class="grid_4"> 0.6.5+</td>
					<td class="grid_4"> Friday, 22.09.2011</td>
					<td class="grid_4"> 9 Days 12 hours 2 min</td>
					<td class="grid_4"> 5 mins</td>
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


<div style="margin-left: 20px; width: 70%; float:left;">
  %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]

  %for (sat_type, sats) in types:
    <h2> {{sat_type.capitalize()}} : </h2>
    <table class="tableCriticity" style="width: 100%; margin-bottom:3px;">
    %for s in sats:


	<th class="tdBorderLeft tdCriticity" style="width:20px; background:none;"> </th>
	<th class="tdBorderLeft tdCriticity" style="width:20px;"> State</th>
	<th class="tdBorderLeft tdCriticity" style="width: 120px;"> Name</th>
	<th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Alive</th>
	<th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Attempts</th>
	<th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Last check</th>
	<th class="tdBorderTop tdBorderLeft tdCriticity" style="width:350px;">Realm</th>

	<tr class="tabledesc">
	  <td class="tdBorderLeft tdCriticity" style="width:20px; background:none;"> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>
	  <td class="tdBorderLeft tdCriticity" style="width:20px;"> <div class="aroundpulse">
	      %# " We put a 'pulse' around the elements if it's an important one "
	      %if not s.alive:
	      <span class="pulse"></span>
	      %end
	      <img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(s)}}" />
	    </div>
	  </td>
	  <td class="tdBorderLeft tdCriticity" style="width: 120px;"> {{s.get_name()}}</td>
	  <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;"> {{s.alive}}</td>
	  <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;"> {{s.attempt}}/{{s.max_check_attempts}}</td>
	  <td title='{{helper.print_date(s.last_check)}}' class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
	  <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:350px;">{{s.realm}}</td>
	</tr>

    %# End of this satellite
    %end
    </table> 
 %# end of this satellite type
 %end

	   
</div>

	
