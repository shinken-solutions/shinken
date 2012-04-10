
%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()



%rebase layout globals(), title='All problems', top_right_banner_state=top_right_banner_state, js=['problems/js/img_hovering.js', 'problems/js/accordion.js', 'problems/js/sliding_navigation.js', 'problems/js/filters.js'], css=['problems/css/accordion.css', 'problems/css/pagenavi.css', 'problems/css/perfometer.css', 'problems/css/img_hovering.css', 'problems/css/sliding_navigation.css', 'problems/css/filters.css'], refresh=True, menu_part='/'+page, user=user 


%# Look for actions if we must show them or not
%global_disabled = ''
%if not helper.can_action(user):
%global_disabled = 'disabled-link'
<script type="text/javascript">
  var actions_enabled = false;
</script>
%else:
<script type="text/javascript">
  var actions_enabled = true;
</script>
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


	var active_filters = [];

	

</script>

%# "We set the actions div that will be show/hide if we select elements"
<ul class="sliding-navigation" id="actions">
  <li class="sliding-element"><h3>Actions</h3></li>
  <li class="sliding-element">
    <a href="javascript:try_to_fix_all();"><i class="icon-pencil icon-white"></i> Try to fix</a>
  </li>		
  <li class="sliding-element">
    <a href="javascript:recheck_now_all()"><i class="icon-repeat icon-white"></i> Recheck</a>
  </li>
  <li class="sliding-element">
    <a href="javascript:acknowledge_all('{{user.get_name()}}')"><i class="icon-ok icon-white"></i> Acknowledge</a>
  </li>
</ul>


<script type="text/javascript">
    // We will create here our new filter options
    // This should be outside the "pageslide" div. I don't know why
    new_filters = [];
</script>

<div id="pageslide" style="display:none">
  <div class='row'>
    <span><h2>Filtering options</h2></span>
    <span class='pull-right'><a class='btn btn-danger' href="javascript:$.pageslide.close()"><i class="icon-remove"></i> Close</a></span>    
  </div>
  <div class='in_panel_filter'>
    <h3>Names</h3>
    <form name='namefilter'>
      <input name='name'></input>
      <p><a class='btn btn-success pull-right' href="javascript:save_name_filter();"> <i class="icon-chevron-right"></i> Add a name filter</a></p>
    </form>

    <span><p>&nbsp;</p></span>
    <h3>Hostgroup</h3>
    <form name='hgfilter'>
      <select name='hg'>
	%for hg in datamgr.get_hostgroups_sorted():
	<option value='{{hg.get_name()}}'> {{hg.get_name()}} ({{len(hg.members)}})</option>
	%end
      </select>
      <p><a class='btn btn-success pull-right' href="javascript:save_hg_filter();"> <i class="icon-chevron-right"></i> Add a group filter</a></p>
    </form>
    <span><p>&nbsp;</p></span>
  </div>
  <div class='row'>
    <span class='pull-left'><a class='btn btn-inverse' href="javascript:clean_new_search();"> <i class="icon-remove"></i> Remove all filters</a></span>
  <span class='pull-right'><a class='btn btn-warning' href="javascript:launch_new_search('/{{page}}');"> <i class="icon-play"></i> Launch the search!</a></span>
    <span><p>&nbsp;</p></span>
  </div>
  <div id='new_search'>
  </div>

</div>

<script >$(function(){
  $(".slidelink").pageslide({ direction: "right", modal : true});
  });
</script>






<div class="span12">
  
  <div class='row'>
    <div class='span2 offset2'>
      <a id='select_all_btn' href="javascript:select_all_problems()" class="btn pull-left"><i class="icon-check"></i> Select all</a>
      <a id='unselect_all_btn' href="javascript:unselect_all_problems()" class="btn pull-left"><i class="icon-minus"></i> Unselect all</a>
    </div>
    <div class='span7'>
      %if navi is not None:
      <div class="pagination center no-margin">
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
    </div>
    
    <div class='span1'>
      <div class="btn-group pull-right">
	<button class="btn"> <i class="icon-cog"></i> </button>
	<button class="btn dropdown-toggle" data-toggle="dropdown">
	  <span class="caret"></span>
	</button>
	<ul class="dropdown-menu">
	  <li>
	    <form>
	      <select name='nb_elements'>
		%t = [30, 50, 100, 200, 500, 1000, '5k', '10k', 'all']
		%for v in t:
		  <option value={{v}}>{{v}}</option>
		%end
	      </select>
	    </form>
	  </li>
	</ul>
      </div>
      
    </div>
</div>


