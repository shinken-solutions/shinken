%include header title='Shinken UI login', print_menu=False

				<div id="login-container" class="prefix_custom_2">
				<div class="grid_8">
					<img src="/static/images/robot_rouge_alpha.png" alt="Shinken Login">
				</div>
				<div id="login-form" class="grid_7">
					<form method="post" id="normal_form">
					
						<div class="text-field">
							<label for="email">Login:</label>
							<input type="text" tabindex="1" size="30">
						</div>
						<div class="text-field">
							<label for="user_password">Password:</label>
							<input type="password" tabindex="2" size="30">
					  </div>
						<input type="hidden" value="0" name="remember_me">
					<div class="check-field">
							<input type="checkbox" id="remember_me" tabindex="3" name="remember_me"> <label for="remember_me">Don't forget me</label>
						</div>
						<div class="buttons">
						<a tabindex="4" class="button" href="#">Login</a>
					</div>
					</form>
				</div>
				</div>
			</div>
			<div class="clear"></div>
			<div id="login_footer" class="grid_16">
				<div class="grid_4 border_right">
					<h3>Additional help</h3> 
					<dl>
					    <dt><a href="http://www.shinken-monitoring.org/wiki/">Wiki</a></dt>
					    <dt><a href="http://www.shinken-monitoring.org/forum/">Forum</a></dt>
					</dl>
				</div>
				<div class="grid_4">
					<h3>Version</h3> 
					<dl>
					    <dt>Shinken</dt>
					    <dd>0.6.5</dd>
					    <dt>UI</dt>
					    <dd>0.0.0</dd>
					</dl>
				</div>
			</div>
			<div class="clear"></div>
		</div>
	</body>
</html>
