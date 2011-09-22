
%rebase layout globals()

%helper = app.helper

<div style="margin-left: 20px; width: 70%; float:left;">
  <h2> Schedulers : </h2>
  %for s in schedulers:
  <table class="tableCriticity" style="width: 100%; margin-bottom:3px;">

    <th class="tdBorderLeft tdCriticity" style="width:20px; background:none;"> </th>
    <th class="tdBorderLeft tdCriticity" style="width:20px;"> State</th>
    <th class="tdBorderLeft tdCriticity" style="width: 120px;"> Name</th>
    <th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Ping</th>
    <th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Alive</th>
    <th class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">Last check</th>
    <th class="tdBorderTop tdBorderLeft tdCriticity" style="width:350px;"> </th>

    <tr class="tabledesc">
      <td class="tdBorderLeft tdCriticity" style="width:20px; background:none;"> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>
      <td class="tdBorderLeft tdCriticity" style="width:20px;"> <div class="aroundpulse">
	  %# " We put a 'pulse' around the elements if it's an important one "
	  %if not s.alive:
	  <span class="pulse"></span>
	  %end
	  <img style="width: 16px; height : 16px;" src="/static/images/enabled.png" />
	</div>
      </td>
      <td class="tdBorderLeft tdCriticity" style="width: 120px;"> {{s.get_name()}}</td>
      <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;"> {{s.alive}}</td>
      <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;"> {{s.reachable}}</td>
      <td title='{{helper.print_date(s.last_check)}}' class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
      <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:350px;"> </td>
    </tr>
  </table>
    
  %end
	   
</div>

	
