%rebase layout_mobile globals(), title="IT problems", js=['mobile/js/mobile_main.js', 'mobile/js/mobile_problems.js'], css=['mobile/css/main.css', 'mobile/css/problems.css']

%helper = app.helper
%datamgr = app.datamgr

%if navi is not None:
<div data-role="navbar">
	<ul>
	%for name, start, end, is_current in navi:
	%if is_current:
		<li class="ui-btn-active"><a href="#">{{name}}</a></li>
	%elif start == None or end == None:

	%else:
		<li><a href='/mobile{{menu_part}}?start={{start}}&end={{end}}'>{{name}}</a></li>
	%end
	%end
	</ul>
</div>
%# end of the navi part
%end

<div data-role="collapsible-set" data-iconpos="right">
  %for pb in problems:
    <div data-role="collapsible" data-collapsed="true" data-content-theme="a" data-theme="a" >
      <h2 class="state_{{pb.state.lower()}}">
      %for j in range(2, pb.business_impact):
	<img src="/static/images/star.png">
      %end

	<img style="width : 20px; height:20px" src="{{helper.get_icon_state(pb)}}" />
	{{pb.state}}: {{pb.get_full_name()}}
      </h2>

	<p>
	<div class='detail' id="{{app.helper.get_html_id(pb)}}">
     <p><strong>Output: </strong>
       %if app.allow_html_output:
       {{!helper.strip_html_output(pb.output)}}
       %else:
       {{pb.output}}
       %end
     </p>

     <p><strong>Since: </strong> {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</p>
     <p><strong>Last check: </strong> {{helper.print_duration(pb.last_chk, just_duration=True, x_elts=2)}} ago</p>
     <p><strong>Next check: </strong> in {{helper.print_duration(pb.next_chk, just_duration=True, x_elts=2)}}</p>
    %if len([imp for imp in pb.impacts if imp.business_impact > 2]) > 0:
     <h4>Important impacts</h4>
      <div class="impacts">
	%for imp in [imp for imp in pb.impacts if imp.business_impact > 2]:
	<div class="impact">
	  <p>
	    <img class="impact_img" src="{{helper.get_icon_state(imp)}}" style="width : 16px; height:16px"/> {{imp.get_full_name()}} is {{imp.state}} since {{helper.print_duration(imp.last_state_change, just_duration=True, x_elts=2)}}
	  </p>
	</div>
	%end
      </div>
    %end
   </div>
	<a href="/mobile{{!helper.get_link_dest(pb)}}" rel="external" data-role="button" data-icon="search" >More Infos</a>
	</div>

   %end

</div>





