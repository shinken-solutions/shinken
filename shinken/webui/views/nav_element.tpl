<div id="nav" class="grid_16">
  <div style="float:left;">
			  <ul>
			    %menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All'), ('/system', 'System') ]
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
  <div style="float:right;">
    
  </div>



</div>
<div class="clear"></div>
