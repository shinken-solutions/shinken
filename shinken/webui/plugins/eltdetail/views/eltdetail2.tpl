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


%rebase layout title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(),  js=['eltdetail/js/graphs.js','eltdetail/js/TabPane.js', 'eltdetail/js/gesture.js'],  css=['eltdetail/css/eltdetail2.css', 'eltdetail/css/gesture.css'], top_right_banner_state=top_right_banner_state , user=user, app=app


%#  "This is the background canvas for all gesture detection things " 
<canvas id="canvas"></canvas>
%# " We will save our element name so gesture functions will be able to call for the good elements."
<script type="text/javascript">var elt_name = '{{elt.get_full_name()}}';</script>

%#  "Left Container Start"
<div id="left_container" class="grid_3">
  

</div>
%#  "Left Container End"

%#  "Content Container Start"
<div id="content_container" class="grid_13">
	<h1 class="grid_16 state_{{elt.state.lower()}} icon_down">{{elt.state}}: {{elt.get_full_name()}}</h1>
	<div id="overview_container" class="grid_16">
		<dl class="grid_4">
		%#Alias, Parents and Hostgroups are for host only
      	%if elt_type=='host':
			<dt>Alias:</dt>
			<dd>{{elt.alias}}</dd>
	
			<dt>Address:</dt>
			<dd>{{elt.address}}</dd>				
			
			<dt>Parents:</dt>
			%if len(elt.parents) > 0:
			<dd>{{','.join([h.get_name() for h in elt.parents])}}</dd>
			%else:
			<dd>No Parents</dd>
			%end
			
			%# End of the host only case, so now service
    		%else:
	 		<dt>Host:</dt>
         	<dd> {{elt.host.host_name}}</dd>
    	%end 
		</dl>
		<dl class="grid_4">
					<dt>Members of:</dt>
			%if len(elt.hostgroups) > 0:	
			<dd>{{','.join([hg.get_name() for hg in elt.hostgroups])}}</dd>
			%else:
			<dd>No Hostgroups</dd>
			%end
			
			<dt>Notes:</dt>
			%if elt.notes != '':
      		<dd>{{elt.notes}}</dd>
      		%else:
      		<dd>(none)</dd>
      		%end
					
			<dt>Importence:</dt>
			<dd>{{!helper.get_business_impact_text(elt)}}</dd>
		</dl>
		<div class="grid_8">
		    %#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
		    %if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
			<p class="error">This element has got an important impact on your business, please fix it or acknowledge it.</p>
		    %# "end of the 'SOLVE THIS' highlight box"
		    %end
		</div>				
	</div>
		<div id="elt_container">

		<script type="text/javascript">
			document.addEvent('domready', function() {
			var tabPane = new TabPane('demo');
					
			   $('demo').addEvent('click:relay(.remove)', function(e) {
			     new Event(e).stop();
			     var parent = this.getParent('.tab');
			     var index = $('demo').getElements('.tab').indexOf(parent);
			     tabPane.closeTab(index);
			   });
					
			    $('new-tab').addEvent('click', function() {
			       var title = $('new-tab-title').get('value');
			       var content = $('new-tab-content').get('value');
				
			       if (!title || !content) {
				       window.alert('Title or content text empty, please fill in some text.');
				       return;
				   }
					
				 $('demo').getElement('ul').adopt(new Element('li', {'class': 'tab', text: title}).adopt(new Element('span', {'class': 'remove', html: '&times'})));
				 $('demo').adopt(new Element('div', {'class': 'content', text: content}).setStyle('display', 'none'));
				});
		     });
		</script>

		<div id="demo" class="grid_16">
						    <ul class="tabs">
						        <li class="tab icon_summary">Summary</li>
						        <li class="tab icon_service">Services</li>
						        <li class="tab icon_comment">Comments/Downtimes</li>
						        <li class="tab icon_dependency ">Dependency Cloud</li>
						        <li class="tab icon_graph">Graphs</li>
						    </ul>
						    <div class="content">
						   <div id="elt_summary">
								<div id="item_information">
									<h2>Host/Service Information</h2>
									<table>
										<tbody>
											<tr>
												<th scope="row" class="column1">{{elt_type.capitalize()}} Status</th>
												<td><span class="state_{{elt.state.lower()}}">{{elt.state}}</span> (since {{helper.print_duration(elt.last_state_change, just_duration=True, x_elts=2)}}) </td>
											</tr>
											<tr class="odd">
												<th scope="row" class="column1">Status Information</th>
												<td>{{elt.output}}</td>
											</tr>
											<tr>
												<th scope="row" class="column1">Performance Data</th>
												<td>{{elt.perf_data}}</td>
											</tr>
											<tr class="odd">
												<th scope="row" class="column1">Current Attempt</th>
												<td>{{elt.attempt}}/{{elt.max_check_attempts}} ({{elt.state_type}} state)</td>
											</tr>
											<tr>
												<th scope="row" class="column1">Last Check Time</th>
												<td title='Last check was at {{time.asctime(time.localtime(elt.last_chk))}}'>was {{helper.print_duration(elt.last_chk)}}</td>
											</tr>
				
											<tr class="odd">
												<th scope="row" class="column1">Next Scheduled Active Check</th>
												<td title='Next active check at {{time.asctime(time.localtime(elt.next_chk))}}'>{{helper.print_duration(elt.next_chk)}}</td>
											</tr>
											<tr>
												<th scope="row" class="column1">Last State Change</th>
												<td>{{time.asctime(time.localtime(elt.last_state_change))}}</td>
											</tr>
										</tbody>
									</table>
								</div>
								<hr />
								<div id="item_information">
								<h2>Additonal Informations</h2>
									<table>
										<tbody>
											<tr>
												<th scope="row" class="column1">Last Notification</th>
												<td>{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
											</tr>
											<tr>
												<th scope="row" class="column1">Check Latency / Duration</th>
												<td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
											</tr>
											<tr>
												<th scope="row" class="column1">Is This Host Flapping?</th>
												<td>{{helper.yes_no(elt.is_flapping)}} ({{helper.print_float(elt.percent_state_change)}}% state change)</td>
											</tr>
											<tr>
												<th scope="row" class="column1">In Scheduled Downtime?</th>
												<td>{{helper.yes_no(elt.in_scheduled_downtime)}}</td>
											</tr>
											
										</tbody>
									</table>
								</div>
							</div>
		
						    </div>
						    <div class="content">
						     
	   
								%#    Now print the dependencies if we got somes
								%if len(elt.parent_dependencies) > 0:
									<a id="togglelink-{{elt.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{elt.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
							      
							      		{{!helper.print_business_rules(datamgr.get_business_parents(elt))}}
								%end
							
								%# " Only print host service if elt is an host of course"
								%# " If the host is a problem, services will be print in the impacts, so don't"
								%# " print twice "
								
								%if elt_type=='host' and not elt.is_problem:
							        <hr>
							
							        <div class='host-services'>
									<h3> Services </h3>
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
								<div class='host-services'>
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
						    <div class="content">
						       	<div class="tabcontent">
									<h2 style="display: none"><a name="comment" id="comment">Comments</a></h2>
										<div id="minimenu">
											<ul>
												<li>
													<a href="#" class="">Add Comments</a>
												</li>
												<li>
													<a onclick="delete_all_comments('{{elt.get_full_name()}}')" href="#" class="">Delete Comments</a>
												</li>
											</ul>
										</div>
									  <div class="clear"></div>
									%if len(elt.comments) > 0:
									  <table>
									    <tr>
									      <td class="tdBorderLeft tdCriticity" style="width:30px;"><b>Author</b></td>
									      <td class="tdBorderLeft tdCriticity" style="width:350px;"><b>Comment</b></td>
									      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>Creation</b></td>
									      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>Expire</b></td>
									      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>Delete</b></td>
									    </tr>
									    %for c in elt.comments:
									    <tr>
									      <td class="tdBorderTop tdCriticity" >{{c.author}}</td>
									      <td class="tdBorderTop tdBorderLeft tdBorderLeft tdCriticity" >{{c.comment}}</td>
									      <td class="tdBorderTop tdBorderLeft tdCriticity">{{helper.print_date(c.entry_time)}}</td>
									      <td class="tdBorderTop tdBorderLeft tdCriticity">{{helper.print_date(c.expire_time)}}</td>
									      <td class="tdBorderTop tdBorderLeft tdCriticity"><a href="#" onclick="delete_comment('{{elt.get_full_name()}}', '{{c.id}}')"><img src="/static/images/delete.png"/></a></td>
									    </tr>
									    %end
									  </table>
									%else:
									  <p>No comments available</p>
									%end
								</div>
						    </div>
						    <div class="content">
						        Lorem Ipsum ....
						    </div>
						    <div class="content">
						    	<h2 style="display: none"><a name="graphs" id="graph">Graphs</a></h2>
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
						</div>
	</div>

</div>
%#  "Content Container End"


%#End of the Host Exist or not case
%end