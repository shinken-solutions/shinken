<!DOCTYPE html>

%#Set default values
%if not 'js' in locals() : js = []
%if not 'title' in locals() : title = 'No title'
%if not 'css' in locals() : css = []
%if not 'print_menu' in locals() : print_menu = True
%if not 'print_header' in locals() : print_header = True
%if not 'refresh' in locals() : refresh = False
%if not 'user' in locals() : user = None
%if not 'app' in locals() : app = None

%# If not need, disable the top right banner
%if not 'top_right_banner_state' in locals() : top_right_banner_state = 0

%# For the menu selection
%if not 'menu_part' in locals() : menu_part = ''


<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

      <title>{{title or 'No title'}}</title>
      
      <link rel="stylesheet" type="text/css" href="/static/css/navigation.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/reset.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/text.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/grid.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/layout.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/message.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/multibox.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/pulse.css" media="screen"/>
      <link rel="stylesheet" type="text/css" href="/static/css/autocompleter.css" media="screen"/>

      %if user is not None:
        <link rel="stylesheet" type="text/css" href="/static/css/userinfo.css" media="screen"/>
      %end

      %# And now for css files
      %for p in css:
		<link rel="stylesheet" type="text/css" href="/static/{{p}}">
      %end

      <script type="text/javascript" src="/static/js/mootools.js"></script>
      <script type="text/javascript" src="/static/js/mootools-more.js"></script>
      <script type="text/javascript" src="/static/js/mootools-message.js"></script>
      
      <script type="text/javascript" src="/static/js/simpletreemenu.js"></script>
      <script type="text/javascript" src="/static/js/rotater.js"></script>
      <script type="text/javascript" src="/static/js/tabs.js"></script>
      <script type="text/javascript" src="/static/js/top_right_banner.js"></script>
      <script type="text/javascript" src="/static/js/floatingtips.js"></script>
      <script type="text/javascript" src="/static/js/tip.js"></script>
      <script type="text/javascript" src="/static/js/action.js"></script>
      <script type="text/javascript" src="/static/js/opacity.js"></script>
      <script type="text/javascript" src="/static/js/multibox.js"></script>
      <script type="text/javascript" src="/static/js/deptree.js"></script>
      
      %# Auto completer part
      <script type="text/javascript" src="/static/js/autocompleter.js"></script>
      <script type="text/javascript" src="/static/js/autocompleter.Request.js"></script>
      <script type="text/javascript" src="/static/js/autocompleterObserver.js"></script>

      %if user is not None and print_header:
        <script type="text/javascript" src="/static/js/userinfo.js"></script>
      %end

      %if refresh:
		<script type="text/javascript" src="/static/js/reload.js"></script>
      %end

      %# End of classic js import. Now call for specific ones
      %for p in js:
		<script type="text/javascript" src="/static/{{p}}"></script>
      %end


    </head>
    
	<body class="main">

    %if user is not None:
    <!-- Userinfo -->
	<div id="userinfo">
    	<div class="userinfoContent">
	  <img src='/static/images/cut_honeycomb.png' alt="" style="width:200px; height:108px;position: absolute;top: 0;left: 0px;border: 0;">
	  <div class="left"> <img style="width:60px; height:80px;" src='/static/photos/{{user.get_name()}}' alt=""> </div>
	  <div>
	    <p>Name : {{user.get_name()}}</p>
	    <p>Email : {{user.email}}</p>
	  </div>
	  
	  <div class="userinfoClose"> <a href="#" id="closeUserinfo"><img style="width: 16px;height: 16px;" src="/static/images/disabled.png" alt="" title="">Close</a> </div>
      	</div>
      <!-- /userinfo -->

    </div>
    %# " End of the userinfo panel "
    %end

	<div class="container_16">
		%if print_header:
			%include header_element globals()
		%end
		%if print_menu:
			%include navigation_element globals()
		%end
		<div id="main_container" class="grid_16">
			%include
		</div>
		<div class="clear"></div>
			%include footer_element
	</div>
	</body>
</html>
