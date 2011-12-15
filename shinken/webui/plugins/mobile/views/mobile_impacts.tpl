
%helper = app.helper
%datamgr = app.datamgr

%rebase layout globals(), title="Tactical view", js=['mobile/js/mobile_main.js', 'mobile/js/mobile_impacts.js'], css=['mobile/css/main.css', 'mobile/css/impacts.css']

<div id="all">
<div> <h1> Shinken business apps</h1> </div>

<h2>End users apps</h2>



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
