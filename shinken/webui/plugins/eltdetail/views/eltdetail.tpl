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

%rebase layout title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(),  js=['eltdetail/js/functions.js','eltdetail/js/graphs.js', 'eltdetail/js/dollar.js'],  css=['eltdetail/css/eltdetail.css', 'eltdetail/css/hide.css', 'eltdetail/css/gesture.css'], top_right_banner_state=top_right_banner_state , user=user, app=app

%# " We will save our element name so gesture functions will be able to call for the good elements."
<script type="text/javascript">var elt_name = '{{elt.get_full_name()}}';</script>



%#  "Content Container Start"
<div id="content_container" class="span12 no-leftmargin">

	<h1 class="grid_16 state_{{elt.state.lower()}} icon_down"><img class="host_img_25" src="{{helper.get_icon_state(elt)}}" />{{elt.state}}: {{elt.get_full_name()}}</h1>

	<div class="span12 no-leftmargin box">	   
		<table class="span4 no-leftmargin">
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
		
		<table class="span3">
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

		<div class="span4">
		    %#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
		    %if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
			<div class="alert alert-critical no-bottommargin">
				<p>This element has got an important impact on your business, please <b>fix it</b> or <b>acknowledge it</b>.</p>
		    %# "end of the 'SOLVE THIS' highlight box"
		    %end
		    </div>
		</div>				
	</div>

	<!-- Switch Start -->
	<div class="switches span12">		
		<ul>
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

    <div class="tabbable">
	    <ul class="nav nav-tabs">
	    	<li class="active"><a href="#1" data-toggle="tab">Summary</a></li>
	    	<li><a href="#2" data-toggle="tab">Services</a></li>
	    	<li><a href="#3" data-toggle="tab">Comments / Downtimes</a></li>
	    	<li><a href="#4" data-toggle="tab">Graph</a></li>
	    </ul>
	    <div class="tab-content">
	    	<!-- Tab Summary Start-->
		    <div class="tab-pane active" id="1">
		    	<h3 class="span12">Host/Service Information</h3>
		    	<table class="span6 table table-striped table-bordered table-condensed">
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

			    <div class="btn-group span5">
			    %if elt_type=='host':
			    	<a class="btn dropdown-toggle" data-toggle="dropdown" href="#">Host Action <span class="caret"></span></a>
			    %else:
			    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">Service Action <span class="caret"></span></a>
			    %end:
				    <ul class="dropdown-menu">
				    	<li><a href="#">Action</a></li>
				    	<li><a href="#">Another action</a></li>
				    	<li><a href="#">Something else here</a></li>
				    	<li class="divider"></li>
				    	<li><a href="#">Separated link</a></li>
				    </ul>
			    </div>

				<h3 class="span12">Additonal Informations</h3>
				<table class="span6 table table-striped table-bordered table-condensed">
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
		    <!-- Tab Summary End-->

		    <!-- Tab Service Start -->
		    <div class="tab-pane" id="2">
	        	%# " Only print host service if elt is an host of course"
				%# " If the host is a problem, services will be print in the impacts, so don't"
				%# " print twice "
								
				%if elt_type=='host' and not elt.is_problem:
				<hr>
							
				<h3> Services </h3>
				%nb = 0
				%for s in helper.get_host_services_sorted(elt):
				%nb += 1
							
				%# " We put a max imapct to print, bacuse too high is just useless"
				%if nb > max_impacts:
				%break 
				%end
							
				%if nb == 8:
					<div style="float:right;" id="hidden_impacts_or_services_button"><a href="javascript:show_hidden_impacts_or_services()"> {{!helper.get_button('Show all services', img='/static/images/expand.png')}}</a></div>
				%end
									
				%if nb < 8:
					<div class="service">
				%else:
					<div class="service hidden_impacts_services">
				%end
					<div class="divstate{{s.state_id}}">
					%for i in range(0, s.business_impact-2):
						<img src='/static/images/star.png'>
					%end
						<img style="width : 16px; height:16px" src="{{helper.get_icon_state(s)}}">
						<span style="font-size:110%">{{!helper.get_link(s, short=True)}}</span> is <span style="font-size:110%">{{s.state}}</span> since {{helper.print_duration(s.last_state_change, just_duration=True, x_elts=2)}}
					</div>
						</div>
						%# End of this service
						%end
					</div>
							    
					%end #of the only host part			
							
					%if elt.is_problem and len(elt.impacts) != 0:
					<div>
								
					<h4 style="margin-bottom: 5px;"> Impacts </h4>
						%nb = 0
						%for i in helper.get_impacts_sorted(elt):
						%nb += 1
						%if nb == 8:	
							<div style="float:right;" id="hidden_impacts_or_services_button"><a href="javascript:show_hidden_impacts_or_services()"> {{!helper.get_button('Show all impacts', img='/static/images/expand.png')}}</a></div>
						%end
						%if nb < 8:
						 	<div class="service">
						%else:
							<div class="service hidden_impacts_services">
						%end
							        
							<div class="divstate{{i.state_id}}">
								%for j in range(0, i.business_impact-2):
									<img src='/static/images/star.png'>
								%end
									<img style="width : 16px; height:16px" src="{{helper.get_icon_state(i)}}">
									<span style="font-size:110%">{{!helper.get_link(i)}}</span> is <span style="font-size:110%">{{i.state}}</span> since {{helper.print_duration(i.last_state_change, just_duration=True, x_elts=2)}}
								</div>
							    </div>
							    %# End of this impact
							    %end
							</div>
						%# end of the 'is problem' if
						%end
		    </div>
		    <!-- Tab Service End -->

		    <!-- Tab Comments and Downtimes Start -->
		    <div class="tab-pane" id="3">
				<div>
					<ul class="nav nav-pills">
						<li class="active"> <a href="#" class="">Add Comments</a> </li>
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
			<!-- Tab Comments and Downtimes End -->

			<!-- Tab Graph Start -->
			<div class="tab-pane" id="4">
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
	   
    </div>

%#End of the Host Exist or not case
%end