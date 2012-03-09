%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%title = {'problems' : 'IT problems', 'all' : 'All elements'}.get(page, 'Unknown page')

%top_right_banner_state = datamgr.get_overall_state()


%rebase layout title=title, top_right_banner_state=top_right_banner_state, js=['problems/js/img_hovering.js', 'problems/js/accordion.js'], css=['problems/css/accordion.css', 'problems/css/pagenavi.css', 'problems/css/perfometer.css', 'problems/css/img_hovering.css'], refresh=True, menu_part='/'+page, user=user


%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end


%# " Add the auto copleter in the search input form"
<script type="text/javascript">
document.addEvent('domready', function() {
 
  var inputWord = $('search_input');
 
  // Our instance for the element with id "search_input"
  new Autocompleter.Request.JSON(inputWord, '/lookup', {
       'indicatorClass': 'autocompleter-loading',
       'minLength': 3
  });

});
</script>


<script type="text/javascript">
	function submitform()
	{
	document.forms["search_form"].submit();
	}
	
	/* Catch the key ENTER and launch the form 
	 Will be link in the password field
	*/
	function submitenter(myfield,e){
	  var keycode;
	  if (window.event) keycode = window.event.keyCode;
	  else if (e) keycode = e.which;
	  else return true;
	
	
	  if (keycode == 13){
	    submitform();
	    return false;
	  }else
	   return true;
	}
</script>


	 
<div id="left_container" class="grid_3">

  <div id="nav_left">
    <ul>
      <li class="left_title"><a href="#">Overview</a></li>
      <li>
					<div class="tac_header">
						<div class="tac_col_1">
							Problems
						</div>
						<div class="tac_col_2">
							Unhandled
						</div>
						<div class="tac_col_3">
							All
						</div>
					</div>
					<div class="tac_content">
						<div class="tac_col_1">
							<a href="/problems/{{show}}" style="padding-top:0;">{{app.datamgr.get_nb_all_problems()}}</a>
						</div>
						<div class="tac_col_2">
							<a href="/problems/{{show}}" style="padding-top:0;">{{app.datamgr.get_nb_problems()}}</a>
						</div>
						<div class="tac_col_3">
							<a href="/all" style="padding-top:0;">{{app.datamgr.get_nb_elements()}}</a>
						</div>
					</div>
      </li>

      <li class="left_title"><a href="#">Search</a></li>
      <li>
				<form method="get" id="search_form" action="/{{page}}/{{show}}">
					<span class="table">
						<span class="row">
							<span class="cell">
								<input name="search" type="text" tabindex="1" value="{{search}}" id="search_input"/>
							</span>
							<span class="cell">
								<a tabindex="4" href="javascript: submitform()">
								<img src="/static/images/search.png" alt="search"/>
								</a>
							</span>
						</span>
					</span>
				</form>
      </li>

  %if page == 'problems':
      <li class="left_title"><a href="#">Filter</a></li>
      <li>
                                <a href="/problems/all">See All</a>
                                <a href="/problems/warning">See Warnings</a>
                                <a href="/problems/critical">See Critical only</a>
      </li>
  %end
    </ul>
  </div>
</div>

%# "We set the actions div that will be show/hide if we select elements"
<div class="dockContainer">
  <div class="dockWrapper" id="actions">
    <div class="cap left"></div>
    <ul class="dock">
      <li class="active">
	<span>Fix</span>
	<a href="#" onclick="try_to_fix_all()"><img src="/static/images/tools.png" alt="tools"/></a>
      </li>		
      <li>
	<span>Recheck</span>
	<a href="#" onclick="recheck_now_all()"><img src="/static/images/big_refresh.png" alt="refresh"/></a>
      </li>
      <li>
	<span>Acknowledge</span>
	<a href="#" onclick="acknowledge_all()"><img src="/static/images/big_ack.png" alt="acknowledge"/></a>
      </li>
      
    </ul>
  </div>
