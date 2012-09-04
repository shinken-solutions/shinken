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

%# Look for actions if we must show them or not
%global_disabled = ''
%if app.manage_acl and not helper.can_action(user):
%global_disabled = 'disabled-link'
%end


%rebase layout title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(), js=['eltdetail/js/jquery.color.js', 'eltdetail/js/jquery.Jcrop.js', 'eltdetail/js/iphone-style-checkboxes.js', 'eltdetail/js/hide.js', 'eltdetail/js/dollar.js', 'eltdetail/js/gesture.js', 'eltdetail/js/graphs.js', 'eltdetail/js/tags.js', 'eltdetail/js/depgraph.js'], css=['eltdetail/css/iphonebuttons.css_', 'eltdetail/css/eltdetail.css', 'eltdetail/css/hide.css', 'eltdetail/css/gesture.css', 'eltdetail/css/jquery.Jcrop.css'], top_right_banner_state=top_right_banner_state , user=user, app=app, refresh=True

%# " We will save our element name so gesture functions will be able to call for the good elements."
<script type="text/javascript">
var elt_name = '{{elt.get_full_name()}}';

var graphstart={{graphstart}};
var graphend={{graphend}};

/* Now hide canvas */
$(document).ready(function(){
	$('#gesture_panel').hide();

    // Also hide the button under IE (gesture don't work under it)
    if (navigator.appName == 'Microsoft Internet Explorer'){
    	$('#btn_show_gesture').hide();
    }
});

