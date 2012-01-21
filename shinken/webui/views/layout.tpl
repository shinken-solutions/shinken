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
      
		<link type="text/css" href="/static/css/custom-theme/jquery-ui-1.8.16.custom.css" rel="stylesheet" />
		<link href="/static/css/grid.css" rel="stylesheet">
		<link href="/static/bootstrap/bootstrap.css" rel="stylesheet">

	    %if user is not None:
	    <link rel="stylesheet" type="text/css" href="/static/css/userinfo.css" media="screen"/>
	    %end

      %# And now for css files
      %for p in css:
		<link rel="stylesheet" type="text/css" href="/static/{{p}}">
      %end
  
	<script type="text/javascript" src="/staticjs/jquery-1.6.2.min.js"></script>
    <script type="text/javascript" src="/staticjs/jquery-ui-1.8.16.custom.min.js"></script>
      
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