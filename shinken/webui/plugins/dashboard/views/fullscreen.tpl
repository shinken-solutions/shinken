%helper = app.helper
%datamgr = app.datamgr

%rebase layout title='All problems', js=['dashboard/js/slideitmoo-1.1-mootools-1.3.js','dashboard/js/dashboard_functions.js'], css=['dashboard/css/fullscreen.css'], menu_part='/'+page, user=user, print_menu=False, print_header=False

%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>

%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end

<div id="fullscreen_info_outer">	
	<div id="fullscreen_info_inner">			
		<div id="fullscreen_info_items">
		    %# " We will print Business impact level of course"
		    %imp_level = 10
		
		    %# " We remember the last hname so see if we print or not the host for a 2nd service"
		    %last_hname = ''
		
		    %# " We try to make only importants things shown on same output "
		    %last_output = ''
		    %nb_same_output = 0

    		%for pb in pbs:
    			%if pb.business_impact != imp_level:
    
     				<div class="info_item">
     					<h2>{{!helper.get_business_impact_text(pb)}} </h2>
     					
					     <ul>
					     	<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
							<li class="grid_3"> <a class="box_round_small spezial_state_critical" href="#">delphi</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">router 1</a> </li>
							<li class="grid_3"> <a class="box_round_small" href="#">router lu</a> </li>
							<li class="grid_3"> <a class="box_round_small spezial_state_unreachable" href="#">backbone router</a> </li>
					     <ul>
     				</div>
       				
       				%# "We reset the last_hname so we won't overlap this feature across tables"
       				%last_hname = ''
       				%last_output = ''
       				%nb_same_output = 0
      			%end
      		%imp_level = pb.business_impact

	      		%# " We check for the same output and the same host. If we got more than 3 of same, make them opacity effect"
	      		%if pb.output == last_output and pb.host_name == last_hname:
	          		%nb_same_output += 1
	      		%else:
	          		%nb_same_output = 0
	      		%end
			      %last_output = pb.output
			%end
		</div>
	</div> 
</div>