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

<div id="login_container" style="margin-left:15%">
  
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
      <p>place</p>
    </div>
    <div class="span6">
      <form method="post" id="loginform" action="/user/auth">
        <label>Name</label>
        <input class="span5" name="login" type="text">

        <label>Password</label>
        <input class="span5" id="password" name="password" type="password">

        <label class="checkbox">
          <input type="checkbox"> Don't forget me!
        </label>
        <button class="btn" type="submit" href="javascript: submitform()">Login</button>
      </form>
    </div>
  </div>
</div>
