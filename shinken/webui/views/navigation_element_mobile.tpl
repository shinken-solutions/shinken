%if not 'app' in locals(): app = None
<div id="navigation">
	<ul id="menu" class="grid_12">
		%menu = [ ('/', 'Home'), ('/mobile/impacts','Impacts'), ('/mobile/problems','IT problems')]
	    	%for (key, value) in menu:
	        %# Check for the selected element, if there is one
		        %if menu_part == key:
				 	<li><a href="{{key}}" id="selected">{{value}}</a></li>
			     %else:
			        <li><a href="{{key}}">{{value}}</a></li>
			    %end
	        %end
	</ul>
<!--
<ul id="dropmenu" class="grid_4 right">
    <li class="menu_right"><a href="#" class="drop">Impacts <span class="tac_impacts">1 / 2 /3</span></a><!-- Begin 3 columns Item -->
        <div class="dropdown_3columns align_right"><!-- Begin 3 columns container -->
            <div class="grid_16">
				<h3>Host Overview</h3>
				<ul class="grid_16 tac_">
					<li class="grid_2"><span>0</span>Up</li>
					<li class="grid_3"><span>0</span>Porblems</li>
					<li class="grid_3"><span>0</span>Down</li>
					<li class="grid_3"><span>0</span>Pending</li>
					<li class="grid_3"><span>0</span>Unreachable</li>
					<li class="grid_2"><span>0</span>Sum</li>
				</ul>
            </div>
			<div>
				<h3>Service Overview</h3>
				<ul class="grid_16 tac_">
					<li class="grid_2"><span>0</span>Up</li>
					<li class="grid_3"><span>0</span>Porblems</li>
					<li class="grid_3"><span>0</span>Down</li>
					<li class="grid_3"><span>0</span>Pending</li>
					<li class="grid_3"><span>0</span>Unreachable</li>
					<li class="grid_2"><span>0</span>Sum</li>
				</ul>
            </div>
        </div><!-- End 3 columns container -->
    </li><!-- End 3 columns Item -->

</ul>
-->
</div>
<div class="clear"></div>
