
%helper = app.helper
%datamgr = app.datamgr

%rebase layout_mobile globals(), title="IT problems", js=['mobile/js/mobile_main.js', 'mobile/js/mobile_problems.js'], css=['mobile/css/main.css', 'mobile/css/problems.css']

<div>

<h2>IT Problems</h2>



<div class="problems">
  %for pb in problems:
    <div class="problem">
      <h2 class="state_{{pb.state.lower()}}">
      %for j in range(2, pb.business_impact):
	<img src="/static/images/star.png">
      %end

	<img style="width : 20px; height:20px" src="{{helper.get_icon_state(pb)}}" />
	{{pb.state}}: {{pb.get_full_name()}}
	<a href="#" onclick="show_detail('{{pb.get_full_name()}}')"><img style="width : 20px; height:20px" src="/static/images/expand.png" /></a>
      </h2>
		
   <div class='detail' id="{{pb.get_full_name()}}">
     <p>Output : 
       %if app.allow_html_output:
       {{!helper.strip_html_output(pb.output)}}
       %else:
       {{pb.output}}
       %end
     </p>

     <p>Since : {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</p>
     <p>Last check : {{helper.print_duration(pb.last_chk, just_duration=True, x_elts=2)}} ago</p>
     <p>Next check : in {{helper.print_duration(pb.next_chk, just_duration=True, x_elts=2)}}</p>
    %if len([imp for imp in pb.impacts if imp.business_impact > 2]) > 0:
     <h4>Important impacts</h4>
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


    </div>
  %end
</div>



</div>
