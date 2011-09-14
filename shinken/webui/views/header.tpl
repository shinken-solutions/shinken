<!DOCTYPE html>

%#Set default values
%if not 'js' in locals() : js = []
%if not 'title' in locals() : title = 'No title'
%if not 'css' in locals() : css = []
%if not 'print_menu' in locals() : print_menu = True
%if not 'print_header' in locals() : print_header = True
%if not 'refresh' in locals() : refresh = False
%if not 'user' in locals() : user = None

%# If not need, disable the top right banner
%if not 'top_right_banner_state' in locals() : top_right_banner_state = 0

%# For the menu selection
%if not 'menu_part' in locals() : menu_part = ''

<html slick-uniqueid="1"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>{{title or 'No title'}}</title>

    <link rel="stylesheet" type="text/css" href="/static/css/nav.css">
    <link rel="stylesheet" type="text/css" href="/static/css/reset.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/css/text.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/css/grid.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/ccs/layout.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/message.css" media="screen">
    <link rel="stylesheet" type="text/css" href="/static/multibox.css" media="screen">

    %if user is not None:
    <link rel="stylesheet" type="text/css" href="/static/userinfo.css" media="screen">
    %end

    <script type="text/javascript" src="/static/js/mootools.js"></script>
    <script type="text/javascript" src="/static/js/mootools-more.js"></script>
    <script type="text/javascript" src="/static/js/mootools-message.js"></script>

    <script type="text/javascript" src="/static/js/rotater.js"></script>
    <script type="text/javascript" src="/static/js/tabs.js"></script>
    <script type="text/javascript" src="/static/js/top_right_banner.js"></script>
    <script type="text/javascript" src="/static/js/floatingtips.js"></script>
    <script type="text/javascript" src="/static/js/tip.js"></script>
    <script type="text/javascript" src="/static/js/action.js"></script>
    <script type="text/javascript" src="/static/js/opacity.js"></script>
    <script type="text/javascript" src="/static/js/multibox.js"></script>

    %if user is not None:
    <script type="text/javascript" src="/static/js/userinfo.js"></script>
    %end

    %if refresh:
    <script type="text/javascript" src="/static/js/reload.js"></script>
    %end
    


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

    %if user is not None:
    <!-- Userinfo -->
    <div id="userinfo">
      <div class="userinfoContent">
	
	<div class="left"><img style="width:60px; height:80px;" src='/static/photos/{{user.get_name()}}'>
	</div>
	<div>
	  <p>Name : {{user.get_name()}}</p>
	  <p>Email : {{user.email}}</p>
        </div>



	<div class="userinfoClose"><a href="#" id="closeUserinfo"><img style="width: 16px;height: 16px;" src="/static/images/disabled.png" title="">Close</a></div>
      </div> <!-- /userinfo -->

      <div class="clearfix"></div>
    </div>
    %# " End of the userinfo panel "
    %end

		<div class="container_16">
%if print_header:
			<!-- Header START -->
			<div id="header" class="grid_16">
			  

    %if user is not None:
      <div id="top">
	<!-- userinfo -->
	<ul class="userinfo">
	  <li class="left">&nbsp;</li>
	  <li>Hello {{user.get_name()}}!</li>
	  <li>|</li>
	  <li><a id="toggleUserinfo" href="#">Parameters</a></li>
	</ul> <!-- / userinfo -->
      </div><!-- / top -->
    %# " End of the userinfo activator "
    %end

				<h1 class="box_textshadow">Shinken</h1>
			%# Set the Top right banner if need
				%if top_right_banner_state != 0:
					<div id="animate-area-back-1">
						<div id="animate-area-back-2">
							<div id="animate-area" style="background-image:url(/static/images/sky_{{top_right_banner_state}}.png);">
  								<a href='/impacts'><img class="top_right_banner" style="position: absolute;top: 0;right: 0;border: 0;" src="/static/images/top_rigth_banner_{{top_right_banner_state}}.png" alt="Banner state{{top_right_banner_state}}" id="top_right_banner"></a>
							</div>
						</div>
					</div>
				%end
			</div>
			<!-- Header END -->
%end
			<div class="clear"></div>
%# " Only show the menu if we want. "
%if print_menu:			
			<div id="nav" class="grid_16">
			  <ul>
			    %menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/system', 'System') ]
			    %for (key, value) in menu:
			      %# Check for the selected element, if there is one
			      %if menu_part == key:
			        <li><a href="{{key}}" id="selected">{{value}}</a></li>
			      %else:
			        <li><a href="{{key}}">{{value}}</a></li>
			      %end
			    %end
			  </ul>
			</div>
			<div class="clear"></div>
%# End of the menu
%end
			<div id="main_container" class="grid_16">
