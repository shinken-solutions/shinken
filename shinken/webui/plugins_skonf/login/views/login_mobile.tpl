%rebase layout title='Shinken UI login', print_menu=False, js=['login/js/pass_shark.js']

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
/*	window.addEvent('domready', function(){
	  new PassShark('password',{
            interval: 300,
	    duration: 1500,
	    replacement: '%u25CF',
	    debug: false
	  });
	});*/

</script>

<div >

%if login_text:
<p><span id="login-text"> {{login_text}}</span></p>
%end
%#	<div class="grid_8">
%#		<img src="/static/images/robot_rouge_alpha.png" alt="Shinken Login">
%#	</div>

	<div id="login-form" class="grid_7">
	%if error:
		<span id="login-error"> {{error}}</span>
	%end
		<form method="post" id="loginform" action="/user/auth">
			<div class="text-field">
			  <label for="login">Login:</label>
				<input name="login" type="text" tabindex="1" size="30">
			</div>
			<div class="text-field">
				<label for="password">Password:</label>
				<input id="password" name="password" type="password" tabindex="2" size="30" onKeyPress="return submitenter(this,event)">
			</div>
			<input type="hidden" value="0" name="remember_me">
				<div class="check-field">
					<input type="checkbox" id="remember_me" tabindex="3" name="remember_me"> <label for="remember_me">Don't forget me</label>
				</div>
				<div class="buttons">
					<a tabindex="4" class="button" href="javascript: submitform()">Login</a>
				</div>
			<input type="hidden" value="1" name="is_mobile">
		</form>
	</div>
</div>
