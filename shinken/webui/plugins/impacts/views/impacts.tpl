
%helper = app.helper

%include header js=['impacts/js/impacts.js'], title='All critical impacts for your business', css=['impacts/impacts.css']




    <div class="whole-page">
      
      
      

      <div class="impacts-panel" style="min-height: 983px; ">

%# " We look for separate bad and good elements, so we remember last state"
%last_was_bad = False
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

	<div class="impact pblink" id="{{imp_id}}">
	  <div class="show-problem" id="show-problem-{{imp_id}}">
	    <img src="static/images/trig_right.png" id="show-problem-img-{{imp_id}}">
	  </div>
	  %for i in range(2, impact.business_impact):
	    <div class="criticity-icon-{{i-1}}">
	      <img src="static/images/star.png">
	    </div>
	  %end

	    
	  <div class="impact-icon"><img src="static/images/50x50.png"></div>
	  <div class="impact-status-icon"><img src="static/images/{{impact.state.lower()}}_medium.png"></div>
	  <div class="impact-rows">
	    <div class="impact-row"><span class="impact-name">{{impact.get_name()}}</span> is <span class="impact-state-text">{{impact.state}}</span>

	    </div>
	    <div class="impact-row"><span class="impact-duration">since {{helper.print_duration(impact.last_state_change, just_duration=True, x_elts=2)}}</span></div>
	  </div>
	</div>
%# end of the for imp_id in impacts:
%end

      </div>
      
      <div class="right-panel"></div>


      

%# "#######    Now we will output righ panel with all root problems"
      <div class="problems-panels">


%# Iinit pb_id
%pb_id = 0

%for imp_id in impacts:
%   impact = impacts[imp_id]


	<div class="problems-panel" id="problems-{{imp_id}}" style="visibility: hidden; zoom: 1; opacity: 0; ">
	  <div class="right-panel-top"> 

	    <div class="pblink" id="{{imp_id}}"> Close </div>
	  </div><br style="clear: both">

	  <div class="impact-icon-big"><img src="static/images/80x80.png">
	  </div>
	  %for i in range(2, impact.business_impact):
	    <div class="criticity-inpb-icon-{{i-1}}">
	      <img src="static/images/star.png">
	    </div>
	  %end


	  <center>
	    <div class="impact-row"><span class="impact-inpb-name">{{impact.get_full_name()}}</span> is <span class="impact-state-text">{{impact.state}}</span>
	    </div>
	  </center>

	  %##### OK, we print root problem NON ack first

	  <br style="clear: both">
	  %unack_pbs = [pb for pb in impact.source_problems if not pb.problem_has_been_acknowledged]
	  %ack_pbs = [pb for pb in impact.source_problems if pb.problem_has_been_acknowledged]
	  %nb_unack_pbs = len(unack_pbs)
	  %if len(unack_pbs+ack_pbs) > 0:
	  Root problems :
	  %end
	  %for pb in unack_pbs+ack_pbs:
	  %   pb_id += 1
	  <div class="problem" id="{{pb_id}}">
	    <div class="divhstate1">{{!helper.get_link(pb)}} is {{pb.state}} since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</div>
	    <div class="problem-actions opacity_hover">
	      <div class="action-fixit"><a href="#" onclick="try_to_fix('{{pb.get_full_name()}}')"> <img class="icon" title="Try to fix it" src="static/images/icon_ack.gif">Try to fix it</a></div>
	      %if not pb.problem_has_been_acknowledged:
	      <div class="action-ack"><a href="#" onclick="acknoledge('{{pb.get_full_name()}}')"><img class="icon" title="Acknoledge it" src="static/images/link_processes.gif">Acknoledge it</a></div>
	      %end
	    </div>
	  </div>
	  %# end for pb in impact.source_problems:
	  %end
	  
	  
	</div>
%# end for imp_id in impacts:
%end




      </div>
    </div>
    
    <table class="footer"><tbody><tr><td class="left"></td><td class="middle"></td><td class="right"></td></tr></tbody>
    </table>

%include footer
    
