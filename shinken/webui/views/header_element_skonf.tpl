%if 'app' not in locals(): app = None

<div id="header" class="grid_16">
	%if user is not None:
    <div id="top">
	<!-- userinfo -->
		<ul class="userinfo">
	  		<li class="left">&nbsp;</li>
	 		 <li>Hello {{user}}!</li>
	 		 <li>|</li>
	 		 <li><a id="toggleUserinfo" href="#">Parameters</a></li>
	 		 <li>|</li>
	 		 <li><a href="/user/logout">Log out</a></li>
		</ul>
	<!-- / userinfo -->
    </div> 
    <!-- / top -->
    %# " End of the userinfo activator "
    %end
    
	<h1 class="box_textshadow">Shinken</h1>


    %# Set the Top right banner if need
    %if top_right_banner_state != 0:
	<div id="animate-area-back-1">
		<div id="animate-area-back-2">
			<div id="animate-area" style="background-image:url(/static/images/sky_{{top_right_banner_state}}.png);">
	  	    	<a href='/impacts'> <img class="top_right_banner" style="position: absolute;top: 0;right: 0;border: 0;" src="/static/images/top_rigth_banner_{{top_right_banner_state}}.png" alt="Banner state{{top_right_banner_state}}" id="top_right_banner"> </a>
	  	    </div>
		</div>
	</div>
    %end 
</div>

<div class="clear"></div>
