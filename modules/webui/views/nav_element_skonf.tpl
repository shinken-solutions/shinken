%if not 'app' in locals(): app = None

<script type="text/javascript">
var myMenu = new UvumiDropdown("dropdown-menu",{
closeDelay:12000
});
</script>

<div id="navigation" class="grid_16">
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
		<a href="/user">User</a>
		<!-- New UL starts here -->
		<ul>
			<div>
				<img style="width:20px; height:20px; padding:10px 0 0 10px;" src='/static/photos/{{user}}'>
				<span>{{user}}</span>
				<hr/>
				<li><a href="/user/logout">Log out</a></li>
			</div>
		</ul>
		<!-- New UL finished here -->

		</li>

	</ul>
</div>
<div class="clear"></div>
