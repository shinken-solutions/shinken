
%helper = app.helper
%datamgr = app.datamgr

%rebase layout_mobile globals(), title="Tactical view", js=['mobile/js/mobile_main.js', 'mobile/js/mobile_impacts.js'], css=['mobile/css/main.css', 'mobile/css/impacts.css']

<div>
<div> <h1> End users apps</h1> </div>


<a href="#" onclick="go_left();"><img src="/static/images/previous.png"/></a>
<a href="#" onclick="go_right();"><img src="/static/images/next.png"/></a>
<br/>
%i = 0

<div class="impacts">
  %for impact in impacts:
    <div class="impact" id="impact-{{i}}" style="left:{{i*250}}px;">
      %for j in range(2, impact.business_impact):
      <div class="criticity-inpb-icon-{{j-1}}">
	<img src="/static/images/star.png">
      </div>
      %end
      <h2 class="state_{{impact.state.lower()}}"><img style="width : 64px; height:64px" src="{{helper.get_icon_state(impact)}}" />{{impact.state}}: {{impact.get_full_name()}}</h2>
		
   
    %if len(impact.source_problems) > 0:
      <h3>Root problems</h3>
      <div class="root_problems">
	%for pb in impact.source_problems:
	<div class="root_problem">
	  <p><img class="root_problem_img" src="{{helper.get_icon_state(pb)}}" /> {{pb.get_full_name()}} is {{pb.state}} since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}
	  %if pb.problem_has_been_acknowledged:
	    ACK : <img class="ack" src="/static/images/big_ack.png">
	  %else:
	    ACK : <img class="ack" src="/static/images/critical_medium.png">
	  %end
	  </p>
	  <p>It's managed by:</p>
	  <ul>
	    %for c in pb.contacts:
	    <li><img src="/static/photos/{{c.get_name()}}" class="admin-photo" /> {{c.get_name()}} : <a href="tel:{{c.pager}}">{{c.pager}}</a> <a href="mailto:{{c.email}}">{{c.email}}</a>
	    </li>
	    %end
	  </ul>
	</div>
	%end
      </div>
    %end

    <h3>Root problem analysis</h3>
    %if len(impact.parent_dependencies) > 0:
      <a id="togglelink-{{impact.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{impact.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
      <div class="clear"></div>
      {{!helper.print_business_rules(datamgr.get_business_parents(impact))}}
    %end  


    </div>
    %i += 1
  %end
</div>



</div>
