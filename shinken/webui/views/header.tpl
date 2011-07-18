

%#Set default values
%if not 'js' in locals() : js = []
%if not 'title' in locals() : title = 'No title'
%if not 'css' in locals() : css = []



 <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html slick-uniqueid="1"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>{{title or 'No title'}}</title>

    <link rel="stylesheet" type="text/css" href="static/nav.css">
    <link rel="stylesheet" type="text/css" href="static/reset.css" media="screen">
    <link rel="stylesheet" type="text/css" href="static/text.css" media="screen">
    <link rel="stylesheet" type="text/css" href="static/grid.css" media="screen">
    <link rel="stylesheet" type="text/css" href="static/layout.css" media="screen">
    <link rel="stylesheet" type="text/css" href="static/nav-new.css" media="screen">
    <script type="text/javascript" src="static/js/rotater.js"></script>
    <script type="text/javascript" src="static/js/tabs.js"></script>
    <script type="text/javascript" src="static/js/mootools.js"></script>
    <script type="text/javascript" src="static/js/mootools-more.js"></script>
    <script type="text/javascript" src="static/js/mootools-message.js"></script>



%# End of classic js import. Now call for specific ones
%for p in js:
  <script type="text/javascript" src="static/js/{{p}}"></script>
%end


%# And now for css files
%for p in css:
    <link rel="stylesheet" type="text/css" href="static/{{p}}">
%end

  </head>
  <body class="main">
		<div class="container_16">
			<div id="header" class="grid_16">
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
