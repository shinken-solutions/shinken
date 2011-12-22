
%helper = app.helper
%datamgr = app.datamgr

%rebase layout globals(), title="IT problems", js=['mobile/js/mobile_main.js'], css=['mobile/css/main.css', 'mobile/css/problems.css']

<div id="all">

<h2>IT Problems</h2>



<div class="problems">
  %for pb in problems:
    <div class="problem">
      <h2 class="state_{{pb.state.lower()}}">
      %for j in range(2, pb.business_impact):
	<img src="/static/images/star.png">
      %end

<img style="width : 20px; height:20px" src="{{helper.get_icon_state(pb)}}" />{{pb.state}}: {{pb.get_full_name()}}</h2>
		
   
    %if len([imp for imp in pb.impacts if imp.business_impact > 2]) > 0:
      <p>Important impacts</p>
      <div class="impacts">
	%for imp in [imp for imp in pb.impacts if imp.business_impact > 2]:
	<div class="impact">
	  <p>
	    <img class="impact_img" src="{{helper.get_icon_state(imp)}}" /> {{imp.get_full_name()}} is {{imp.state}} since {{helper.print_duration(imp.last_state_change, just_duration=True, x_elts=2)}}
	  </p>
	</div>
	%end
      </div>
    %end


    </div>
  %end
</div>



</div>
