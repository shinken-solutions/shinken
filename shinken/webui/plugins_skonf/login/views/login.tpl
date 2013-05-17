%rebase layout title='Shinken UI login', print_header=False, js=['login/js/detectmobilebrowser.js'], css=['login/css/login.css']

<script type="text/javascript">
// If we are a mobile device, go in the /mobile part :)
  $(document).ready(function(){
  //jQuery.browser.mobile is filled by login/js/detectmobilebrowser.js
  if($.browser.mobile){
    window.location = '/mobile/';
  }
  });
</script>


<div id="login_container" class="span9">

%if login_text:
<p><span id="login-text"> {{login_text}}</span></p>
%end
	<div id="login-form">
	%if error:
		<span id="login-error"> {{error}}</span>
	%end

	</div>
	<div class="row well">
    <div class="span5">
    	<img src="/static/img/logo.png">
    </div>
    <div class="span6">
      <form method="post" id="loginform" action="/user/auth">
        <label>Name</label>
        <input class="span6" name="login" type="text">

        <label>Password</label>
        <input class="span6" id="password" name="password" type="password">
	<!--
        <label class="checkbox">
          <input type="checkbox"> Don't forget me!
        </label>
	-->
	<label/>
        <button class="btn" type="submit" href="javascript: submitform()"><i class="icon-signin"></i> Login</button>
      </form>
    </div>
  </div>
</div>
