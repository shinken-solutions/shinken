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

<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{title or 'No title'}}</title>

    <!-- Le HTML5 shim, for IE6-8 support of HTML elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->

    <!-- Le styles -->
    <link href="/static/css/bootstrap.css" rel="stylesheet">
    <link href="/static/css/custom/layout.css" rel="stylesheet">
    <link href="/static/css/custom/badger.css" rel="stylesheet">
    <link href="/static/css/elements/jquery.meow.css" rel="stylesheet">

    %# And now for css files
      %for p in css:
    <link rel="stylesheet" type="text/css" href="/static/{{p}}">
      %end
    
    <style type="text/css">
      body {
        padding-top: 60px;
        padding-bottom: 40px;
      }
      .sidebar-nav {
        padding: 9px 0;
      }
    </style>

  </head>

<body>

	%if print_header:
		%include header_element globals()
	%end

    <div class="container-fluid no-leftpadding">
      <div class="row-fluid">
        <div class="span2">
			%if print_menu:
				%include navigation_element globals()
			%end
        </div><!--/span-->
        <div class="span10">
			%include
        </div><!--/span-->
      </div><!--/row-->

      <hr>

		%include footer_element

    </div><!--/.fluid-container-->


    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="/static/js/jquery.js"></script>
    <script src="/static/js/jquery-ui-1.8.17.custom.min.js"></script>
    <script src="/static/js/shinkenui.js"></script>
    <script src="/static/js/bootstrap-collapse.js"></script>
    <script src="/static/js/bootstrap-tab.js"></script>
    <script src="/static/js/bootstrap-button.js"></script>
    <script src="/static/js/bootstrap-dropdown.js"></script>
    <script src="/static/js/bootstrap-tooltip.js"></script>
    <script src="/static/js/jquery.meow.js"></script>

    %# End of classic js import. Now call for specific ones
      %for p in js:
    <script type="text/javascript" src="/static/{{p}}"></script>
      %end

  </body>
</html>