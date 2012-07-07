%rebase layout_mobile globals(), title="Impacts View", js=['mobile/js/mobile_impacts.js'], css=['mobile/css/impacts.css'], menu_part='/impacts'

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
		<li><a href='/mobile/impacts?start={{start}}&end={{end}}'>{{name}}</a></li>
	%end
	%end
	</ul>
</div>
%# end of the navi part
%end

<div data-role="collapsible-set" data-iconpos="right" >


%i = 0

  %for impact in impacts:
     <div data-role="collapsible" data-content-theme="a" data-theme="a">
      <h2 class="state_{{impact.state.lower()}}">
      %for i in range(2, impact.business_impact):
	<img src="/static/images/star.png">
      %end
	<img style="width: 20px; height:20px" src="{{helper.get_icon_state(impact)}}" />
	{{impact.state}}: {{impact.get_full_name()}}
      </h2>

    %if len(impact.source_problems) > 0:
      <h3>Root problems</h3>
      <div class="root_problems">
	%for pb in impact.source_problems:
	<div class="root_problem">
	  <p><img class="root_problem_img" src="{{helper.get_icon_state(pb)}}" width="32px" /> {{pb.get_full_name()}} is {{pb.state}} since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}
	  %if pb.problem_has_been_acknowledged:
	    ACK: <img class="ack" style="width: 20px; height:20px" src="/static/images/big_ack.png">
	  %else:
	    ACK: <img class="ack" style="width: 20px; height:20px" src="/static/images/critical_medium.png">
	  %end
	  </p>
	  <p>It's managed by:</p>
	  <ul>
	    %for c in pb.contacts:
	    <li><img src="/static/photos/{{c.get_name()}}" class="admin-photo" width="32px" /> {{c.get_name()}}: <a href="tel:{{c.pager}}">{{c.pager}}</a> <a href="mailto:{{c.email}}">{{c.email}}</a>
	    </li>
	    %end
	  </ul>
	</div>
	%end
      </div>
    %end
	<div data-role="collapsible" data-content-theme="a" data-theme="a">
	    <h3>Root problem analysis</h3>
	    %if len(impact.parent_dependencies) > 0:
	      {{!helper.print_business_rules_mobile(datamgr.get_business_parents(impact))}}
	    %else:
	      No analysis avialable
	    %end
	</div>
    </div>
    %i += 1
  %end
</div>
