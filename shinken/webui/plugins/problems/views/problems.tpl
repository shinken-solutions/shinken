%import time
%start = time.time()

%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%include header title='All problems', top_right_banner_state=top_right_banner_state, js=['problems/js/accordion.js'], css=['problems/accordion.css']


	 
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

<div class="grid_13">
  <div id="accordion">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %for pb in pbs:

    <div class="clear"></div>      
      %if pb.business_impact != imp_level:
       <h2> Business impact : {{!helper.get_business_impact_text(pb)}} </h2>
      %end
      %imp_level = pb.business_impact


	<div> 
	  <div class="toggler">
	    <h4 style="margin-bottom:3px;">
	      <img src="/static/images/state_{{pb.state.lower()}}.png" />
	      {{pb.get_full_name()}} is {{pb.state}} since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}
	    </h4>
	  </div>
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

    %# "This div is need so the element will came back in the center of the previous div"
    <div class="clear"></div>
      <div class="element">
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
	    <td class="tdCriticity" style="width:40px;"><img src="/static/images/heart_add.png" />Add to Fav </td>
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
	    <td class="tdCriticity" style="width:20px;"><img src="/static/images/accept.png" />Try to fix it! </td>
	  </tr>
	</table>
	<hr />
	%if len(pb.impacts) > 0:
	<h5>Impacts:</h5>
	%end
	%for i in helper.get_impacts_sorted(pb):
	<div class="state_{{i.state.lower()}}">
	  <p><img src="/static/images/state_{{i.state.lower()}}.png" />
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


