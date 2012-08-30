
%rebase layout_skonf globals(), js=['newhosts/js/newhosts.js'], title='Discover new hosts'

<script type="text/javascript">
  function submitform() {
  document.forms["launchform"].submit();
  }
</script>



<div id="login-form" class="span5 offset2">
  <h2> Discover your new hosts </h2>
  <form method="post" id="launchform" action="/newhosts/launch">
    <div class="textarea-field">
      <label for="names">Scan:</label>
      <textarea name="names" type="textarea" class='input-xxlarge' tabindex="1" rows="4" placeholder='Please type your hosts IP/FQDN here' value=''></textarea>
    </div>
    <a id='btn_adv_options' class='btn btn-info' href="javascript:newhosts_show_adv_options()"><i class="icon-chevron-down"></i> Show advanced options</a></span>

    <div id='adv_options'>
      %print 'DATAMGR', app.conf.discoveryruns.__dict__
      %i = 0
      %# """ Only take the first level discovery runners here"""
      %for r in [r for r in app.conf.discoveryruns if r.is_first_level()]:
         %i += 1
         <input type="hidden" value="1" name="runner-{{r.get_name()}}">
	 <div class="check-field">
           <span class="help-inline">Enable the {{r.get_name().capitalize()}} based discovery</span>
           <input type="checkbox" id="enable-runner-{{r.get_name()}}" tabindex="{{i}}" checked name="enable-runner-{{r.get_name()}}">
           <p class="help-block" for="enable-runner-{{r.get_name()}}"> </p>
	 </div>
      %end
    </div>
    <div class="pull-right">
      <a class='btn btn-success' tabindex="4" href="javascript: submitform()">Scan!</a>
    </div>

  </form>
</div>
