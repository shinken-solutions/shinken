%rebase layout title='Shinken UI login', print_menu=False, js=['login/js/jQuery.dPassword.js', 'login/js/iPhonePassword.js'], css=['login/css/login.css']


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
    	<img src="/static/img/logo.png">
    </div>
    <div class="span6">
      <form method="post" id="loginform" action="/user/auth">
        <label>Name</label>
        <input class="span6" name="login" type="text">

        <label>Password</label>
        <input class="span6" id="password" name="password" type="password">

        <label class="checkbox">
          <input type="checkbox"> Don't forget me!
        </label>
        <button class="btn" type="submit" href="javascript: submitform()">Login</button>
      </form>
    </div>
  </div>
</div>