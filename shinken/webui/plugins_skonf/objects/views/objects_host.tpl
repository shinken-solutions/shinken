
%rebase layout_skonf globals(), title="Host %s" % elt.get('host_name', 'unknown'),  css=['objects/css/token-input.css', 'objects/css/token-input-facebook.css', 'objects/css/jquery.bsmselect.css'], js=['objects/js/host.js', 'objects/js/jquery.tokeninput.js', 'objects/js/jquery.bsmselect.js', 'objects/js/jquery.bsmselect.sortable.js', 'objects/js/jquery.bsmselect.compatibility.js']

<script>
function submit_form(){
 var f = document.forms['form-host'];
 console.log("submiting form"+f);
 console.log('Dump properties'+dump(properties));
}

// Keep a list of all properties, with their own properties :)
var properties = [];

$(document).ready(function() {
$("select[multiple]").bsmSelect(
{
        showEffect: function($el){ $el.fadeIn(); },
        hideEffect: function($el){ $el.fadeOut(function(){ $(this).remove();}); },
        plugins: [$.bsmSelect.plugins.sortable()],
        title: 'Pick some cities',
        highlight: 'highlight',
        addItemTarget: 'original',
        removeLabel: '<strong>X</strong>',
        containerClass: 'bsmContainer', // Class for container that wraps this widget
        listClass: 'bsmList-custom', // Class for the list ($ol)
        listItemClass: 'bsmListItem-custom', // Class for the <li> list items
        listItemLabelClass: 'bsmListItemLabel-custom', // Class for the label text that appears in list items
        removeClass: 'bsmListItemRemove-custom' // Class given to the "remove" link
	//extractLabel: function($o) {return $o.parents('optgroup').attr('label') + "&nbsp;>&nbsp;" + $o.html();}
      }

/*{
        sortable: true,
        animate: true,
        addItemTarget: 'top'
    }*/);
});

</script>

<form>
<select id="cities1" multiple="multiple" name="cities[]" title="Click to Select a City" class="sminit">
  <option>Amsterdam</option>
  <option>Amsterdam</option>
  <option>Amsterdam</option>
  <option>Amsterdam</option>
  <option>Amsterdam</option>
  <option>Amsterdam</option>
</select>
</form>

<div class='offset1 span10'>
  <form name='form-host'>
    <input name="_id" type="hidden" value="{{elt.get('_id', '')}}"/>
    <ul class="nav nav-tabs">
      <li class="active"><a href="#generic" data-toggle="tab">Generic</a></li>
      <li><a href="#macros" data-toggle="tab">Macros</a></li>
      <li><a href="#notifications" data-toggle="tab">Notifications</a></li>
      <li><a href="#depdencies" data-toggle="tab">Dependencies</a></li>
      <li><a href="#graphs" data-toggle="tab" >Advanced</a></li>
    </ul>
    
    <div class="tab-content">
      <!-- Tab Generic Stop-->
      <div class="tab-pane active" id="generic">


	{{!helper.get_string_input(elt, 'host_name', 'Hostname')}}
	{{!helper.get_string_input(elt, 'display_name', 'Display name')}}
	{{!helper.get_string_input(elt, 'address', 'Address')}}
	<span class="span10">
	  <span class="help-inline">Tags </span>
	  <input id='input-{{elt['host_name']}}' class='to_use_complete' data-use='{{elt.get('use', '')}}' name="use" type="text" tabindex="2"/>
	</span>
	{{!helper.get_string_input(elt, 'poller_tag', 'Monitored from')}}
	{{!helper.get_select_input(elt, 'check_period', 'Check Period', 'timeperiods', 'timeperiod_name')}}
	{{!helper.get_select_input(elt, 'check_command', 'Check Command', 'commands', 'command_name')}}
	{{!helper.get_string_input(elt, 'max_check_attemps', 'Max Check Attempts')}}
	{{!helper.get_string_input(elt, 'check_interval', 'Normal Check Interval* 60 seconds')}}
	{{!helper.get_string_input(elt, 'active_checks_enabled', 'Active Checks Enabled')}}
	{{!helper.get_string_input(elt, 'passive_checks_enabled', 'Passive Checks Enabled')}}

	{{!helper.get_string_input(elt, 'notifications_enabled', 'Notification Enabled')}}
	{{!helper.get_select_input(elt, 'contacts', 'Contacts', 'contacts', 'contact_name')}}
	{{!helper.get_string_input(elt, 'contact_groups', 'Contact groups')}}
	{{!helper.get_string_input(elt, 'notification_interval', 'Notification Interval* 60 seconds')}}
	{{!helper.get_select_input(elt, 'notification_period', 'Notification Period', 'timeperiods', 'timeperiod_name' )}}
	{{!helper.get_string_input(elt, 'notification_options', 'Notification Options')}}
	{{!helper.get_string_input(elt, 'first_notification_delay', 'First notification delay')}}

	{{!helper.get_select_input(elt, 'parents', 'Network parents', 'hosts', 'host_name')}}
	

	{{!helper.get_string_input(elt, 'obsess_over_host', 'Obsess Over Host')}}
	{{!helper.get_string_input(elt, 'check_freshness', 'Check Freshness')}}
	{{!helper.get_string_input(elt, 'freshness_threshold', 'Freshness Threshold seconds')}}
	{{!helper.get_string_input(elt, 'flap_detection_enabled', 'Flap Detection Enabled')}}
	{{!helper.get_string_input(elt, 'flap_detection_options', 'Flapping options')}}
	{{!helper.get_string_input(elt, 'low_flap_threshold', 'Low Flap threshold %')}}
	{{!helper.get_string_input(elt, 'high_flap_threshold','High Flap Threshold %')}}
	{{!helper.get_string_input(elt, 'process_perf_data', 'Process Perf Data')}}

	{{!helper.get_string_input(elt, 'event_handler_enabled', 'Automatic event Handler Enabled')}}
	{{!helper.get_select_input(elt, 'event_handler', 'Event Handler command', 'commands', 'command_name')}}


	

      </div>
      <!-- Tab Generic stop-->
    </div>

    
    
    <!--{{elt}} -->
   
  </form>
  <a class='btn btn-info' href="javascript:submit_form()"><i class="icon-ok"></i> Submit</a>
</div>

