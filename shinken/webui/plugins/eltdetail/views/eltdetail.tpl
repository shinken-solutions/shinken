%# " We should limit the number of impacts to show here. Too much is just useless "
%max_impacts = 200

%print 'Elt value?', elt
%import time

%# If got no Elt, bailout
%if not elt:
%rebase layout title='Invalid name'

Invalid element name

%else:

%helper = app.helper
%datamgr = app.datamgr

%elt_type = elt.__class__.my_type

%top_right_banner_state = datamgr.get_overall_state()

%rebase layout title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(),  js=['eltdetail/js/functions.js','eltdetail/js/graphs.js', 'eltdetail/js/dollar.js','eltdetail/js/TabPane.js', 'eltdetail/js/gesture.js', 'eltdetail/js/hide.js', 'eltdetail/js/switchbuttons.js', 'eltdetail/js/multi.js'],  css=['eltdetail/css/eltdetail2.css', 'eltdetail/css/hide.css', 'eltdetail/css/gesture.css'], top_right_banner_state=top_right_banner_state , user=user, app=app

%# " We will save our element name so gesture functions will be able to call for the good elements."
<script type="text/javascript">var elt_name = '{{elt.get_full_name()}}';</script>

%#  "Left Container Start"
<div id="left_container" class="grid_2">
	<div id="nav_left">
		<ul>
			<li><a href="#">Overview</a></li>
			<li><a class="pointer_down" id="v_toggle" href="#">Gesture</a></li>
		</ul>
	</div>
	
	<div id="gesture_slide" class="grid_16 opacity_hover">
	%#  "This is the background canvas for all gesture detection things " 
	%# " Don't ask me why, but the size must be included in the
	%# canvas line here or we got problem!"
		<canvas id="canvas" class="grid_10" style="border: 1px solid black; width: 100%;"></canvas>
		<ul>
			<li class="gesture_button">
		       	<img title="By keeping a left click pressed and drawing a check, you will launch an acknowledgement." src="/static/eltdetail/images/gesture-check.png"/> Acknowledge
			</li>
			<li class="gesture_button">
		       	<img title="By keeping a left click pressed and drawing a check, you will launch an recheck." src="/static/eltdetail/images/gesture-circle.png"/> Recheck
			</li>
			<li class="gesture_button">
		       	<img title="By keeping a left click pressed and drawing a check, you will launch a try to fix command." src="/static/eltdetail/images/gesture-zigzag.png"/> Fix
			</li>
		</ul>
	</div>	    
	
</div>
%#  "Left Container End"

