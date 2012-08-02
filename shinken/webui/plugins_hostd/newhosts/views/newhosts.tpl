
%rebase layout_skonf globals(), js=['newhosts/js/newhosts.js']

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
      <input type="hidden" value="1" name="use_nmap">
      <div class="check-field">
	<span class="help-inline">Use Nmap discovery</span>
	<input type="checkbox" id="use_nmap" tabindex="1" checked name="use_nmap">
	<p class="help-block" for="use_vmware"> Nmap is a network based scanner</p>
      </div>
      <input type="hidden" value="1" name="use_vmware">
      <div class="check-field">
	<span class="help-inline">Use VMware/vSphere discovery</span>
	<input type="checkbox" id="use_vmware" tabindex="2" checked name="use_vmware">
      </div>
    </div>
    <div class="pull-right">
      <a class='btn btn-success' tabindex="4" href="javascript: submitform()">Scan!</a>
    </div>

  </form>
</div>
