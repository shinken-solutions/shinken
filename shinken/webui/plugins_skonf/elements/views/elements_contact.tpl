%rebase layout_skonf globals(), css=['elements/css/token-input.css', 'elements/css/token-input-facebook.css', 'elements/css/jquery.bsmselect.css', 'elements/css/jquery-ui.css'], js=['elements/js/host.js', 'elements/js/jquery.tokeninput.js', 'elements/js/jquery.bsmselect.js', 'elements/js/jquery.bsmselect.sortable.js', 'elements/js/jquery.bsmselect.compatibility.js', 'elements/js/sliders.js', 'elements/js/selects.js', 'elements/js/forms.js', 'elements/js/macros.js'], title='Contact'

%editable = ''
%print "EDITABLE?", elt, elt.get('editable', '1')
%if elt.get('editable', '1') == '0':
%editable = 'disabled'
%end

<script>
  // Keep a list of all properties, with their own properties :)
  var properties = [];
  var new_properties = [];
</script>

<div class="row-fluid">
  <span id="saving_log" class="hide alert"></span>
</div>

<!-- <a class='btn btn-info' href="javascript:submit_form()"><i class="icon-ok"></i> Submit</a> -->

<div class="row-fluid">
  <div data-table='contacts' name='form-element'>
    <input name="_id" type="hidden" value="{{elt.get('_id', '')}}"/>
    <ul class="nav nav-tabs">
      <li class="active"><a href="#generic" data-toggle="tab">Generic</a></li>
      <li><a href="#direct" data-toggle="tab">Direct configuration</a></li>
      <li><a href="#macros" data-toggle="tab">Macros</a></li>
      <a href="javascript:submit_form()" class="btn btn-small btn-info pull-right"><i class="icon-ok"></i> Submit</a>
    </ul>

    <div class="tab-content">

<!-- Tab Generic Stop-->
<div class="tab-pane active" id="generic">
  <div class="span6">
    {{!helper.get_string_input(elt, 'contact_name', 'Contact name', span='', editable=editable)}}

    {{!helper.get_string_input(elt, 'display_name', 'Display name', span='', innerspan='', placeholder=elt.get('contact_name', ''), editable=editable)}}
  </div>
	
  <div class="span6">
    {{!helper.get_string_input(elt, 'email', 'Email', span='', editable=editable)}}
  
    {{!helper.get_string_input(elt, 'pager', 'Phone', span='', editable=editable)}}
  </div>

  <div class="span12 no-leftmargin">
    <form class="form-horizontal">
      <div class="control-group">
        <label class="control-label">Tags </label>
          <div class="controls"> 
            <input id='use' class="to_use_complete" data-use='{{elt.get('use', '')}}' data-cls='contact' name="use" type="text" tabindex="2"/>
          </div>
        <script>properties.push({'name': 'use', 'type': 'use_tags'});</script>
      </div>
    </form>
  </div>

  <div class="span6 no-leftmargin">
    {{!helper.get_bool_input(elt, 'can_submit_commands', 'Can submit command', editable=editable)}}
    {{!helper.get_bool_input(elt, 'is_admin', 'Is a monitoring administrator', editable=editable)}}
  </div>
	
</div>
<!-- Tab Generic stop-->

<!-- Tab Macros -->
<div class="tab-pane" id="direct">
	{{!helper.get_select_input(elt, 'host_notification_period', 'Host notification Period', 'timeperiods', 'timeperiod_name', editable=editable)}}

	{{!helper.get_select_input(elt, 'service_notification_period', 'Service notification Period', 'timeperiods', 'timeperiod_name', editable=editable)}}

	{{!helper.get_bool_input(elt, 'host_notifications_enabled', 'Enable host notifications', editable=editable)}}

	{{!helper.get_bool_input(elt, 'service_notifications_enabled', 'Enable service notifications', editable=editable)}}

	{{!helper.get_multiselect_input(elt, 'host_notification_commands', 'Host notification commands', 'commands', 'command_name', editable=editable)}}

	{{!helper.get_multiselect_input(elt, 'service_notification_commands', 'Service notification commands', 'commands', 'command_name', editable=editable)}}

	{{!helper.get_string_input(elt, 'host_notification_options', 'Host notification options', editable=editable)}}
	
  {{!helper.get_string_input(elt, 'service_notification_options', 'Service notification options', editable=editable)}}

	{{!helper.get_string_input(elt, 'min_business_impact', 'Minimum business impact (filter)', editable=editable)}}
</div>
      <!-- Tab Macros stop -->


<!-- Tab Macros -->
<div class="tab-pane" id="macros">
	{{!helper.get_customs_inputs(app, elt, editable=editable)}}
</div>
<!-- Tab Macros stop -->




    </div>



    <!--{{elt}} -->

  </div>

</div>

