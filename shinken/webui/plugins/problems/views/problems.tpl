%import time
%start = time.time()

%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%include header title='All problems', top_right_banner_state=top_right_banner_state, js=['problems/js/accordion.js'], css=['problems/accordion.css'], refresh=True, menu_part='/problems', user=user


%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end


	 
<div id="left_container" class="grid_2">
  <div id="dummy_box" class="box_gradient_horizontal"> 
    <p>Dummy box</p>
  </div>
  <div id="nav_left">
    <ul>
      <li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Overview</a></li>
      <li><a href="http://unitedseed.de/tmp/Meatball/host_detail.html#">Detail</a></li>
    </ul>
  </div>
</div>

%# "We set the actions div that will be show/hide if we select elements"
<div class="actions" id="actions">
    <div style="float:right;">
      <a href="#" onclick="try_to_fix_all()">{{!helper.get_button('Fix all!', img='/static/images/enabled.png')}}</a>
    </div>
    <div style="float:right;">
      <a href="#" onclick="recheck_now_all()">{{!helper.get_button('Recheck all', img='/static/images/delay.gif')}}</a>
    </div>
    <div style="float:right;">
      <a href="#" onclick="acknoledge_all()">{{!helper.get_button('Acknoledge all', img='/static/images/wrench.png')}}</a>
    </div>

</div>

<div class="grid_13">
  <div id="accordion">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %# " We remember the last hname so see if we print or not the host for a 2nd service"
    %last_hname = ''
    %for pb in pbs:

      <div class="clear"></div>      
      %if pb.business_impact != imp_level:
       <h2> Business impact : {{!helper.get_business_impact_text(pb)}} </h2>
       %# "We reset teh last_hname so we won't overlap this feature across tables"
       %last_hname = ''
      %end
      %imp_level = pb.business_impact

	<div> 
	  <div style="margin-left: 20px; width: 70%; float:left;">
	    <table class="tableCriticity" style="width: 100%; margin-bottom:3px;">
	      <tr class="tabledesc">
	        <td class="tdBorderLeft tdCriticity" style="width:20px; background:none;"> <img src="/static/images/untick.png" /style="cursor:pointer;" onclick="add_remove_elements('{{pb.get_full_name()}}')" id="selector-{{pb.get_full_name()}}" > </td>
	        <td class="tdBorderLeft tdCriticity" style="width:20px;"> <img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(pb)}}" /> </td>
		%if pb.host_name == last_hname:
		   <td class="tdBorderLeft tdCriticity" style="width: 120px;"> </td>
		%else:
		    <td class="tdBorderLeft tdCriticity" style="width: 120px;"> {{!helper.get_host_link(pb)}}</td>
		%end
		%last_hname = pb.host_name

		%if pb.__class__.my_type == 'service':
		  <td	class="tdBorderTop tdBorderLeft tdCriticity" style="width:120px;">{{!helper.get_link(pb, short=True)}}</td>
		%else:
                  <td   class="tdBorderTop tdBorderLeft tdCriticity" style="width:120px;"></td>
                %end
		<td class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;"> {{pb.state}}</td>
		<td title='{{helper.print_date(pb.last_state_change)}}' class="tdBorderTop tdBorderLeft tdCriticity" style="width:50px;">{{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</td>
		<td title="{{pb.output}}" class="tdBorderTop tdBorderLeft tdCriticity" style="width:350px;"> {{pb.output[:55]}}</td>
		<td class="tdBorderLeft tdCriticity opacity_hover shortdesc" style="max-width:20px;" onclick="show_detail('{{pb.get_full_name()}}')"> <img src="/static/images/expand.png" /> </td>
		</tr>
             </table>
	  </div>  
	  %# " We put actions buttons with a opacity hover effect, so they won't be too visible"
	  <div class="opacity_hover">
	    <div style="float:right;">
	      <a href="#" onclick="try_to_fix('{{pb.get_full_name()}}')">{{!helper.get_button('Fix!', img='/static/images/enabled.png')}}</a>
	    </div>
	    <div style="float:right;">
	      <a href="#" onclick="acknoledge('{{pb.get_full_name()}}')">{{!helper.get_button('Ack', img='/static/images/wrench.png')}}</a>
	    </div>
	    <div style="float:right;">
	      <a href="#" onclick="recheck_now('{{pb.get_full_name()}}')">{{!helper.get_button('Recheck', img='/static/images/delay.gif')}}</a>
	    </div>
	  </div>
	</div>

    %# "This div is need so the element will came back in the center of the previous div"
    <div class="clear"></div>
      <div id="{{pb.get_full_name()}}" class="detail">
	<table class="tableCriticity">
	  <tr>
	    <td class="tdBorderLeft tdCriticity" style="width:20px;"><b>Host</b></td>
	    %if pb.__class__.my_type == 'service':
	    <td class="tdCriticity" style="width:20px;"><b>Service</b></td>
	    %end
	    <td class="tdBorderLeft tdCriticity" style="width:20px;"><b>Realm</b></td>
	    <td class="tdBorderLeft tdCriticity" style="width:20px;"><b>Last check</b></td>
	    <td class="tdBorderLeft tdCriticity" style="width:20px;"><b>Next check</b></td>
	    <td class="tdCriticity" style="width:20px;"><b>Actions</b></td>
	    <td class="tdCriticity" style="width:40px;">	<div style="float:right;">
		<a href="#">{{!helper.get_button('Add to fav', img='/static/images/heart_add.png')}}</a>
	      </div>
	    </td>
	  </tr>
	  <tr>
	    <td class="tdBorderTop tdCriticity" style="width:20px;">{{pb.host_name}}</td>
	    %if pb.__class__.my_type == 'service':
	    <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:20px;">{{pb.service_description}}</td>
	    %end
	    <td class="tdBorderTop tdBorderLeft tdBorderLeft tdCriticity" style="width:20px;">{{pb.get_realm()}}</td>
	    <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:20px;">{{helper.print_duration(pb.last_chk, just_duration=True, x_elts=2)}} ago</td>
	    <td class="tdBorderTop tdBorderLeft tdCriticity" style="width:20px;">in {{helper.print_duration(pb.next_chk, just_duration=True, x_elts=2)}}</td>
	    
	    <td class="tdCriticity" style="width:20px;"></td>
	    <td class="tdCriticity" style="width:20px;"><div style="float:right;"> <a href="{{!helper.get_link_dest(pb)}}">{{!helper.get_button('Go to details', img='/static/images/search.png')}}</a>
	</div> </td>
	  </tr>
	</table>

	<hr />
	%if len(pb.impacts) > 0:
	<h5>Impacts:</h5>
	%end
	%for i in helper.get_impacts_sorted(pb):
	<div class="state_{{i.state.lower()}}">
	  <p><img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(i)}}" />
	        %for j in range(0, i.business_impact-2):
	          <img src='/static/images/star.png'>
		%end
	     {{!helper.get_link(i)}} is {{i.state}}
	  </p>
	</div>
	%end
      </div>
    %end
  </div>
      
</div>

<div class="clear"></div>
</div>

Page generated in {{"%.2f" % (time.time() - start)}} seconds
%include footer