/* Look at the # part of the URI. If it match a nav name, go for it*/
$(document).ready(function(){
	if (window.location.hash.length > 0) {
		$('ul.nav-tabs > li > a[href="' + window.location.hash + '"]').tab('show');
	}else{
		$('ul.nav-tabs > li > a:first').tab('show');
	}
});

  // Now we hook the global search thing
  $('.typeahead').typeahead({
    // note that "value" is the default setting for the property option
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

  %#  "Content Container Start"
  <!--<div class="">-->
  <div id="content_container" class="span12">
  	<h1 class="span6 no-leftmargin state_{{elt.state.lower()}} icon_down"> <img class="imgsize3" alt="icon state" src="{{helper.get_icon_state(elt)}}" />{{elt.state}}: {{elt.get_full_name()}}</h1> 

	<div class="span6 no-leftmargin">
		<span class="pull-right leftmargin" id="host_tags">
			%tags = elt.get_host_tags()
			%for t in tags:
			<script>add_tag_image('/static/images/sets/{{t.lower()}}/tag.png','{{t}}');</script>
			%end
		</span>

	  	%if elt.action_url != '':
	    	%action_urls = elt.action_url.split('|')
			%if len(action_urls) > 0:
				%for triplet in action_urls:
					%if len(triplet.split(',')) == 3:
						%( action_url, icon, alt) = triplet.split(',')
						<a href="{{action_url}}" target=_blank><img src={{icon}} alt="{{alt}}"></a>
					%else:
						%if len(triplet.split(',')) == 1:
							<a href="{{triplet}}" target=_blank><button class="btn btn-mini pull-right" type="button"><i class="icon-cog"></i></button></a>
						%end
					%end
				%end
			%end
	  	%end
	</div>

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
				<td>Notes: </td>
				%if elt.notes != '' and elt.notes_url != '':
				<td><a href="{{elt.notes_url}}" target=_blank>{{elt.notes}}</a></td>
				%elif elt.notes == '' and elt.notes_url != '':
				<td><a href="{{elt.notes_url}}" target=_blank>{{elt.notes_url}}</a></td>
				%elif elt.notes != '' and elt.notes_url == '':
				<td>{{elt.notes}}</td>
				%else:
				<td>(none)</td>
				%end
			</tr>
		</table>	    

		<div class="span4">
			%#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
			%if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
			<div class="alert alert-critical no-bottommargin pulsate">
				<p>This element has got an important impact on your business, please <b>fix it</b> or <b>acknowledge it</b>.</p>
				%# "end of the 'SOLVE THIS' highlight box"
				%end
			</div>
		</div>				
	</div>

	<!-- Switch Start -->

	%# By default all is unabled
	% chk_state = not_state =  evt_state = flp_state = 'checked=""'
	%if not (elt.active_checks_enabled|elt.passive_checks_enabled):
	%chk_state = 'unchecked=""'
	%end
	%if not elt.notifications_enabled:
	%not_state = 'unchecked=""'
	%end
	%if not elt.event_handler_enabled:
	%evt_state = 'unchecked=""'
	%end
	%if not elt.flap_detection_enabled:
	%flp_state = 'unchecked=""'
	%end

	<script type="text/javascript">
	$(document).ready(function() {
		$('#btn-checks').iphoneStyle({
			resizeContainer: false,
			resizeHandle: false,
			onChange : function(elt, b){toggle_checks("{{elt.get_full_name()}}", !b);}
		}
		);

		$('#btn-not').iphoneStyle({
			resizeContainer: false,
			resizeHandle: false,
			onChange : function(elt, b){toggle_notifications("{{elt.get_full_name()}}", !b);}
		}
		);

		$('#btn-evt').iphoneStyle({
			resizeContainer: false,
			resizeHandle: false,
			onChange : function(elt, b){toggle_event_handlers("{{elt.get_full_name()}}", !b);}
		}
		);

		$('#btn-flp').iphoneStyle({
			resizeContainer: false,
			resizeHandle: false,
			onChange : function(elt, b){toggle_flap_detection("{{elt.get_full_name()}}", !b);}

		}
		);
	}); 
	</script>

	<!-- Le Anfang -->
	<div class="span12">
		<!-- Start Host/Services-->
		<div class="tabbable verticaltabs-container span3 no-leftmargin"> <!-- Wrap the Bootstrap Tabs/Pills in this container to position them vertically -->
			<ul class="nav nav-tabs">
				<li class="active"><a href="#basic" data-toggle="tab">{{elt_type.capitalize()}} Information:</a></li>
				<li><a href="#additonal" data-toggle="tab">Additonal Informations:</a></li>
				<li><a href="#commands" data-toggle="tab">Commands:</a></li>
				<li><a href="#gesture" data-toggle="tab">Gesture:</a></li>
			</ul>

			<div class="tab-content">
				<div class="tab-pane fade in active" id="basic">
					%if elt_type=='host':
					<h3>Host Information:</h3>
					%else:
					<h3>Service Information:</h3>
					%end:

					<script type="text/javascript">
					$().ready(function() {
						$('.truncate').jTruncate({
							length: 85,
							minTrail: 0,
							moreText: "[see all]",
							lessText: "[hide extra]",
							ellipsisText: " (truncated)",
							moreAni: "fast",
							lessAni: 2000
						});
					});
					</script>

					<table class="table">
						<tr>
							<td class="column1"><b>Status:</b></td>
							<td><span class="btn span11 alert-small alert-{{elt.state.lower()}} quickinforight" data-original-title="since {{helper.print_duration(elt.last_state_change, just_duration=True, x_elts=2)}}">{{elt.state}}</span> </td>
						</tr>
						<tr>
							<td class="column1"><b>Flapping:</b></td>
							<td><span class="btn alert-small trim-{{helper.yes_no(elt.in_scheduled_downtime)}} span11" quickinfo="{{helper.print_float(elt.percent_state_change)}}% state change">{{helper.yes_no(elt.is_flapping)}}</span></td>
						</tr>
						<tr>
							<td class="column1"><b>In Scheduled Downtime?</b></td>
							<td><span class="btn span11 alert-small trim-{{helper.yes_no(elt.in_scheduled_downtime)}}">{{helper.yes_no(elt.in_scheduled_downtime)}}</span></td>
						</tr>
					</table>
					<hr>
					<div class="truncate"> <b><i>{{elt.output}}</i></b> </div>
					<hr>
					<table class="table">
						<tr>
							<td class="column1"><b>Last Check:</b></td>
							<td><span class="quickinfo" data-original-title='Last check was at {{time.asctime(time.localtime(elt.last_chk))}}'>was {{helper.print_duration(elt.last_chk)}}</span></td>
						</tr>
						<tr>		
							<td class="column1"><b>Last State Change</b></td>
							<td>{{time.asctime(time.localtime(elt.last_state_change))}}</td>
						</tr>
						<tr>										
							<td class="column1"><b>Current Attempt</b></td>
							<td>{{elt.attempt}}/{{elt.max_check_attempts}} ({{elt.state_type}} state)</td>
						</tr>
						<tr>		
							<td class="column1"><b>Next Active Check:</b></td>
							<td><span class="quickinfo" data-original-title='Next active check at {{time.asctime(time.localtime(elt.next_chk))}}'>{{helper.print_duration(elt.next_chk)}}</span></td>
						</tr>
					</table>
				</div>

				<div class="tab-pane fade" id="additonal">
					<script type="text/javascript">
					$().ready(function() {
						$('.truncate_perf').jTruncate({
							length: 50,
							minTrail: 0,
							moreText: "[see all]",
							lessText: "[hide extra]",
							ellipsisText: " <b>(truncated)</b>",
							moreAni: "fast",
							lessAni: 2000
						});
					});
					</script>

					<h3>Additonal Informations</h3>
					<table class="table tabletop">
						<tbody class="tabletop">
						<tr class="tabletop">
							<td class="column1"><b>Performance Data</b></td>
							%# "If there any perf data?"
							%if len(elt.perf_data) > 0:
							<td class="column2 truncate_perf">{{elt.perf_data}}</td>
							%else:
							<td class="column2 truncate_perf">&nbsp;</td>
							%end
						</tr>
						<tr>			
							<td class="column1"><b>Check Latency / Duration</b></td>
							<td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
						</tr>
						<tr>			
							<td class="column1"><b>Last Notification</b></td>
							<td class="column2">{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
						</tr>
						<tr>
							<td class="column1"><b>Current Attempt</b></td>
							<td class="column2">{{elt.attempt}}/{{elt.max_check_attempts}} ({{elt.state_type}} state)</td>
						</tr>
						</tbody>
					</table>
					<hr>
					<table class="table">
						<tr>
							<td class="column1"><b>Active/passive checks</b></td>
							<td><input {{chk_state}} class="iphone" type="checkbox" id='btn-checks'></td>
						</tr>
						<tr>		
							<td class="column1"><b>Notifications</b></td>
							<td><input {{not_state}} class="iphone" type="checkbox" id='btn-not'></td>
						</tr>
						<tr>			
							<td class="column1"><b>Event handler</b></td>
							<td><input {{evt_state}} class="iphone" type="checkbox" id='btn-evt'></td>
						</tr>
						<tr>
							<td class="column1"><b>Flap detection</b></td>
							<td><input {{flp_state}} class="iphone" type="checkbox" id='btn-flp'></td>
						</tr>
					</table>
				</div>

				<div class="tab-pane fade" id="commands">
					<h3>Commands</h3>
					<div>
						<ul style="padding-top:5px" class="nav nav-list">
							%disabled_s = ''
							%if not elt.event_handler:
							%disabled_s = 'disabled-link'
							%end
							<li><a class='{{disabled_s}} {{global_disabled}}' href="javascript:try_to_fix('{{elt.get_full_name()}}')"><i class="icon-pencil"></i> Try to fix it!</a></li>
							%disabled_s = ''
							%if elt.problem_has_been_acknowledged:
							%disabled_s = 'disabled-link'
							%end
							<li><a class='{{disabled_s}} {{global_disabled}}' href="/forms/acknowledge/{{helper.get_uri_name(elt)}}" data-toggle="modal" data-target="#modal"> <img src="/static/img/icons/atwork.png" alt="atwork" height="15" width="17" /> Acknowledge it!</a></li>
							<li><a class='{{global_disabled}}' href="javascript:recheck_now('{{elt.get_full_name()}}')"><i class="icon-repeat"></i> Recheck now</a></li>
							<li><a class='{{global_disabled}}' href="/forms/submit_check/{{helper.get_uri_name(elt)}}" data-toggle="modal" data-target="#modal"><i class="icon-share-alt"></i> Submit Check Result</a></li>
							<li><a class='disabled-link {{global_disabled}}' href="#"><i class="icon-comment"></i> Send Custom Notification</a></li>
							<li><a class='{{global_disabled}}' href="/forms/downtime/{{helper.get_uri_name(elt)}}" data-toggle="modal" data-target="#modal"><i class="icon-fire"></i> Schedule Downtime</a></li>
							<li class="divider"></li>
							<li><a class='disabled-link' href="#"><i class="icon-edit"></i> Edit {{elt_type.capitalize()}}</a></li>
						</ul>
				    </div>
				</div>

				<div class="tab-pane fade" id="gesture">
					<h3>Gesture</h3>
					<canvas id="canvas" width="100" height="200" class="grid_10" style="border: 1px solid black;"></canvas>
					<div class="gesture_button">
						<img title="By keeping a left click pressed and drawing a check, you will launch an acknowledgement." alt="gesture acknowledge" src="/static/eltdetail/images/gesture-check.png"/> Acknowledge
					</div>
					<div class="gesture_button">
						<img title="By keeping a left click pressed and drawing a check, you will launch an recheck." alt="gesture recheck" src="/static/eltdetail/images/gesture-circle.png"/> Recheck
					</div>
					<div class="gesture_button">
						<img title="By keeping a left click pressed and drawing a check, you will launch a try to fix command." alt="gesture fix" src="/static/eltdetail/images/gesture-zigzag.png"/> Fix
					</div>
				</div>
			</div>
		</div>

		<!-- Detail info box start -->
		<div class="span9 tabbable no-leftmargin">
			<ul class="nav nav-tabs">
				<li class="active"><a href="#impacts" data-toggle="tab">Impacts</a></li>
				<li><a href="#comments" data-toggle="tab">Comments</a></li>
				<li><a href="#downtimes" data-toggle="tab">Downtimes</a></li>
				<li><a href="#graphs" data-toggle="tab" id='tab_to_graphs'>Graphs</a></li>
				<li><a href="#depgraph" data-toggle="tab" id='tab_to_depgraph'>Impact graph</a></li>
				<!--<li><a href="/depgraph/{{elt.get_full_name()}}" title="Impact map of {{elt.get_full_name()}}">Impact map</a></li> -->
			</ul>
			<div class="tab-content">
				<!-- Tab Summary Start-->
				<div class="tab-pane active" id="impacts">
		      <!-- Start of the Whole info pack. We got a row of 2 thing : 
		      left is information, right is related elements -->
		      <div class="row-fluid">
		      	<!-- So now it's time for the right part, replaceted elements -->
		      	<div class="span12">

		      		<!-- Show our father dependencies if we got some -->
		      		%#    Now print the dependencies if we got somes
		      		%if len(elt.parent_dependencies) > 0:
		      		<h3 class="span10">Root cause:</h3>
		      		<a id="togglelink-{{elt.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{elt.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
		      		<div class="clear"></div>
		      		{{!helper.print_business_rules(datamgr.get_business_parents(elt), source_problems=elt.source_problems)}}

		      		%end

		      		<!-- If we are an host and not a problem, show our services -->
		      		%# " Only print host service if elt is an host of course"
		      		%# " If the host is a problem, services will be print in the impacts, so don't"
		      		%# " print twice "
		      		%if elt_type=='host' and not elt.is_problem:
		      		%if len(elt.services) > 0:
		      		<h3 class="span10">My services:</h3>
		      		%elif len(elt.parent_dependencies) == 0:
		      		<h3 class="span10">No services</h3>
		      		%end
		      		<hr>
		      		<div class='host-services'>
		      			%nb = 0
		      			%for s in helper.get_host_services_sorted(elt):
		      			%nb += 1

		      			%# " We put a max imapct to print, bacuse too high is just useless"
		      			%if nb > max_impacts:
		      			%   break
		      			%end

		      			%if nb == 8:
		      			<div style="float:right;" id="hidden_impacts_or_services_button"><a href="javascript:show_hidden_impacts_or_services()"> {{!helper.get_button('Show all services', img='/static/images/expand.png')}}</a></div>
		      			%end

		      			%if nb < 8:
		      			<div class="service">
		      				%else:
		      				<div class="service hidden_impacts_services">
		      					%end
		      					<div>
		      						<img style="width : 16px; height:16px" alt="icon state" src="{{helper.get_icon_state(s)}}">
		      						<span class='alert-small alert-{{s.state.lower()}}' style="font-size:110%">{{s.state}}</span> for <span style="font-size:110%">{{!helper.get_link(s, short=True)}}</span> since {{helper.print_duration(s.last_state_change, just_duration=True, x_elts=2)}}
		      						%for i in range(0, s.business_impact-2):
		      						<img alt="icon state" src="/static/images/star.png">
		      						%end

		      					</div>
		      				</div>
		      				%# End of this service
		      				%end
		      			</div>
		      			%end #of the only host part


		      			<!-- If we are a root problem and got real impacts, show them! -->
		      			%if elt.is_problem and len(elt.impacts) != 0:
		      			<h3 class="span10">My impacts:</h3>
		      			<div class='host-services'>
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

		      						<div>
		      							<img style="width : 16px; height:16px" alt="icon state" src="{{helper.get_icon_state(i)}}">
		      							<span class='alert-small alert-{{i.state.lower()}}' style="font-size:110%">{{i.state}}</span> for <span style="font-size:110%">{{!helper.get_link(i, short=True)}}</span> since {{helper.print_duration(i.last_state_change, just_duration=True, x_elts=2)}}
		      							%for i in range(0, i.business_impact-2):
		      							<img alt="icon state" src="/static/images/star.png">
		      							%end

		      						</div>
		      					</div>
		      					%# End of this impact
		      					%end
		      				</div>
		      				%# end of the 'is problem' if
		      				%end



		      			</div><!-- End of the right part -->

		      		</div>
		      		<!-- End of the row with the 2 blocks-->
		      	</div>
		      	<!-- Tab Summary End-->

		      	<!-- Tab Comments Start -->
		      	<div class="tab-pane" id="comments">
		      		<div>
		      			<ul class="nav nav-pills">
		      				<li class="active"><a class='{{global_disabled}}' href="/forms/comment/{{helper.get_uri_name(elt)}}" data-toggle="modal" data-target="#modal"><i class="icon-plus"></i> Add comment</a></li>
		      				<li> <a class='{{global_disabled}}' onclick="delete_all_comments('{{elt.get_full_name()}}')" href="#" class=""><i class="icon-minus"></i> Delete all comments</a> </li>
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
		      					<div class="right log-action"><a class="icon_delete {{global_disabled}}" href="javascript:delete_comment('{{elt.get_full_name()}}', {{c.id}})">Delete</a></div>
		      				</li>
		      				%end
		      			</ol>
		      			%else:
		      			<p>No comments available</p>
		      			%end
		      		</div>
		      	</div>
		      	<!-- Tab Comments End -->


		      	<!-- Tab Downtimes Start -->
		      	<div class="tab-pane" id="downtimes">
		      		<div>
		      			<ul class="nav nav-pills">
		      				<li class="active"><a class='{{global_disabled}}' href="/forms/downtime/{{helper.get_uri_name(elt)}}" data-toggle="modal" data-target="#modal"><i class="icon-plus"></i> Add a downtime</a></li>
		      				<li> <a onclick="delete_all_downtimes('{{elt.get_full_name()}}')" href="#" class="{{global_disabled}}"><i class="icon-minus"></i> Delete all downtimes</a> </li>
		      			</ul>
		      		</div>
		      		<div class="clear"></div>

		      		<div id="log_container">
		      			%if len(elt.downtimes) > 0:
		      			<h2></h2>
		      			<ol>
		      				%for dt in elt.downtimes:
		      				<li>
		      					<div class="left">
		      						<p class="log-text">{{dt.comment}}</p>
		      						<div class="log-meta"> <span><b>Author:</b> {{dt.author}}</span> <span><b>Start:</b> {{helper.print_date(dt.start_time)}}</span> <span>	<b>Expire:</b>{{helper.print_date(dt.end_time)}}</span>
		      						</div>
		      					</div>
		      					<div class="right log-action"><a class="icon_delete {{global_disabled}}" href="javascript:delete_downtime('{{elt.get_full_name()}}', {{dt.id}})">Delete</a></div>
		      				</li>
		      				%end
		      			</ol>
		      			%else:
		      			<p>No downtime planned.</p>
		      			%end
		      		</div>
		      	</div>
		      	<!-- Tab Comments and Downtimes End -->


		      	<!-- Tab Graph Start -->
		      	<div class="tab-pane" id="graphs">
		      		%uris = app.get_graph_uris(elt, graphstart, graphend)
		      		%if len(uris) == 0:
		      		<h3>No graphs, sorry</h3>
		      		%else:
		      		<h3>Graphs</h3>
		      		<div class='row-fluid well span6'>

		      			<!-- Get the uris for the 4 standard time ranges in advance	 -->
		      			%now = int(time.time())
		      			%fourhours = now - 3600*4
		      			%lastday =   now - 86400
		      			%lastweek =  now - 86400*7
		      			%lastmonth = now - 86400*31
		      			%lastyear =  now - 86400*365

		      			%# Let's get all the uris at once.
		      			%uris_4h = app.get_graph_uris(elt, fourhours, now)
		      			%uris_1d = app.get_graph_uris(elt, lastday, now)
		      			%uris_1w = app.get_graph_uris(elt, lastweek, now)
		      			%uris_1m = app.get_graph_uris(elt, lastmonth, now)
		      			%uris_1y = app.get_graph_uris(elt, lastyear, now)

		      			<!-- Use of javascript to change the content of a div!-->										
		      			<div class='span2'><a onclick="setHTML(html_4h,{{fourhours}});" class=""> 4 hours</a></div>
		      			<div class='span2'><a onclick="setHTML(html_1d,{{lastday}});" class=""> 1 day</a></div>
		      			<div class='span2'><a onclick="setHTML(html_1w,{{lastweek}});" class=""> 1 week</a></div>
		      			<div class='span2'><a onclick="setHTML(html_1m,{{lastmonth}});" class=""> 1 month</a></div>
		      			<div class='span2'><a onclick="setHTML(html_1y,{{lastyear}});" class=""> 1 year</a></div>


		      		</div>

		      		<script langage="javascript">
		      		function setHTML(html,start) {
		      			<!-- change the content of the div --!>
		      			document.getElementById("real_graphs").innerHTML=html;

		      			<!-- and call the jcrop javascript --!>
		      			$('.jcropelt').Jcrop({
		      				onSelect: update_coords,
		      				onChange: update_coords
		      			});
		      			graphstart=start;
		      			get_range();
		      		}

		      		<!-- let's create the html content for each time rand --!>
		      		<!-- This is quite ugly here. I do the same thing 4 times --!->
		      		<!-- someone said "function" ? You're right.--!>
		      		<!-- but the mix between python and javascript is not a easy thing for me --!>
		      		html_4h='<p>';
		      		html_1d='<p>';
		      		html_1w='<p>';
		      		html_1m='<p>';
		      		html_1y='<p>';

		      		%for g in uris_4h:
		      		%img_src = g['img_src']
		      		%link = g['link']
		      		var img_src="{{img_src}}";
		      		html_4h = html_4h + '<img src="'+ img_src.replace("'","\'") +'" class="jcropelt"/>';
		      		html_4h = html_4h + '<a href="{{link}}" class="btn"><i class="icon-plus"></i> Show more</a>';
		      		html_4h = html_4h + '<a href="javascript:graph_zoom(\'/{{elt_type}}/{{elt.get_full_name()}}?\')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>';
		      		html_4h = html_4h + '<br>';
		      		%end
		      		html_4h=html_4h+'</p>';

		      		%for g in uris_1d:
		      		%img_src = g['img_src']
		      		%link = g['link']
		      		var img_src="{{img_src}}";
		      		html_1d = html_1d +'<img src="'+ img_src.replace("'","\'") +'" class="jcropelt"/>';
		      		html_1d = html_1d + '<a href={{link}}" class="btn"><i class="icon-plus"></i> Show more</a>';
		      		html_1d = html_1d + '<a href="javascript:graph_zoom(\'/{{elt_type}}/{{elt.get_full_name()}}?\')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>';
		      		html_1d = html_1d + '<br>';
		      		%end
		      		html_1d=html_1d+'</p>';

		      		%for g in uris_1w:
		      		%img_src = g['img_src']
		      		%link = g['link']
		      		var img_src="{{img_src}}";
		      		html_1w = html_1w + '<img src="'+ img_src.replace("'","\'") +'" class="jcropelt"/>';
		      		html_1w = html_1w + '<a href="{{link}}" class="btn"><i class="icon-plus"></i> Show more</a>';
		      		html_1w = html_1w + '<a href="javascript:graph_zoom(\'/{{elt_type}}/{{elt.get_full_name()}}?\')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>';
		      		html_1w = html_1w + '<br>';
		      		%end

		      		%for g in uris_1m:
		      		%img_src = g['img_src']
		      		%link = g['link']
		      		var img_src="{{img_src}}";
		      		html_1m = html_1m + '<img src="'+ img_src.replace("'","\'") +'" class="jcropelt"/>';
		      		html_1m = html_1m + '<a href="{{link}}" class="btn"><i class="icon-plus"></i> Show more</a>';
		      		html_1m = html_1m + '<a href="javascript:graph_zoom(\'/{{elt_type}}/{{elt.get_full_name()}}?\')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>';
		      		html_1m = html_1m + '<br>';
		      		%end

		      		%for g in uris_1y:
		      		%img_src = g['img_src']
		      		%link = g['link']
		      		var img_src="{{img_src}}";
		      		html_1y = html_1y + '<img src="'+ img_src.replace("'","\'") +'" class="jcropelt"/>';
		      		html_1y = html_1y + '<a href="{{link}}" class="btn"><i class="icon-plus"></i> Show more</a>';
		      		html_1y = html_1y + '<a href="javascript:graph_zoom(\'/{{elt_type}}/{{elt.get_full_name()}}?\')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>';
		      		html_1y = html_1y + '<br>';
		      		%end


		      		</script>

		      		<div class='row-fluid well span8 jcrop'>
		      			<div id='real_graphs'>
    			  <!-- Let's keep this part visible. This is the custom and default range --!>
				    %for g in uris:
				      %img_src = g['img_src']
				      %link = g['link']
				      <p>
						
				        <img src="{{img_src}}" class="jcropelt"/>
				        <a href="{{link}}" class="btn"><i class="icon-plus"></i> Show more</a>
				        <a href="javascript:graph_zoom('/{{elt_type}}/{{elt.get_full_name()}}?')" class="btn"><i class="icon-zoom-in"></i> Zoom</a>
                      </p>
                      
					%end      
					
				  </div>
				</div>
				%end
			</div>
			<!-- Tab Graph End -->


			<!-- Tab Dep graph Start -->
			<div class="tab-pane" id="depgraph">
				<div id='inner_depgraph' data-elt-name='{{elt.get_full_name()}}'>
					<span class='alert alert-error'> Cannot load dependency graph.</span>
				</div>
			</div>
			<!-- Tab Dep graph End -->
		</div>
		<!-- Detail info box end -->
	</div>
	<!-- Le Ende -->
	<!--</div>-->
</div>

</div>
%#End of the Host Exist or not case
%end

<script>
/*$(document).ready(function(){
    $('#inner_depgraph').load('/inner/depgraph/{{elt.get_full_name()}}');
});*/
</script>
