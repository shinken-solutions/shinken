
%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%rebase layout globals(), title='All problems', top_right_banner_state=top_right_banner_state, js=['problems/js/img_hovering.js', 'problems/js/accordion.js'], css=['problems/css/accordion.css', 'problems/css/pagenavi.css', 'problems/css/perfometer.css', 'problems/css/img_hovering.css'], refresh=True, menu_part='/'+page, user=user 


%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end


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

	$('.typeahead').typeahead({
	// note that "value" is the default setting for the property option
	   /*source: [{value: 'Charlie'}, {value: 'Gudbergur'}, {value: 'Charlie2'}],*/
	   source: function (typeahead, query) {
	              $.ajax({url: "/lookup/"+query,
	                      success: function (data){
	                        typeahead.process(data)}
	              });
	           },
	onselect: function(obj) { 
	             $("ul.typeahead.dropdown-menu").find('li.active').data(obj);
	         }
	});

</script>

%# "We set the actions div that will be show/hide if we select elements"
<div class="dockContainer">
  <div class="dockWrapper" id="actions">
    <div class="cap left"></div>
    <ul class="dock">
      <li class="active">
	<span>Fix</span>
	<a href="javascript:try_to_fix_all();"><img src="/static/images/tools.png" alt="tools"/></a>
      </li>		
      <li>
	<span>Recheck</span>
	<a href="javascript:recheck_now_all()"><img src="/static/images/big_refresh.png" alt="refresh"/></a>
      </li>
      <li>
	<span>Acknowledge</span>
	<a href="javascript:acknowledge_all('{{user.get_name()}}')"><img src="/static/images/big_ack.png" alt="acknowledge"/></a>
      </li>
      
    </ul>
  </div>
</div>



   <div class="span12 offset2">

  	%if navi is not None:
    <div class="pagination center">
	    <ul class="pull-right">
	    %for name, start, end, is_current in navi:
	    	%if is_current:
	    	<li class="active"><a href="#">{{name}}</a></li>
	    	%elif start == None or end == None:
	    	<li class="disabled"> <a href="#">...</a> </li>
	    	%else:
			<li><a href='/{{page}}?start={{start}}&end={{end}}' class='page larger'>{{name}}</a></li>
	    	%end
	    %end
	    </ul>
    </div>
  	%# end of the navi part
  	%end

  <div id="accordion" class="span12">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %# " We remember the last hname so see if we print or not the host for a 2nd service"
    %last_hname = ''

    %# " We try to make only importants things shown on same output "
    %last_output = ''
    %nb_same_output = 0

    %for pb in pbs:
     
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

	  <div>
	    <table class="tableCriticity">
	      <tr>
	        <td class='tick'> <img src="/static/images/untick.png" alt="untick" /style="cursor:pointer;" onclick="add_remove_elements('{{helper.get_html_id(pb)}}')" id="selector-{{helper.get_html_id(pb)}}" > </td>
		<td class='img_status'> <div class="aroundpulse">
		    %# " We put a 'pulse' around the elements if it's an important one "
		    %if pb.business_impact > 2 and pb.state_id in [1, 2, 3]:
		         <span class="pulse"></span>
	            %end
		    <img src="{{helper.get_icon_state(pb)}}" /></div>
		</td>
		%if pb.host_name == last_hname:
		   <td class="hostname"> </td>
		%else:
		    <td class="hostname"> {{!helper.get_host_link(pb)}}</td>
		%end
		%last_hname = pb.host_name

		%if pb.__class__.my_type == 'service':
		  <td class="srvdescription">{{!helper.get_link(pb, short=True)}}</td>
		%else:
                  <td class="srvdescription"></td>
                %end
		<td class='txt_status state_{{pb.state.lower()}}'> {{pb.state}}</td>
		<td class='duration' rel="tooltip" data-original-title='{{helper.print_date(pb.last_state_change)}}'>{{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</td>
		%# "We put a title (so a tip) on the output onlly if need"
		%if len(pb.output) > 100:
		   %if app.allow_html_output:
		      <td class='output' rel="tooltip" data-original-title="{{pb.output}}"> {{!helper.strip_html_output(pb.output[:100])}}</td>
		   %else:
		      <td class='output' rel="tooltip" data-original-title="{{pb.output}}"> {{pb.output[:100]}}
		   %end
		%else:
		   %if app.allow_html_output:
                      <td class='output'> {{!helper.strip_html_output(pb.output)}}</td>
		   %else:
		      <td class='output'> {{pb.output}} </td>
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
		<td class="no_border opacity_hover shortdesc expand" style="max-width:20px;" onclick="show_detail('{{helper.get_html_id(pb)}}')"> <img src="/static/images/expand.png" alt="expand" /> </td>
		
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
      <div id="{{helper.get_html_id(pb)}}" class="detail row-fluid">
	<table class="tableCriticity table-bordered table-condensed span6">
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
	    <td class="tdCriticity" style="width:20px;"><div style="float:right;"> <a href="{{!helper.get_link_dest(pb)}}" class='btn'><i class="icon-search"></i> Details</a>
	</div> </td>
	  </tr>
	</table>


	<div class='span8'>
	%if len(pb.impacts) > 0:
	<hr />
	<h5>Impacts:</h5>
	%end
	%for i in helper.get_impacts_sorted(pb):
	<div>
	  <p><img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(i)}}" />
	    <span class="alert-small alert-{{i.state.lower()}}">{{i.state}}</span> for {{!helper.get_link(i)}}
	        %for j in range(0, i.business_impact-2):
	          <img src='/static/images/star.png' alt="star">
		%end
	  </p>
	</div>
	%end
	</div>
      </div>


    %end
  </div>

	%if navi is not None:
	<div class="pagination center">
		<ul class="pull-right">
		%for name, start, end, is_current in navi:
		   	%if is_current:
		   	<li class="active"><a href="#">{{name}}</a></li>
		   	%elif start == None or end == None:
		   	<li class="disabled"> <a href="#">...</a> </li>
			%elif search:
			<a href='/{{page}}?start={{start}}&end={{end}}&search={{search}}' class='page larger'>{{name}}</a>
		   	%else:
			<li><a href='/{{page}}?start={{start}}&end={{end}}' class='page larger'>{{name}}</a></li>
		   	%end
		    %end
		</ul>
	</div>
	%# end of the navi part
	%end


</div>


%# """ This div is an image container and will move hover the perfometer with mouse hovering """
<div id="img_hover"></div>


  <a class="btn" href="/blabla" data-toggle="modal" data-target="#modal">Launch Modal</a>      
