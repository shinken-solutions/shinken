%rebase layout_skonf globals(), js=['newhosts/js/newhosts.js'], title='Discover new hosts'

<script type="text/javascript">
function submitform() {
  document.forms["launchform"].submit();
}
</script>

<h2 class="offset1">Discover your new hosts</h2>
<div id="login-form" class="span7 offset1 row-fluid">
  <form method="post" id="launchform" action="/newhosts/launch">
    <div class="textarea-field">
      <label for="names">Scan:</label>
      <textarea name="names" type="textarea" class="span12" tabindex="1" rows="4" placeholder='Please type your hosts IP/FQDN here' value=''></textarea>
    </div>
    <a id='btn_adv_options' class='btn btn-info' href="javascript:newhosts_show_adv_options()"><i class="icon-chevron-down"></i> Show advanced options</a>
    <div id="adv_options">
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
      <a class="btn btn-success" tabindex="4" href="javascript: submitform()"><i class="icon-play"></i> Scan</a>
    </div>
  </form>
</div>

<div class="span4 row-fluid pull-right">
  <div class="well">
    <!-- <img alt="" src="http://placehold.it/300x200"> -->
    <div class="caption">
      <h3 class="font-blue"><i class="icon-question-sign"></i> Information</h3>
      <p>Possible input: IP address (IPv4) or any other Fully Qualified Domain Name (FDQN)
        <br><b>e.g.</b> hamburg.example.com
      </p>
    </div>
  </div>
</div>