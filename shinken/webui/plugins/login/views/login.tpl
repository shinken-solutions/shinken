%rebase layout title='Shinken UI login', print_menu=False, js=['login/js/pass_shark.js'], css=['login/css/login.css']

<script type="text/javascript">
	function submitform() {
		document.forms["loginform"].submit();
	}
	
	/* Catch the key ENTER and launch the form 
	 Will be link in the password field
	*/
	function submitenter(myfield,e) {
	  var keycode;
	  if (window.event) keycode = window.event.keyCode;
	  else if (e) keycode = e.which;
	  else return true;
	
	  if (keycode == 13) {
	    submitform();
	    return false;
	  } else
	   return true;
	}

	// Add a iphone like password show/hide 
	window.addEvent('domready', function(){
	  new PassShark('password',{
            interval: 300,
	    duration: 1500,
	    replacement: '%u25CF',
	    debug: false
	  });
	});

</script>

<div id="login_container" style="margin-left: 40.425531911%">
  
%if login_text:
<p><span id="login-text"> {{login_text}}</span></p>
%end
	<div id="login-form">
	%if error:
		<span id="login-error"> {{error}}</span>
	%end
		<form method="post" id="loginform" action="/user/auth">
		<fieldset>		
			<div class="text-field">
			  	<label class="pull-left span2" for="login">Login:</label>
			  	<div class="input"> <input name="login" type="text" tabindex="1" size="30"> </div>
			</div>
			<div class="text-field">
				<label class="pull-left span2" for="password">Password:</label>
				<input id="password" name="password" type="password" tabindex="2" size="30" onKeyPress="return submitenter(this,event)">
			</div>
			<!--
			<div>			
				<label>Don't forget me! </label>
				<input class="pull-left span2" type="checkbox" name="dontforget" value="option1">
			</div>
			-->
			<div>
				<a tabindex="4" class="btn offset1" href="javascript: submitform()">Login</a>
			</div>
        </fieldset>
		</form>
	</div>
</div>