</div>
<div class="grid_13">

  %if navi is not None:
      <div id="pagination">
	<div class='pagenavi'>
	  %for name, start, end, is_current in navi:
	     %if is_current:
	        <span class='current'>{{name}}</span>
	     %elif start == None or end == None:
		<span class='extend'>...</span>
	     %elif search:
                <a href='/{{page}}/{{show}}?start={{start}}&end={{end}}&search={{search}}' class='page larger'>{{name}}</a>
             %else:
		<a href='/{{page}}/{{show}}?start={{start}}&end={{end}}' class='page larger'>{{name}}</a>
	     %end
          %end
	</div>
      </div>
  %# end of the navi part
  %end



  <div id="accordion">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %# " We remember the last hname so see if we print or not the host for a 2nd service"
    %last_hname = ''

    %# " We try to make only importants things shown on same output "
    %last_output = ''
    %nb_same_output = 0

    %for pb in pbs:

      <div class="clear"></div>      
      %if pb.business_impact != imp_level:
       <h2> Business impact : {{!helper.get_business_impact_text(pb)}} </h2>
       %# "We reset the last_hname so we won't overlap this feature across tables"
       %last_hname = ''
       %last_output = ''
       %nb_same_output = 0
      %end
      %imp_level = pb.business_impact

      %# " We check for the same output and the same host. If we got more than 3 of same, make them opacity effect"
      %if pb.output == last_output and pb.host_name == last_hname:
          %nb_same_output += 1
      %else:
          %nb_same_output = 0
      %end
      %last_output = pb.output

      %if nb_same_output > 3:
       <div class='opacity_hover'>
      %else:
       <div>
      %end

	  <div style="margin-left: 20px; width: 95%; float:left;">
	    <table class="tableCriticity" style="width: 100%; margin-bottom:3px;">
	      <tr class="tabledesc">
	        <td class="no_border" style="width:20px; background:none;"> <img src="/static/images/untick.png" alt="untick" /style="cursor:pointer;" onclick="add_remove_elements('{{pb.get_full_name()}}')" id="selector-{{pb.get_full_name()}}" > </td>
	        <td class="no_border" style="width:20px;"> <div class="aroundpulse">
		    %# " We put a 'pulse' around the elements if it's an important one "
		    %if pb.business_impact > 2 and pb.state_id in [1, 2, 3]:
		    <span class="pulse"></span>
		    %end
		    <img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(pb)}}" /></div> </td>
		%if pb.host_name == last_hname:
		   <td class="no_border" style="width: 120px;"> </td>
		%else:
		    <td class="no_border" style="width: 120px;"> {{!helper.get_host_link(pb)}}</td>
		%end
		%last_hname = pb.host_name

		%if pb.__class__.my_type == 'service':
		  <td	class=" no_border" style="width:120px;">{{!helper.get_link(pb, short=True)}}</td>
		%else:
                  <td   class=" no_border" style="width:120px;"></td>
                %end
		<td class=" no_border {{pb.__class__.my_type}}_{{pb.state_id}}" style="width:50px;"> {{pb.state}}</td>
		<td title='{{helper.print_date(pb.last_state_change)}}' class=" no_border" style="width:50px;">{{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</td>
		%# "We put a title (so a tip) on the output onlly if need"
		%if len(pb.output) > 100:
		   %if app.allow_html_output:
		      <td title="{{pb.output}}" class=" no_border" style="width:450px;"> {{!helper.strip_html_output(pb.output[:100])}}</td>
		   %else:
		      <td title="{{pb.output}}" class=" no_border" style="width:450px;"> {{pb.output[:100]}}
		   %end
		%else:
		   %if app.allow_html_output:
                      <td class=" no_border" style="width:450px;"> {{!helper.strip_html_output(pb.output)}}</td>
		   %else:
		      <td class=" no_border" style="width:450px;"> {{pb.output}} </td>
                   %end
		%end
		%graphs = app.get_graph_uris(pb, now- 4*3600 , now)
		%onmouse_code = ''
		%if len(graphs) > 0:
		      %onmouse_code = 'onmouseover="display_hover_img(\'%s\',\'\');" onmouseout="hide_hover_img();" ' % graphs[0]['img_src']
		%end
		<td class="perfometer" {{!onmouse_code}}>
		  {{!helper.get_perfometer(pb)}}
		</td>
		<td class="no_border opacity_hover shortdesc" style="max-width:20px;" onclick="show_detail('{{pb.get_full_name()}}')"> <img src="/static/images/expand.png" alt="expand" /> </td>
		
		</tr>
	      
             </table>
	  </div>  
	  %# " We put actions buttons with a opacity hover effect, so they won't be too visible"
%#	  <div class="opacity_hover" >
%#	    <div style="float:right;">
%#	      <a href="#" onclick="try_to_fix('{{pb.get_full_name()}}')">{{!helper.get_button('Fix!', img='/static/images/enabled.png')}}</a>
%#	    </div>
%#	    <div style="float:right;">
%#	      <a href="#" onclick="acknowledge('{{pb.get_full_name()}}')">{{!helper.get_button('Ack', img='/static/images/wrench.png')}}</a>
%#	    </div>
%#	    <div style="float:right;">
%#	      <a href="#" onclick="recheck_now('{{pb.get_full_name()}}')">{{!helper.get_button('Recheck', img='/static/images/delay.gif')}}</a>
%#	    </div>
%#	  </div>
	</div>

    %# "This div is need so the element will came back in the center of the previous div"
    <div class="clear"></div>
      <div id="{{pb.get_full_name()}}" class="detail">
	<table class="tableCriticity">
	  <tr>
	    <td style="width:20px;"><b>Host</b></td>
	    %if pb.__class__.my_type == 'service':
	    <td class="tdCriticity" style="width:20px;"><b>Service</b></td>
	    %end
	    <td style="width:20px;"><b>Realm</b></td>
	    <td style="width:20px;"><b>Last check</b></td>
	    <td style="width:20px;"><b>Next check</b></td>
	    <td class="tdCriticity" style="width:20px;"><b>Actions</b></td>
	    <td class="tdCriticity" style="width:40px;">	<div style="float:right;">
		<a href="#">{{!helper.get_button('Add to fav', img='/static/images/heart_add.png')}}</a>
	      </div>
	    </td>
	  </tr>
	  <tr>
	    <td class=" tdCriticity" style="width:20px;">{{pb.host_name}}</td>
	    %if pb.__class__.my_type == 'service':
	    <td  style="width:20px;">{{pb.service_description}}</td>
	    %end
	    <td class=" tdBorderLeft" style="width:20px;">{{pb.get_realm()}}</td>
	    <td  style="width:20px;">{{helper.print_duration(pb.last_chk, just_duration=True, x_elts=2)}} ago</td>
	    <td  style="width:20px;">in {{helper.print_duration(pb.next_chk, just_duration=True, x_elts=2)}}</td>
	    
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
	          <img src='/static/images/star.png' alt="star">
		%end
	     {{!helper.get_link(i)}} is {{i.state}}
	  </p>
	</div>
	%end
      </div>


    %end
  </div>

  %if navi is not None:
      <div id="pagination">
	<div class='pagenavi'>
	  %for name, start, end, is_current in navi:
	     %if is_current:
	        <span class='current'>{{name}}</span>
	     %elif start == None or end == None:
		<span class='extend'>...</span>
             %else:
		<a href='/{{page}}/{{show}}?start={{start}}&end={{end}}' class='page larger'>{{name}}</a>
	     %end
          %end
	</div>
      </div>
  %# end of the navi part
  %end

      
</div>

<div class="clear"></div>

%# """ This div is an image container and will move hover the perfometer with mouse hovering """
<div id="img_hover"></div>
