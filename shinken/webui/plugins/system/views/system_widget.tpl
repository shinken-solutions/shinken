
%from shinken.bin import VERSION
%helper = app.helper

%collapsed_s = ''
%if collapsed:
   %collapsed_s = 'collapsed'
%end


<script type="text/javascript">
$(document).ready(function(){

  var w = {'id' : '{{wid}}', 'base_url' : '/widget/system', 'position' : 'widget-place-1',
          'options' : {'key' : 'value'}};

  // save into widgets
  widgets.push(w);
});
</script>



<div class="widget movable collapsable removable editable closeconfirm {{collapsed_s}}" id="{{wid}}">
  <div class="widget-header">
    <strong>System widget</strong>
  </div>
  <div class="widget-editbox">
    System widget options
  </div>
  <div class="widget-content">
    BLABLA, SYSTEM data


    %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]

    %for (sat_type, sats) in types:
      <h3> {{sat_type.capitalize()}} : </h3>

      <table class="table table-striped table-bordered table-condensed">
	%for s in sats:
			<!--<th> </th>-->
			<th> State</th>
			<th> Name</th>
			<th>Alive</th>
			<th>Attempts</th>
			<th>Last check</th>
			<th>Realm</th>

			<tr>
			<!--<td> <img src="/static/images/untick.png" style="cursor:pointer;" onclick="add_remove_elements('{{s.get_name()}}')" id="selector-{{s.get_name()}}" > </td>-->
			<td> <div class="aroundpulse">

			%# " We put a 'pulse' around the elements if it's an important one "
			%if not s.alive:

			<span class="pulse"></span>
			%end
			</div>
			<img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(s)}}" />
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
      %end
      </div>
</div>