%#  "Content Container Start"
<div id="content_container" class="grid_14">

	<h1 class="grid_16 state_{{elt.state.lower()}} icon_down"><img class="host_img_25" src="{{helper.get_icon_state(elt)}}" />{{elt.state}}: {{elt.get_full_name()}}</h1>
	
	<div id="overview_container" class="grid_16">	   
		<table class="grid_5">
		%#Alias, apretns and hostgroups arefor host only
		%if elt_type=='host':
			<tr>
		    	<td>Alias:</td>
		    	<td>{{elt.alias}}</td>
			</tr>
			<tr>
		    	<td>Address:</td>
		    	<td>{{elt.address}}</td>
			</tr>
			<tr>
		    	<td>Importance:</td>
		    	<td>{{!helper.get_business_impact_text(elt)}}</td>
			</tr>
		</table>
		
		<table class="grid_4">
			<tr>
		    	<td>Parents:</td>
		    	%if len(elt.parents) > 0:
		    	<td>{{elt.alias}}</td>
		    	%else:
		    	<td>No parents</td>
		    	%end
			</tr>
			<tr>
		    	<td>Members of:</td>
		    	%if len(elt.hostgroups) > 0:
		    	<td>{{','.join([hg.get_name() for hg in elt.hostgroups])}}</td>
		    	%else:
			    <td> No groups </td>
				%end
			</tr>
			%# End of the host only case, so now service
		    %else:
			<tr>
		    	<td>Host:</td>
		    	<td><a href="/host/{{elt.host.host_name}}" class="link">{{elt.host.host_name}}</a></td>
			</tr>
			<tr>
		    	<td>Members of:</td>
		    	%if len(elt.servicegroups) > 0:
		    	<td>{{','.join([sg.get_name() for sg in elt.servicegroups])}}</td>
				%else:
			    <td> No groups </td>
				%end
			</tr>
			%end
			<tr>
			  	<td>Notes:</td>
			    %if elt.notes != '':
			    <td>{{elt.notes}}</td>
			    %else:
			    <td>(none)</td>
			    %end
			</tr>
		</table>	    

		<div class="grid_7">
		    %#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
		    %if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
			<div class="ui-state-error ui-corner-all push_top2">
				<p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>	This element has got an important impact on your business, please <b>fix it</b> or <b>acknowledge it</b>.</p>
			</div>
		    %# "end of the 'SOLVE THIS' highlight box"
		    %end
		</div>				
	</div>
	
	<!-- Switch Start -->
	<div class="switches">
		<ul class="grid_16">
		    %if elt_type=='host':
		       %title = 'This will also enable/disable this host services'
		    %else:
		       %title = ''
		    %end
			<li class="grid_4" title="{{title}}" onclick="toggle_checks('{{elt.get_full_name()}}' , '{{elt.active_checks_enabled|elt.passive_checks_enabled}}')"><span>Active/passive Checks</span> {{!helper.get_input_bool(elt.active_checks_enabled|elt.passive_checks_enabled)}}
			<li class="grid_4" onclick="toggle_notifications('{{elt.get_full_name()}}' , '{{elt.notifications_enabled}}')"><span>Notifications</span> {{!helper.get_input_bool(elt.notifications_enabled)}} </li>
			<li class="grid_4" onclick="toggle_event_handlers('{{elt.get_full_name()}}' , '{{elt.event_handler_enabled}}')" ><span>Event Handler</span> {{!helper.get_input_bool(elt.event_handler_enabled)}} </li>
			<li class="grid_4" onclick="toggle_flap_detection('{{elt.get_full_name()}}' , '{{elt.flap_detection_enabled}}')" ><span>Flap Detection</span> {{!helper.get_input_bool(elt.flap_detection_enabled)}} </li>	
		</ul>	
	</div>
    <!-- Switch End-->
    
    <!-- elt Container Start-->
	<div id="elt_container" class="grid_16">
		<!-- Tabs -->
		<div id="tabs">
			<ul>
	        	<li><a href="#summary">Summary</a></li>
	            <li><a href="#services">Services</a></li>
	            <li><a href="#comments">Comments/Downtimes</a></li>
				<li><a href="#graphs">Graphs</a></li>
			</ul>
			
			<!-- Tab Summary Start-->
	        <div id="summary">
				<div id="item_information">
					<h2>Host/Service Information</h2>
					<table>
						<tr>
							<td class="column1">{{elt_type.capitalize()}} Status</td>
							<td><span class="state_{{elt.state.lower()}}">{{elt.state}}</span> (since {{helper.print_duration(elt.last_state_change, just_duration=True, x_elts=2)}}) </td>
						</tr>
						<tr>
							<td class="column1">Status Information</td>
							<td>{{elt.output}}</td>
						</tr>
						<tr>
							<td class="column1">Performance Data</td>
							%# "If there any perf data?"
							%if len(elt.perf_data) > 0:
							<td>{{elt.perf_data}}</td>
							%else:
							<td>&nbsp;</td>
							%end
						</tr>	
						<tr>										
							<td class="column1">Current Attempt</td>
							<td>{{elt.attempt}}/{{elt.max_check_attempts}} ({{elt.state_type}} state)</td>
						</tr>
						<tr>		
							<td class="column1">Last Check Time</td>
							<td title='Last check was at {{time.asctime(time.localtime(elt.last_chk))}}'>was {{helper.print_duration(elt.last_chk)}}</td>
						</tr>
						<tr>		
							<td class="column1">Next Scheduled Active Check</td>
							<td title='Next active check at {{time.asctime(time.localtime(elt.next_chk))}}'>{{helper.print_duration(elt.next_chk)}}</td>
						</tr>
						<tr>		
							<td class="column1">Last State Change</td>
							<td>{{time.asctime(time.localtime(elt.last_state_change))}}</td>
						</tr>
					</table>
					<div>
						<a href="#" onclick="try_to_fix('{{elt.get_full_name()}}')">{{!helper.get_button('Try to fix it!', img='/static/images/enabled.png')}}</a>
						<a href="#" onclick="acknowledge('{{elt.get_full_name()}}')">{{!helper.get_button('Acknowledge it', img='/static/images/wrench.png')}}</a>
						<a href="#" onclick="recheck_now('{{elt.get_full_name()}}')">{{!helper.get_button('Recheck now', img='/static/images/delay.gif')}}</a>
						<a href="/depgraph/{{elt.get_full_name()}}" class="mb" title="Impact map of {{elt.get_full_name()}}">{{!helper.get_button('Show impact map', img='/static/images/state_ok.png')}}</a>
						{{!helper.get_button('Submit Check Result', img='/static/images/passiveonly.gif')}}
						{{!helper.get_button('Send Custom Notification', img='/static/images/notification.png')}}
						{{!helper.get_button('Schedule Downtime', img='/static/images/downtime.png')}}
					</div>
				</div>
				<hr />
				<div id="item_information">
					<h2>Additonal Informations</h2>
					<table>
						<tr>
							<td class="column1">Last Notification</td>
							<td>{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
						</tr>
						<tr>			
							<td class="column1">Check Latency / Duration</td>
							<td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
						</tr>
						<tr>
							<td class="column1">Is This Host Flapping?</td>
							<td>{{helper.yes_no(elt.is_flapping)}} ({{helper.print_float(elt.percent_state_change)}}% state change)</td>
						</tr>
						<tr>
							<td class="column1">In Scheduled Downtime?</td>
							<td>{{helper.yes_no(elt.in_scheduled_downtime)}}</td>
						</tr>
					</table>
				</div>
	        </div>
	        <!-- Tab Summary End-->
	        
	        <!-- Tab Service Start -->
	        <div id="services">Phasellus mattis tincidunt nibh. Cras orci urna, blandit id, pretium vel, aliquet ornare, felis. Maecenas scelerisque sem non nisl. Fusce sed lorem in enim dictum bibendum.
	        </div>
	        <!-- Tab Service End -->

	        <!-- Tab Comments Start -->
	        <div id="comments">
				<h2>Comments</h2>
				<div id="minimenu">
					<ul>
						<li> <a href="#" class="">Add Comments</a> </li>
						<li> <a onclick="delete_all_comments('{{elt.get_full_name()}}')" href="#" class="">Delete Comments</a> </li>
					</ul>
				</div>
			  	<div class="clear"></div>
									  
			 	<div id="log_container">
					%if len(elt.comments) > 0:
					<h2></h2>
					<ol>
						%for c in elt.comments:
						<li>
							<div class="left">
								<p class="log-text">{{c.comment}}</p>
								<div class="log-meta"> <span><b>Author:</b> {{c.author}}</span> <span><b>Creation:</b> {{helper.print_date(c.entry_time)}}</span> <span>	<b>Expire:</b>{{helper.print_date(c.expire_time)}}</span>
								</div>
							</div>
							<div class="right log-action"><a class="icon_delete" href="#">Delete</a></div>
						</li>
						%end
					</ol>
					%else:
						<p>No comments available</p>
					%end
				</div>
	        </div>
	        <!-- Tab Comments End -->

	        <!-- Tab Graph Start -->
	        <div id="graphs">
	           	<h2>Graphs</h2>
	       		%uris = app.get_graph_uris(elt, graphstart, graphend)
	      		%if len(uris) == 0:
	      			<p>No graphs, sorry</p>
				%else:
					<ul class="tabmenu">
						%now = int(time.time())
						%fourhours = now - 3600*4
						%lastday = now - 86400
						%lastweek = now - 86400*7
						%lastmonth = now - 86400*31
						%lastyear = now - 86400*365
						
						<li><a href="/{{elt_type}}/{{elt.get_full_name()}}?graphstart={{fourhours}}&graphend={{now}}#graphs" class="">4 hours</a></li>
						<li><a href="/{{elt_type}}/{{elt.get_full_name()}}?graphstart={{lastday}}&graphend={{now}}#graphs" class="">Day</a></li>
						<li><a href="/{{elt_type}}/{{elt.get_full_name()}}?graphstart={{lastweek}}&graphend={{now}}#graphs" class="">Week</a></li>
						<li><a href="/{{elt_type}}/{{elt.get_full_name()}}?graphstart={{lastmonth}}&graphend={{now}}#graphs" class="">Month</a></li>
						<li><a href="/{{elt_type}}/{{elt.get_full_name()}}?graphstart={{lastyear}}&graphend={{now}}#graphs" class="">Year</a></li>
					</ul>
				%end
								
				%for g in uris:
				%img_src = g['img_src']
				%link = g['link']
				<p><a href="{{link}}"><img src="{{img_src}}" class="graphimg"></img></a></p>
				moncul
				%end
	        </div>
	        <!-- Tab Graph End -->
		</div>
        <!--end tabs-->
</div>
%#  "Content Container End"

%#End of the Host Exist or not case
%end