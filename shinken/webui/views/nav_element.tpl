%if 'app' not in locals(): app = None

<script type="text/javascript">
var myMenu = new UvumiDropdown("dropdown-menu",{
closeDelay:12000
});
</script>

<div class="grid_16">
	<ul id="dropdown-menu" class="dropdown">
	
	%menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All'), ('/system', 'System') ]
	%for (key, value) in menu:
	
		    %# Check for the selected element, if there is one
			%if menu_part == key:
				<li><a href="{{key}}" id="selected">{{value}}</a></li>
				%else:
					<li><a href="{{key}}">{{value}}</a></li>
				%end
			%end
		<li class="menu_right">
		<a href="tools.html">{{user.get_name()}}!</a>
		<!-- New UL starts here -->
		<ul>
			<li>
				<a href="tools1.html">d</a>
			</li>
		</ul>
		<!-- New UL finished here -->
		
		</li>

	</ul>
</div>
<div class="clear"></div>
