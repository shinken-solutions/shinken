

%rebase layout_skonf globals(), title="Host %s" % elt.get('host_name', 'unknown'),  css=['elements/css/token-input.css', 'elements/css/token-input-facebook.css', 'elements/css/jquery.bsmselect.css', 'elements/css/jquery-ui.css'], js=['elements/js/host.js', 'elements/js/jquery.tokeninput.js', 'elements/js/jquery.bsmselect.js', 'elements/js/jquery.bsmselect.sortable.js', 'elements/js/jquery.bsmselect.compatibility.js', 'elements/js/sliders.js', 'elements/js/selects.js', 'elements/js/forms.js']

<script>

// Keep a list of all properties, with their own properties :)
var properties = [];

    </script>

</script>

<div class='offset1 span10'>
  <span id='saving_log' class='hide alert'></span>
</div>

<a class='btn btn-info' href="javascript:submit_form()"><i class="icon-ok"></i> Submit</a>

<div class='offset1 span10'>
  <form name='form-host'>
    <input name="_id" type="hidden" value="{{elt.get('_id', '')}}"/>
    <ul class="nav nav-tabs">
      <li class="active"><a href="#generic" data-toggle="tab">Generic</a></li>
      <li><a href="#macros" data-toggle="tab">Macros</a></li>
      <li><a href="#notifications" data-toggle="tab">Notifications</a></li>
      <li><a href="#depedencies" data-toggle="tab">Dependencies</a></li>
      <li><a href="#advanced" data-toggle="tab">Advanced</a></li>
    </ul>
    
    <div class="tab-content">
      <!-- Tab Generic Stop-->
      <div class="tab-pane active" id="generic">


	{{!helper.get_string_input(elt, 'host_name', 'Hostname', span='span5', popover='Name of the host. Should be unique.')}}
	{{!helper.get_string_input(elt, 'display_name', 'Display name', span='span6', innerspan='span3', placeholder=elt.get('host_name', ''))}}
	{{!helper.get_string_input(elt, 'address', 'Address', span='span5')}}
	<span class="span10">
	  <span class="help-inline span1">Tags </span>
	  <input id='use' class='to_use_complete offset1' data-use='{{elt.get('use', '')}}' name="use" type="text" tabindex="2"/>
	  <script>properties.push({'name' : 'use', 'type' : 'use_tags'});</script>
	</span>
	{{!helper.get_select_input(elt, 'maintenance_period', 'Maintenance Period', 'timeperiods', 'timeperiod_name')}}
	{{!helper.get_select_input(elt, 'check_period', 'Check Period', 'timeperiods', 'timeperiod_name')}}
	{{!helper.get_command_input(elt, 'check_command', 'Check Command', 'commands', 'command_name')}}
	{{!helper.get_string_input(elt, 'max_check_attemps', 'Max Check Attempts')}}
	{{!helper.get_string_input(elt, 'check_interval', 'Normal Check Interval* 60 seconds')}}
	{{!helper.get_bool_input(elt, 'active_checks_enabled', 'Active Checks Enabled')}}
	{{!helper.get_bool_input(elt, 'passive_checks_enabled', 'Passive Checks Enabled')}}


      </div>
      <!-- Tab Generic stop-->

      <!-- Tab Macros -->
      <div class="tab-pane" id="macros">
	None
      </div>
      <!-- Tab Macros stop -->

      <!-- Tab Notifications -->
      <div class="tab-pane" id="notifications">

	{{!helper.get_bool_input(elt, 'notifications_enabled', 'Notification Enabled')}}
	{{!helper.get_multiselect_input(elt, 'contacts', 'Contacts', 'contacts', 'contact_name')}}
	{{!helper.get_multiselect_input(elt, 'contact_groups', 'Contact groups', 'contact_groups', 'contactgroup_name')}}
	{{!helper.get_string_input(elt, 'notification_interval', 'Notification Interval* 60 seconds')}}
	{{!helper.get_select_input(elt, 'notification_period', 'Notification Period', 'timeperiods', 'timeperiod_name' )}}
	{{!helper.get_string_input(elt, 'notification_options', 'Notification Options')}}
	{{!helper.get_string_input(elt, 'first_notification_delay', 'First notification delay')}}


      </div>
      <!-- Tab Notif stop -->

      <!-- Tab Depedencies -->
      <div class="tab-pane" id="depedencies">
	{{!helper.get_multiselect_input(elt, 'parents', 'Network parents', 'hosts', 'host_name')}}
      </div>
      <!-- Tab dep stop -->


      <!-- Tab Advanced -->
      <div class="tab-pane" id="advanced">
	{{!helper.get_poller_tag_input(elt, 'poller_tag', 'Monitored from')}}
	{{!helper.get_realm_input(elt, 'realm', 'Realm')}}

	{{!helper.get_bool_input(elt, 'obsess_over_host', 'Obsess Over Host')}}	
	{{!helper.get_bool_input(elt, 'check_freshness', 'Check Freshness')}}
	{{!helper.get_string_input(elt, 'freshness_threshold', 'Freshness Threshold seconds')}}
	{{!helper.get_bool_input(elt, 'flap_detection_enabled', 'Flap Detection Enabled')}}
	{{!helper.get_string_input(elt, 'flap_detection_options', 'Flapping options')}}
	{{!helper.get_percent_input(elt, 'low_flap_threshold', 'Low Flap threshold %')}}
	{{!helper.get_percent_input(elt, 'high_flap_threshold','High Flap Threshold %')}}
	{{!helper.get_bool_input(elt, 'process_perf_data', 'Process Perf Data')}}

	{{!helper.get_bool_input(elt, 'event_handler_enabled', 'Automatic event Handler Enabled')}}
	{{!helper.get_command_input(elt, 'event_handler', 'Event Handler command', 'commands', 'command_name')}}

      </div>
      <!-- Tab Notif stop -->


    </div>

    
    
    <!--{{elt}} -->

  </form>

</div>

