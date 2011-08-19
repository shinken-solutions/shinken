<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">


%#Set default values
%if not 'js' in locals() : js = []
%if not 'title' in locals() : title = 'No title'
%if not 'css' in locals() : css = []
%if not 'print_menu' in locals() : print_menu = True

%if not 'top_right_banner_state' in locals() : top_right_banner_state = 1


<html slick-uniqueid="1"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>{{title or 'No title'}}</title>

    <link rel="stylesheet" type="text/css" href="/static/nav.css">
    <link rel="stylesheet" type="text/css" href="/static/reset.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/text.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/grid.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/layout.css" media="screen">
    <script type="text/javascript" src="/static/js/mootools.js"></script>
    <script type="text/javascript" src="/static/js/mootools-more.js"></script>
    <script type="text/javascript" src="/static/js/mootools-message.js"></script>

    <script type="text/javascript" src="/static/js/rotater.js"></script>
    <script type="text/javascript" src="/static/js/tabs.js"></script>



%# End of classic js import. Now call for specific ones
%for p in js:
  <script type="text/javascript" src="/static/{{p}}"></script>
%end


%# And now for css files
%for p in css:
    <link rel="stylesheet" type="text/css" href="/static/{{p}}">
%end

  </head>
  <body class="main">


		<div class="container_16">

			<div id="header" class="grid_16">
				<h1 class="box_textshadow">Meatball</h1>
%# Set the Top right banner if need
%if top_right_banner_state != 0:
<img class="top_right_banner" style="position: absolute;
top: 0;
right: 0;
border: 0;" src="/static/images/top_rigth_banner_{{top_right_banner_state}}.png" alt="Banner state{{top_right_banner_st\
ate}}">
%end

			</div>
			<div class="clear"></div>
%# Only show the menu if we want.
%if print_menu:
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
%# End of the menu
%end
			<div id="main_container" class="grid_16">
