
%helper = app.helper

%collapsed_s = ''
%collapsed_j = 'false'
%if collapsed:
   %collapsed_s = 'collapsed'
   %collapsed_j = 'true'
%end


<script type="text/javascript">
$(document).ready(function(){

  var w = {'id' : '{{wid}}', 'base_url' : '/widget/system', 'position' : 'widget-place-1',
          'options' : {'key' : 'value'}, 'collapsed' : {{collapsed_j}}};

  // save into widgets
  widgets.push(w);


});
  function submit_{{wid}}_form(){
    var form = document.forms["options-{{wid}}"];
    console.log('Saving form'+form+'and widget'+'{{wid}}');
    var widget = find_widget('{{wid}}');
    // If we can't find the widget, bail out
    if(widget == -1){console.log('cannot find the widget for saving options!'); return;}
    console.log('We fond the widget'+widget);
    %for k in options:
       var v = form.{{k}}.value;
       console.log('Saving the {{k}} with the value'+v);
       widget.options['{{k}}'] = v;
    %end
    // so now we can ask for saving the state :)
    ask_for_widgets_state_save();
  }


</script>



<div class="widget movable collapsable removable editable closeconfirm {{collapsed_s}}" id="{{wid}}">
  <div class="widget-header">
    <strong>System widget</strong>
  </div>
  <div class="widget-editbox">
    <form name='options-{{wid}}'>
      %for (k, v) in options.iteritems():
         %value = v.get('value', '')
         %t = v.get('type', 'text')
         %if t in ['text', 'int']:
            <input name='{{k}}' value='{{value}}'/>
	 %end
	 %if t in ['select']:
	    %values = v.get('values', [])
	    <select name='{{k}}'>
	      %for sub_val in values:
	         <option value="{{sub_val}}">{{sub_val}}</option>
	      %end
            </select>
	 %end
      %end
    </form>

    System widget options
    <a class="widget-close-editbox" onclick="submit_{{wid}}_form();" title="Save changes">Save changes</a>
  </div>
  <div class="widget-content">
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

