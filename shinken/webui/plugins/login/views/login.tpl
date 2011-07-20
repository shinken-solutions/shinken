<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8" />
		<title>Meatball</title>
		<link rel="stylesheet" type="text/css" href="/static/reset.css" media="screen" />
		<link rel="stylesheet" type="text/css" href="/static/text.css" media="screen" />
		<link rel="stylesheet" type="text/css" href="/static/grid.css" media="screen" />
		<link rel="stylesheet" type="text/css" href="/static/layout.css" media="screen" />
		<link rel="stylesheet" type="text/css" href="/static/nav.css" media="screen" />
		<!--<link rel="stylesheet" type="text/css" href="style.css" media="screen" />-->
		<!--[if IE 6]><link rel="stylesheet" type="text/css" href="css/ie6.css" media="screen" /><![endif]-->
		<!--[if IE 7]><link rel="stylesheet" type="text/css" href="css/ie.css" media="screen" /><![endif]-->
	</head>
	<body>
		<div class="container_16">
			<div id="main_container" class="grid_16">
				<div id="login">
				
				<h1>Login</h1>

				<form action="index.php" method="post" name="form1">
					<fieldset class="form">
						<p>
							<label for="user_name">Username:</label>
							<input type="text" value="" id="user_name" name="user_name">
						</p>
						<p>
							<label for="user_password">Password:</label>
							<input type="password" id="user_password" name="user_password">
						</p>
						<button name="Submit" class="positive" type="submit">Login</button>
    				</fieldset>
					</form>	
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