<div class='row-fluid'>
  <div class='span2'>
    <a href="#pageslide" class="slidelink btn btn-success"><i class="icon-plus"></i> Show filters</a>
    <p></p>
    %if len([k for (k,v) in filters.iteritems() if v != '']) > 0:
      <h3>Active filters</h3>
    %end
    <ul class="unstyled">

    %for n in filters['hst_srv']:
    <li>
      <span class="filter_color hst_srv_filter_color">&nbsp;</span>
      <span class="hst_srv_filter_name">Name : {{n}}</span>
      <span class="filter_delete"><a class="close">&times;</a></span>
    </li>
    <script>add_hst_srv_filter('{{n}}');</script>
    %end

    %for hg in filters['hg']:
    <li>
      <span class="filter_color hg_filter_color">&nbsp;</span>
      <span class="hg_filter_name">Group : {{hg}}</span>
      <span class="filter_delete"><a class="close">&times;</a></span>
    </li>
    <script>add_hg_filter('{{hg}}');</script>
    %end
    

    </ul>
    <br/>
    <button class="btn btn-info"> <i class="icon-cog"></i> Save this search</button>
  </div>
    <div class="span10 no-leftmargin">
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

	  <div class="tableCriticity pull-left">
%#	    <table class="tableCriticity">
	      <div class='tick pull-left' style="cursor:pointer;" onclick="add_remove_elements('{{helper.get_html_id(pb)}}')"><img id='selector-{{helper.get_html_id(pb)}}' class='img_tick' src='/static/images/tick.png' /></div>
	      <div class='img_status pull-left'>
		<div class="aroundpulse">
		    %# " We put a 'pulse' around the elements if it's an important one "
		    %if pb.business_impact > 2 and pb.state_id in [1, 2, 3]:
		         <span class="pulse"></span>
	            %end
		    <img src="{{helper.get_icon_state(pb)}}" /></div>
		</div>
		%if pb.host_name == last_hname:
		   <div class="hostname cut_long pull-left"> &nbsp;  </div>
		%else:
	          <div class="hostname cut_long pull-left"> {{!helper.get_host_link(pb)}}</div>
		%end
		%last_hname = pb.host_name

		%if pb.__class__.my_type == 'service':
		  <div class="srvdescription cut_long pull-left">{{!helper.get_link(pb, short=True)}}</div>
		%else:
                  <div class="srvdescription cut_long pull-left"> &nbsp; </div>
                %end
		<div class='txt_status state_{{pb.state.lower()}}  pull-left'> {{pb.state}}</div>
		<div class='duration pull-left' rel="tooltip" data-original-title='{{helper.print_date(pb.last_state_change)}}'>{{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}</div>
		%# "We put a title (so a tip) on the output onlly if need"
		%if len(pb.output) > 100:
		   %if app.allow_html_output:
		      <div class='output pull-left' rel="tooltip" data-original-title="{{pb.output}}"> {{!helper.strip_html_output(pb.output[:100])}}</div>
		   %else:
		      <div class='output pull-left' rel="tooltip" data-original-title="{{pb.output}}"> {{pb.output[:100]}}</div>
		   %end
		%else:
		   %if app.allow_html_output:
                     <div class='output pull-left'> {{!helper.strip_html_output(pb.output)}}</div>
		   %else:
		      <div class='output pull-left'> {{pb.output}} </div>
                   %end
		%end
		%graphs = app.get_graph_uris(pb, now- 4*3600 , now)
		%onmouse_code = ''
		%if len(graphs) > 0:
		      %onmouse_code = 'onmouseover="display_hover_img(\'%s\',\'\');" onmouseout="hide_hover_img();" ' % graphs[0]['img_src']
		%end
		<div class="perfometer pull-left" {{!onmouse_code}}>
		  {{!helper.get_perfometer(pb)}} &nbsp;
		</div>
		<div class="no_border opacity_hover shortdesc expand pull-right" style="max-width:20px;" onclick="show_detail('{{helper.get_html_id(pb)}}')"><i class="icon-chevron-down" id='show-detail-{{helper.get_html_id(pb)}}'></i> <i class="icon-chevron-up chevron-up" id='hide-detail-{{helper.get_html_id(pb)}}'></i> </div>
		
	      
%#             </table>
	  </div>  
	  <div style="clear:both;"/>
	</div>
       </div>

    %# "This div is need so the element will came back in the center of the previous div"
    <div class="clear"></div>
      <div id="{{helper.get_html_id(pb)}}" class="detail row-fluid">
	<table class="well tableCriticity table-bordered table-condensed span6">
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
</div>

%# """ This div is an image container and will move hover the perfometer with mouse hovering """
<div id="img_hover"></div>

