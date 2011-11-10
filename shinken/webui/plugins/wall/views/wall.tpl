%#<!DOCTYPE html>
%#<html>
%#<head>

<!--
    Copyright (C) 2009 Charles Ying. All Rights Reserved.
    This source code is available under Apache License 2.0.
-->
%rebase layout css=['wall/css/snowstack.css', 'wall/css/wall.css'], title='Wall view', js=['wall/js/snowstack.js', 'wall/js/wall.js'], refresh=True, user=user, print_menu=False, print_header=True


%#<title>Snow Stack - WebKit 3D CSS Visual Effects</title>
%#<meta name="Description" content="Snow Stack is a demo of WebKit CSS 3D visual effects with latest WebKit nightly on Mac OS X Snow Leopard" />

%#<link rel="stylesheet" type="text/css" href="/static/wall/css/snowstack.css">
%#<link rel="stylesheet" type="text/css" href="/static/wall/css/wall.css">

<style type="text/css">

body
{
	font-family: 'Helvetica Neue Light', 'HelveticaNeue-Light', sans-serif;
	margin: 0;
	padding: 0;
}

#caption
{
	position: absolute;
	bottom: 0; right: 0; left: 0;
	font-size: 15pt;
	text-overflow: ellipsis; overflow: hidden; white-space: nowrap;
	padding: 10pt 10pt 10pt 20pt;
	-webkit-transform: translate3d(0, 0, 2000px);
	background-color: rgba(0, 0, 0, 0.5);
	-webkit-transition-property: opacity;
	-webkit-transition-duration: 550ms;
}

#caption.hide
{
    opacity: 0;
}

</style>

%#</head>

%#<body>

<div class="page view">
    <div class="origin view">
        <div id="camera" class="camera view"></div>
    </div>
</div>

<div id="caption" class="caption">
	snow stack / webkit css visual effects demo &mdash; arrow keys to move, space toggles magnify
</div>

%#<script type="text/javascript" src="/static/wall/js/snowstack.js"></script>
%#<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
%#<script type="text/javascript" src="/static/js/mootools.js"></script>
%#<script type="text/javascript" src="/static/js/mootools-more.js"></script>

<script type="text/javascript">

var page = 1;

function flickr(callback)
{
    var url = "http://api.flickr.com/services/rest/?method=flickr.interestingness.getList&api_key=60746a125b4a901f2dbb6fc902d9a716&per_page=21&extras=url_o,url_m,url_s,owner_name&page=" + page + "&format=json&jsoncallback=?";
    
	jQuery.getJSON(url, function(data) 
	{
        var images = jQuery.map(data.photos.photo, function (item)
        {
            /* return item.url_s; */
            return {
                title: item.ownername + " / " + item.title,
            	thumb: item.url_s,
            	zoom: 'http://farm' + item.farm + '.static.flickr.com/' + item.server + '/' + item.id + '_' + item.secret + '.jpg',
            	link: 'http://www.flickr.com/photos/' + item.owner + '/' + item.id
            };
        });

        callback(images);
        page = page + 1;
    });
}

function init_pageimages(options)
{
	var imgs = document.querySelectorAll("a>img");
	var images = [];

	for (var i = 0; i < imgs.length; i++)
	{
		var img = imgs[i];
		var title = img.alt || img.title || img.parentNode.title;
		var thumb = img.src;
		var link = img.parentNode.href;
		var zoom = img.src;
		
		images.push({ title: title, thumb: thumb, link: link, zoom: zoom });
	}

	snowstack_init(images, options);
}


/*var images = [
   { "title": "My Image 1", "thumb": "/static/images/state_down.png", "zoom": "/static/images/state_down.png", "link": "http://www.satine.org/"},
	{ "title": "My Image 2", "thumb": "/static/images/state_up.png", "zoom": "/static/images/state_up.png", "link": "http://www.satine.org/" },
   { "title": "My Image 3", "thumb": "/static/images/state_flapping.png", "zoom": "/static/images/state_flapping.png"}
];*/

var images = {{!impacts}};

</script>


%#</body>

%#</html>
