

%rebase layout_skonf globals(), title="Host %s" % elt.get('host_name', 'unknown'),  css=['elements/css/token-input.css', 'elements/css/token-input-facebook.css', 'elements/css/jquery.bsmselect.css', 'elements/css/jquery-ui.css'], js=['elements/js/host.js', 'elements/js/jquery.tokeninput.js', 'elements/js/jquery.bsmselect.js', 'elements/js/jquery.bsmselect.sortable.js', 'elements/js/jquery.bsmselect.compatibility.js', 'elements/js/sliders.js', 'elements/js/selects.js', 'elements/js/forms.js', 'elements/js/macros.js']


%editable = ''
%print "EDITABLE?", elt, elt.get('editable', '1')
%if elt.get('editable', '1') == '0':
%editable = 'disabled'
%end

<script>

// Keep a list of all properties, with their own properties :)
var properties = [];

// And keep a list of the ids of the new macros generated
var new_properties = [];


</script>

</script>

<div class='offset1 span10'>
  <span id='saving_log' class='hide alert'></span>
</div>

<a class='btn btn-info {{editable}}' href="javascript:submit_form()"><i class="icon-ok"></i> Submit</a>

<div class='offset1 span10'>
  <form data-table='services' name='form-element'>
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

	{{!helper.get_string_input(elt, 'service_description', 'Name', span='span5', popover='Name of the service.', editable=editable)}}
	{{!helper.get_string_input(elt, 'display_name', 'Display name', span='span6', innerspan='span3', placeholder=elt.get('service_description', ''), editable=editable)}}
	<span class="span10">
	  <span class="help-inline span1">Tags </span>
	  <input id='use' class='to_use_complete offset1' data-use='{{elt.get('use', '')}}' data-cls='host' name="use" type="text" tabindex="2"/>
	  <script>properties.push({'name': 'use', 'type': 'use_tags'});</script>
	</span>
	{{!helper.get_select_input(elt, 'maintenance_period', 'Maintenance Period', 'timeperiods', 'timeperiod_name', editable=editable)}}
	{{!helper.get_select_input(elt, 'check_period', 'Check Period', 'timeperiods', 'timeperiod_name', editable=editable)}}
	{{!helper.get_command_input(elt, 'check_command', 'Check Command', 'commands', 'command_name', editable=editable)}}
	{{!helper.get_multiselect_input(elt, 'host_name', 'Hostnames', 'hosts', 'host_name', editable=editable)}}
	{{!helper.get_string_input(elt, 'max_check_attemps', 'Max Check Attempts', editable=editable)}}
	{{!helper.get_string_input(elt, 'check_interval', 'Normal Check Interval* 60 seconds', editable=editable)}}
	{{!helper.get_bool_input(elt, 'active_checks_enabled', 'Active Checks Enabled', editable=editable)}}
	{{!helper.get_bool_input(elt, 'passive_checks_enabled', 'Passive Checks Enabled', editable=editable)}}


      </div>
      <!-- Tab Generic stop-->

      <!-- Tab Macros -->
      <div class="tab-pane" id="macros">
	{{!helper.get_customs_inputs(app, elt, editable=editable)}}
      </div>
      <!-- Tab Macros stop -->

      <!-- Tab Notifications -->
      <div class="tab-pane" id="notifications">

	{{!helper.get_bool_input(elt, 'notifications_enabled', 'Notification Enabled', editable=editable)}}
	{{!helper.get_multiselect_input(elt, 'contacts', 'Contacts', 'contacts', 'contact_name', editable=editable)}}
	{{!helper.get_multiselect_input(elt, 'contact_groups', 'Contact groups', 'contact_groups', 'contactgroup_name', editable=editable)}}
	{{!helper.get_string_input(elt, 'notification_interval', 'Notification Interval* 60 seconds', editable=editable)}}
	{{!helper.get_select_input(elt, 'notification_period', 'Notification Period', 'timeperiods', 'timeperiod_name' , editable=editable)}}
	{{!helper.get_string_input(elt, 'notification_options', 'Notification Options', editable=editable)}}
	{{!helper.get_string_input(elt, 'first_notification_delay', 'First notification delay', editable=editable)}}


      </div>
      <!-- Tab Notif stop -->

      <!-- Tab Depedencies -->
      <div class="tab-pane" id="depedencies">
	%#{{!helper.get_multiselect_input(elt, 'parents', 'Network parents', 'hosts', 'host_name', editable=editable)}}
      </div>
      <!-- Tab dep stop -->


      <!-- Tab Advanced -->
      <div class="tab-pane" id="advanced">
	{{!helper.get_poller_tag_input(elt, 'poller_tag', 'Monitored from', editable=editable)}}

	{{!helper.get_bool_input(elt, 'obsess_over_service', 'Obsess Over Service', editable=editable)}}
	{{!helper.get_bool_input(elt, 'check_freshness', 'Check Freshness', editable=editable)}}
	{{!helper.get_string_input(elt, 'freshness_threshold', 'Freshness Threshold seconds', editable=editable)}}
	{{!helper.get_bool_input(elt, 'flap_detection_enabled', 'Flap Detection Enabled', editable=editable)}}
	{{!helper.get_string_input(elt, 'flap_detection_options', 'Flapping options', editable=editable)}}
	{{!helper.get_percent_input(elt, 'low_flap_threshold', 'Low Flap threshold %', editable=editable)}}
	{{!helper.get_percent_input(elt, 'high_flap_threshold','High Flap Threshold %', editable=editable)}}
	{{!helper.get_bool_input(elt, 'process_perf_data', 'Process Perf Data', editable=editable)}}

	{{!helper.get_bool_input(elt, 'event_handler_enabled', 'Automatic event Handler Enabled', editable=editable)}}
	{{!helper.get_command_input(elt, 'event_handler', 'Event Handler command', 'commands', 'command_name', editable=editable)}}

      </div>
      <!-- Tab Notif stop -->


    </div>



    <!--{{elt}} -->

  </form>

</div>

