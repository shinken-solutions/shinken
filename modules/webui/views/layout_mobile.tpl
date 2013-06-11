<!DOCTYPE html>
%#Set default values
%if not 'title' in locals(): title = 'No title'
%if not 'js' in locals(): js = []
%if not 'css' in locals(): css = []
%if not 'print_menu' in locals(): print_menu = True
%if not 'print_header' in locals(): print_header = True
%if not 'refresh' in locals(): refresh = False
%if not 'user' in locals(): user = None
%if not 'app' in locals(): app = None
%if not 'menu_part' in locals(): menu_part = ''
%if not 'back_hide' in locals(): back_hide = False

%print "APP is", app
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{title or 'No title'}}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <link rel="stylesheet" href="/static/css/jquery.mobile-1.1.0.min.css" />
    <link rel="stylesheet" href="/static/css/shinken-mobile.min.css" />
    <script src="/static/js/jquery-1.6.4.min.js"></script>
    <script src="/static/js/jquery.mobile-1.1.0.min.js"></script>
  </head>

<body>
 	%include header_element_mobile globals()
  <div data-role="content">
    %include
  </div>

  	%include footer_element_mobile globals()

  </body>
  	<script type="text/javascript" >
		$('[data-role=page]').live('swipeleft', function(event) {
			$.mobile.changePage($('#right_link').attr('href'));
		});

		$('[data-role=page]').live('swiperight', function(event) {
			$.mobile.changePage($('#left_link').attr('href'), {transition:'slide', reverse:true});
		});
	</script>
</html>
