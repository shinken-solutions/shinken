
%rebase layout_skonf globals(), title="Host %s" % elt.get('host_name', 'unknown'),  css=['objects/css/token-input.css', 'objects/css/token-input-facebook.css', 'objects/css/jquery.bsmselect.css', 'objects/css/jquery-ui.css'], js=['objects/js/host.js', 'objects/js/jquery.tokeninput.js', 'objects/js/jquery.bsmselect.js', 'objects/js/jquery.bsmselect.sortable.js', 'objects/js/jquery.bsmselect.compatibility.js', 'objects/js/sliders.js']

<script>
function submit_form(){
 var f = document.forms['form-host'];
 console.log("submiting form"+f);
 console.log('Dump properties'+dump(properties));

 // Sample for bool: $('button[name="process_perf_data"].active').val();
  console.log('Dump process_perf_data'+ $('button[name="process_perf_data"].active').val());


}

// Keep a list of all properties, with their own properties :)
var properties = [];

$(document).ready(function() {
$("select[multiple]").bsmSelect(
{
        showEffect: function($el){ $el.fadeIn(); },
        hideEffect: function($el){ $el.fadeOut(function(){ $(this).remove();}); },
        plugins: [$.bsmSelect.plugins.sortable()],
        title: 'Add',
        highlight: 'highlight',
        addItemTarget: 'original',
        removeLabel: '<span class="token-input-delete-token-facebook">x</span>',
        containerClass: 'bsmContainer span9', // Class for container that wraps this widget
        listClass: 'token-input-list-facebook span8', //bsmList-custom', // Class for the list ($ol)
        listItemClass: 'token-input-token-facebook', // bsmListItem-custom', // Class for the <li> list items
        listItemLabelClass: 'bsmListItemLabel-custom', // Class for the label text that appears in list items
        selectClass : 'bsmSelect span3',
        removeClass: 'bsmListItemRemove-custom' // Class given to the "remove" link
	//extractLabel: function($o) {return $o.parents('optgroup').attr('label') + "&nbsp;>&nbsp;" + $o.html();}
      }
    );

});


$(function() {
    
    $( ".slider" ).slider({
       value:$(this).attr('data-value'),
       min: $(this).attr('data-min'),
       max: $(this).attr('data-max'),
       step: 1,
       slide: function( event, ui ) {
          $(''+$(this).attr('data-log')).html( ui.value+$(this).attr('data-unit'));
          $(this).attr('data-value', ui.value);
    }
    });
    });
    </script>

</script>

<div id="slider"></div>

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
	{{!helper.get_select_input(elt, 'maintenance_period', 'Maintenance Period', 'timeperiods', 'timeperiod_name')}}
	{{!helper.get_select_input(elt, 'check_command', 'Check Command', 'commands', 'command_name')}}
	{{!helper.get_string_input(elt, 'max_check_attemps', 'Max Check Attempts')}}
	{{!helper.get_string_input(elt, 'check_interval', 'Normal Check Interval* 60 seconds')}}
	{{!helper.get_bool_input(elt, 'active_checks_enabled', 'Active Checks Enabled')}}
	{{!helper.get_bool_input(elt, 'passive_checks_enabled', 'Passive Checks Enabled')}}

	{{!helper.get_bool_input(elt, 'notifications_enabled', 'Notification Enabled')}}
	{{!helper.get_multiselect_input(elt, 'contacts', 'Contacts', 'contacts', 'contact_name')}}
	{{!helper.get_multiselect_input(elt, 'contact_groups', 'Contact groups', 'contact_groups', 'contactgroup_name')}}
	{{!helper.get_string_input(elt, 'notification_interval', 'Notification Interval* 60 seconds')}}
	{{!helper.get_select_input(elt, 'notification_period', 'Notification Period', 'timeperiods', 'timeperiod_name' )}}
	{{!helper.get_string_input(elt, 'notification_options', 'Notification Options')}}
	{{!helper.get_string_input(elt, 'first_notification_delay', 'First notification delay')}}

	{{!helper.get_multiselect_input(elt, 'parents', 'Network parents', 'hosts', 'host_name')}}
	

	{{!helper.get_bool_input(elt, 'obsess_over_host', 'Obsess Over Host')}}
	
	{{!helper.get_bool_input(elt, 'check_freshness', 'Check Freshness')}}
	{{!helper.get_string_input(elt, 'freshness_threshold', 'Freshness Threshold seconds')}}
	{{!helper.get_bool_input(elt, 'flap_detection_enabled', 'Flap Detection Enabled')}}
	{{!helper.get_string_input(elt, 'flap_detection_options', 'Flapping options')}}
	{{!helper.get_percent_input(elt, 'low_flap_threshold', 'Low Flap threshold %')}}
	{{!helper.get_string_input(elt, 'high_flap_threshold','High Flap Threshold %')}}
	{{!helper.get_bool_input(elt, 'process_perf_data', 'Process Perf Data')}}

	{{!helper.get_bool_input(elt, 'event_handler_enabled', 'Automatic event Handler Enabled')}}
	{{!helper.get_select_input(elt, 'event_handler', 'Event Handler command', 'commands', 'command_name')}}


	

      </div>
      <!-- Tab Generic stop-->
    </div>

    
    
    <!--{{elt}} -->

  </form>
  <a class='btn btn-info' href="javascript:submit_form()"><i class="icon-ok"></i> Submit</a>
</div>

