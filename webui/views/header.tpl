

%#Set default values
%if not 'js' in locals() : js = []
%if not 'title' in locals() : title = 'No title'
%if not 'css' in locals() : css = []



 <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html slick-uniqueid="1"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>{{title or 'No title'}}</title>

    <link rel="stylesheet" type="text/css" href="static/nav.css">
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
