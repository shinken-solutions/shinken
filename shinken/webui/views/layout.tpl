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
    <title>Bootstrap, from Twitter</title>

    <!-- Le HTML5 shim, for IE6-8 support of HTML elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->

    <!-- Le styles -->
    <link href="/static/css/bootstrap.css" rel="stylesheet">
    <style type="text/css">
      body {
        padding-top: 60px;
        padding-bottom: 40px;
      }
      .sidebar-nav {
        padding: 9px 0;
      }
    </style>
    <link href="/static/css/bootstrap-responsive.css" rel="stylesheet">

    <!-- Le fav and touch icons -->
    <link rel="shortcut icon" href="images/favicon.ico">
    <link rel="apple-touch-icon" href="images/apple-touch-icon.png">
    <link rel="apple-touch-icon" sizes="72x72" href="images/apple-touch-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="114x114" href="images/apple-touch-icon-114x114.png">
  </head>

<body>

	%if print_header:
		%include header_element globals()
	%end

    <div class="container-fluid">
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
    <script src="../assets/js/tests/vendor/jquery.js"></script>
    <script src="../assets/js/bootstrap-transition.js"></script>
    <script src="../assets/js/bootstrap-collapse.js"></script>

  </body>
</html>