
%rebase layout_skonf globals()
<div> <h1> Discover your new hosts </h1> </div>


<script type="text/javascript">
  function submitform() {
  document.forms["launchform"].submit();
  }
</script>



<div id="login-form" class="grid_7">
  <form method="post" id="launchform" action="/newhosts/launch">
    <div class="textarea-field">
      <label for="names">Ips/Names:</label>
      <textarea name="names" type="textarea" tabindex="1" size="30">
      </textarea>
    </div>
    <input type="hidden" value="1" name="use_nmap">
    <div class="check-field">
      <input type="checkbox" id="use_nmap" tabindex="1" value="1" name="use_nmap"> <label for="use_nmap">Use Nmap discovery</label>
    </div>
    <input type="hidden" value="1" name="use_vmware">
    <div class="check-field">
      <input type="checkbox" id="use_vmware" tabindex="2" value="1" name="use_vmware"> <label for="use_vmware">Use VMware discovery</label>
    </div>
    <div class="buttons">
      <a tabindex="4" class="button" href="javascript: submitform()">Scan!</a>
    </div>
  </form>
</div>
