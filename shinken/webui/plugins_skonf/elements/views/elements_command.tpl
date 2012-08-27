

%rebase layout_skonf globals(), title="Host %s" % elt.get('host_name', 'unknown'),  css=['elements/css/token-input.css', 'elements/css/token-input-facebook.css', 'elements/css/jquery.bsmselect.css', 'elements/css/jquery-ui.css'], js=['elements/js/host.js', 'elements/js/jquery.tokeninput.js', 'elements/js/jquery.bsmselect.js', 'elements/js/jquery.bsmselect.sortable.js', 'elements/js/jquery.bsmselect.compatibility.js', 'elements/js/sliders.js', 'elements/js/selects.js', 'elements/js/forms.js', 'elements/js/macros.js'], title='Command'


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
  <form data-table='commands' name='form-element'>
    <input name="_id" type="hidden" value="{{elt.get('_id', '')}}"/>
    <ul class="nav nav-tabs">
      <li class="active"><a href="#generic" data-toggle="tab">Generic</a></li>
      <li><a href="#advanced" data-toggle="tab">Advanced</a></li>
    </ul>

    <div class="tab-content">
      <!-- Tab Generic Stop-->
      <div class="tab-pane active" id="generic">


	{{!helper.get_string_input(elt, 'command_name', 'Name', span='span5', popover='Name of the command. Should be unique.', editable=editable)}}
	{{!helper.get_string_input(elt, 'command_line', 'Command', span='span10', inputsize='input-xxlarge', editable=editable)}}
      </div>
      <!-- Tab Generic stop-->



      <!-- Tab Advanced -->
      <div class="tab-pane" id="advanced">
	{{!helper.get_poller_tag_input(elt, 'poller_tag', 'Monitored from', editable=editable)}}
	{{!helper.get_string_input(elt, 'module_type', 'Module type', editable=editable)}}

      </div>
      <!-- Tab Notif stop -->


    </div>



    <!--{{elt}} -->

  </form>

</div>

