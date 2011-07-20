
<!--
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
				
		<title>Meatball</title>
		<link rel="stylesheet" type="text/css" href="/static/reset.css" media="screen">
		<link rel="stylesheet" type="text/css" href="/static/text.css" media="screen">
		<link rel="stylesheet" type="text/css" href="/static/grid.css" media="screen">
		<link rel="stylesheet" type="text/css" href="/static/layout.css" media="screen">
		<link rel="stylesheet" type="text/css" href="/static/nav-new.css" media="screen">
		<script src="/static/js/mootools-more.js" type="text/javascript"></script>
		<script src="/static/js/rotater.js" type="text/javascript"></script>
		<script src="/static/js/tabs.js" type="text/javascript"></script>

	</head>
	<body>
		<div class="container_16">
-->



%include header title='Host detail about {{host_name}}'

<script type="text/javascript">
  var tabs = new MGFX.Tabs('.tab','.feature',{
  autoplay: false,
  transitionDuration:500,
  slideInterval:3000,
  hover:true
  });
</script>

<!--			<div id="header" class="grid_16">
				<h1 class="box_textshadow">Meatball</h1>
			</div>
			<div class="clear"></div>
			<div id="nav" class="grid_16">
				<ul>
					<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Dashboard</a></li>
					<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Hosts</a></li>
					<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#" id="selected">Incidents</a></li>
					<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Services</a></li>
					<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">System</a></li>
				</ul>
			</div>
			<div class="clear"></div>
			<div id="main_container" class="grid_16">
-->
				<div id="left_container" class="grid_3">
					<div id="dummy_box" class="box_gradient_horizontal"> 
						<p>Dummy box</p>
					</div>
					<div id="nav_left">
						<ul>
							<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Overview</a></li>
							<li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Detail</a></li>
						</ul>
					</div>
				</div>
				<div class="grid_13">
					<div id="host_preview">
						<h2 class="icon_warning">Warning: {{host_name}}</h2>
						<dl class="grid_6">
						    <dt>Alias:</dt>
						    <dd>alias-name</dd>
						    <dt>Parents:</dt>
						    <dd>parents-name</dd>
						    <dt>Members of:</dt>
						    <dd>members-name</dd>
						</dl>
						<dl class="grid_6">
						    <dt>Notes:</dt>
						    <dd>Personal notes (inline editing?) <br> The Hitchhiker’s Guide to the Galaxy / 42</dd>
						</dl>
						<div class="grid_4">
							<img class="box_shadow host_img_80" src="/static/images/no_image.png">
						</div>
					</div>
					<hr>
					<div id="host_overview">
						<h2>Host Overview</h2>
						<div class="grid_6">
							    <table>
									<tbody>
										<tr>
											<th scope="row" class="column1">Host Status</th>
											<td><span class="state_ok icon_ok">UP</span> (for 0d 1h 3m 33s) </td>
										</tr>	
									 	 <tr class="odd">
											<th scope="row" class="column1">Status Information</th>
											<td>Please remove this host later</td>
										</tr>	
									 	<tr>
											<th scope="row" class="column1">Performance Data</th>	
											<td>1</td>
										</tr>
									 	<tr>
											<th scope="row" class="column1">Impact Level</th>	
											<td>5</td>
										</tr>	
									 	<tr class="odd">
											<th scope="row" class="column1">Current Attempt</th>
											<td>1/1 (HARD state)</td>
										</tr>	
									 	<tr>
											<th scope="row" class="column1">Last Check Time</th>
											<td>2011-06-18 23:59:37</td>
										</tr>	
									 	<tr class="odd">
											<th scope="row" class="column1">Check Type</th>
											<td>ACTIVE</td>
										</tr>	
									 	<tr>
											<th scope="row" class="column1">Check Latency / Duration</th>
											<td>0.086  / 0.002 seconds</td>
										</tr>	
									 	<tr class="odd">
											<th scope="row" class="column1">Next Scheduled Active Check</th>
											<td>00:09:39</td>
										</tr>	
									 	<tr>
											<th scope="row" class="column1">Last State Change</th>
											<td>2011-06-18 22:59:32</td>
										</tr>	
									 	<tr class="odd">
											<th scope="row" class="column1">Last Notification</th>
											<td>N/A  (notification 0)</td>
										</tr>	
									 	<tr>						
											<th scope="row" class="column1">Is This Host Flapping?</th>
											<td>NO (0.00% state change)</td>
										</tr>
									 	<tr class="odd">
											<th scope="row" class="column1">In Scheduled Downtime?</th>
											<td>NO</td>
										</tr>	
									 	<tr class="odd">
											<th scope="row" class="column1">Last Update</th>
											<td>00:07:33 (0d 0h 0m 0s ago)</td>
										</tr>
									</tbody>
									<tbody>
									 	<tr class="odd">
											<th scope="row" class="column1">Active Checks</th>
											<td class="icon_tick">ENABLED</td>						
										</tr>	
									 	<tr>
											<th scope="row" class="column1">Passive Checks</th>
											<td class="icon_tick">ENABLED</td>
										</tr>
									 	<tr>
											<th scope="row" class="column1">Obsessing</th>
											<td class="icon_tick">ENABLED</td>
										</tr>
									 	<tr>
											<th scope="row" class="column1">Notifications</th>
											<td class="icon_cross">DISABLE</td>
										</tr>
									 	<tr>
											<th scope="row" class="column1">Event Handler</th>
											<td class="icon_tick">ENABLED</td>
										</tr>
										<tr>
											<th scope="row" class="column1">Flap Detection</th>
											<td class="icon_cross">DISABLE</td>
										</tr>
									</tbody>	
							    </table>
						</div>
					</div>
					<div id="host_more">

					</div>
				</div>
				
			</div>
			<div class="clear"></div>
			<div id="footer" class="grid_16">
				Lorem
			</div>
			<div class="clear"></div>
		</div>

%include footer

