%helper = app.helper
%datamgr = app.datamgr

%rebase layout js=['impacts/js/impacts.js', 'impacts/js/multi.js'], title='All critical impacts for your business', css=['impacts/css/impacts.css'], refresh=True, menu_part = '/impacts', user=user

%# " If the auth succeed, we go in the /problems page "
%if not valid_user:
	<script type="text/javascript">
		window.location.replace("/login");
	</script>
%# " And if the javascript is not follow? not a problem, we gave no data here."
%end

<div id="impact-container">

	<div class="impacts-panel">

		%# " We look for separate bad and good elements, so we remember last state"
		%last_was_bad = False
		%# " By default we won't expand an impact."
		<script type="text/javascript">
		  var  impact_to_expand = -1;
		</script>
		%for imp_id in impacts:
		%   impact = impacts[imp_id]
	
	  	%# "When we swtich, add a HR to really separate things"
	  	%if impact.state_id == 0 and last_was_bad and imp_id != 1:
	    	<hr>
	    	%last_was_bad = False
	  	%end
	  	%if impact.state_id != 0:
	    	%last_was_bad = True
	  	%end
	
	  	%if imp_id == 1 and impact.state_id != 0:
		    <script type="text/javascript">
		    	impact_to_expand = {{imp_id}};
		    </script>
	  	%end
	  	
	    <div class="impact pblink" id="{{imp_id}}">
			<div class="show-problem" id="show-problem-{{imp_id}}">
				<img src="static/images/trig_right.png" id="show-problem-img-{{imp_id}}">
			</div>
			
		%for i in range(2, impact.business_impact):
			<div class="criticity-icon-{{i-1}}">
				<img src="static/images/star.png">
			</div>
		%end
	
		%#	<div class="impact-icon"><img src="static/images/50x50.png"></div>
			<div class="impact-icon"><img style="width: 64px;height: 64px;" src="{{helper.get_icon_state(impact)}}"></div>
			<div class="impact-rows">
				<div class="impact-row">
					<span class="impact-name">{{impact.get_name()}}</span> is <span class="impact-state-text">{{impact.state}}</span>
				</div>
				<div class="impact-row">
					<span class="impact-duration">since {{helper.print_duration(impact.last_state_change, just_duration=True, x_elts=2)}}</span>
				</div>
			</div>
		</div>
		%# end of the for imp_id in impacts:
		%end

	</div>
      
	<div class="right-panel">
		<a href="/3dimpacts" class="mb" title="Show impacts in 3D mode.">{{!helper.get_button('Show impacts in 3d', img='/static/images/state_ok.png')}}</a>
	</div> 


      

%# "#######    Now we will output righ panel with all root problems"
	<div class="problems-panels">

		%# Iinit pb_id
		%pb_id = 0
	
		%for imp_id in impacts:
		%impact = impacts[imp_id]
	
	    <div class="problems-panel" id="problems-{{imp_id}}" style="visibility: hidden; zoom: 1; opacity: 0; ">
		<div class="right-panel-top"> 
			<div class="pblink" id="{{imp_id}}"> <img style="width: 16px;height: 16px;" src='/static/images/disabled.png'> Close </div>
		</div>
		
		<br style="clear: both">
	
		<!--<div class="impact-icon-big"><img style="width: 80px;height: 80px;" src="{{helper.get_icon_state(impact)}}"> </div>-->
		%for i in range(2, impact.business_impact):
			<div class="criticity-inpb-icon-{{i-1}}">
		    	<img src="static/images/star.png">
		    </div>
		%end
		<h2 class="state_{{impact.state.lower()}}"><img style="width : 64px; height:64px" src="{{helper.get_icon_state(impact)}}" />{{impact.state}}: {{impact.get_full_name()}}</h2>
		<!--<center>
			<div class="impact-row"><span class="impact-inpb-name">{{impact.get_full_name()}}</span> is <span class="impact-state-text">{{impact.state}}</span></div>
		</center>-->
	
		<div style="float:right;">
			<a href="{{!helper.get_link_dest(impact)}}">{{!helper.get_button('Go to details', img='/static/images/search.png')}}</a>
		    <a href="/depgraph/{{impact.get_full_name()}}" class="mb" title="Impact map of {{impact.get_full_name()}}">{{!helper.get_button('Show impact map', img='/static/images/state_ok.png')}}</a>
		</div>
	
		%##### OK, we print root problem NON ack first
	
		<br style="clear: both">
		
		%l_pb_id = 0
		%unack_pbs = [pb for pb in impact.source_problems if not pb.problem_has_been_acknowledged]
		%ack_pbs = [pb for pb in impact.source_problems if pb.problem_has_been_acknowledged]
		%nb_unack_pbs = len(unack_pbs)
		%nb_ack_pbs = len(ack_pbs)
		%if nb_unack_pbs > 0:
			Root problems unacknowledged :
		%end
	
		%guessed = []
		%if impact.state_id != 0 and len(unack_pbs+ack_pbs) == 0:
			%guessed = datamgr.guess_root_problems(impact)
		%end
	
		%for pb in unack_pbs+ack_pbs+guessed:
		%   pb_id += 1
		% l_pb_id += 1
		  
		%if nb_ack_pbs != 0 and l_pb_id == nb_unack_pbs + 1:
			Acknowledged problems:
		%end
	
		%if len(guessed) != 0 and l_pb_id == nb_unack_pbs + nb_ack_pbs + 1:
		Pure guessed root problems :
		%end
	
		<div class="problem" id="{{pb_id}}">
			<div class="divhstate1"> <img style="width: 32px;height: 32px;" src="{{helper.get_icon_state(pb)}}"> {{!helper.get_link(pb)}} is {{pb.state}} since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</div>
		    <div class="problem-actions opacity_hover">
		    	<div class="action-fixit"><a href="#" onclick="try_to_fix('{{pb.get_full_name()}}')"> <img class="icon" title="Try to fix it" src="static/images/icon_ack.gif">Try to fix it</a></div>
		    	%if not pb.problem_has_been_acknowledged:
		    		<div class="action-ack"><a href="#" onclick="acknowledge('{{pb.get_full_name()}}')"><img class="icon" title="Acknowledge it" src="static/images/link_processes.gif">Acknowledge it</a></div>
		      	%end
		    </div>
		</div>
		%# end for pb in impact.source_problems:
		%end
	
		%if len(impact.parent_dependencies) > 0:
			<a id="togglelink-{{impact.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{impact.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
			<div class="clear"></div>
		  	{{!helper.print_business_rules(datamgr.get_business_parents(impact))}}
		%end  
	</div>
	%# end for imp_id in impacts:
	%end
   </div>
</div>
