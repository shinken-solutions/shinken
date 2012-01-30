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


%rebase layout title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(),  js=['eltdetail/js/graphs.js', 'eltdetail/js/domtab.js','eltdetail/js/dollar.js', 'eltdetail/js/gesture.js', 'eltdetail/js/hide.js', 'eltdetail/js/switchbuttons.js', 'eltdetail/js/multi.js'],  css=['eltdetail/css/tabs.css', 'eltdetail/css/eltdetail.css', 'eltdetail/css/switchbuttons.css', 'eltdetail/css/hide.css', 'eltdetail/css/gesture.css'], top_right_banner_state=top_right_banner_state , user=user, app=app



%# " We will save our element name so gesture functions will be able to call for the good elements."
<script type="text/javascript">var elt_name = '{{elt.get_full_name()}}';</script>


<div id="left_container" class="grid_3 fadein">
  <div id="dummy_box" class="box_gradient_horizontal"> 
  </div>
  <div id="nav_left">
    <ul>
      <li><a href="#">Overview</a></li>
      
      <li>
	<center>
	  <table cellspacing="2" cellpadding="0" border="0">
	    <tbody>
	      <tr>
		<th>Problems</th><th>Unhandled</th><th>All</th>
	      </tr>
	      
	      <tr>
		<td>
		  <a href="/problems" style="padding-top:0;">{{app.datamgr.get_nb_all_problems()}}</a>
		</td>
		<td>
		  %# " Add a pulse if there are problems unacked "
		  %nb_unack_pb = app.datamgr.get_nb_problems()
		  %if nb_unack_pb > 0:
		  <a href="/problems" style="padding-top:0;">
		    <div class="aroundpulse">
                      <span class="pulse" title=""></span>
		      {{nb_unack_pb}}
		    </div>
		  </a>
		  %else:
		    {{nb_unack_pb}}
		  %end
		</td>
                <td><a href="/problems" style="padding-top:0;">{{app.datamgr.get_nb_elements()}}</a></td>
              </tr>
	    </tbody>
	  </table>
	</center>
      </li>

      <li>
	<a href="#">Gestures</a>
      </li>
    </ul>
	<div class="opacity_hover">
	%#  "This is the background canvas for all gesture detection things " 
	%# " Don't ask me why, but the size must be included in the
	%# canvas line here or we got problem!"
	<center><canvas id="canvas" width="200" height="200"  style="border: 1px solid black;"></canvas></center>

		<div class="gesture_button">
          	<img title="By keeping a left click pressed and drawing a check, you will launch an acknowledgement." src="/static/eltdetail/images/gesture-check.png"/> Acknowledge
		</div>
		<div class="gesture_button">
          	<img title="By keeping a left click pressed and drawing a check, you will launch an recheck." src="/static/eltdetail/images/gesture-circle.png"/> Recheck
		</div>
		<div class="gesture_button">
          	<img title="By keeping a left click pressed and drawing a check, you will launch a try to fix command." src="/static/eltdetail/images/gesture-zigzag.png"/> Fix
		</div>
	</div>
  </div>
</div>
<div class="grid_12">
  <div id="host_preview" style="vertical-align:middle;">
    <h2 class="state_{{elt.state.lower()}}"><img style="width : 64px; height:64px" src="{{helper.get_icon_state(elt)}}" />{{elt.state}}: {{elt.get_full_name()}}</h2>

    <dl class="grid_6">
      %#Alias, apretns and hostgroups arefor host only
      %if elt_type=='host':
         <dt>Alias:</dt>
         <dd>{{elt.alias}}</dd>

			<dt>Address:</dt>
			<dd>{{elt.address}}</dd>

         <dt>Parents:</dt>
	 %if len(elt.parents) > 0:
         <dd> {{','.join([h.get_name() for h in elt.parents])}}</dd>
	 %else:
         <dd> No parents </dd>
	 %end
         <dt>Members of:</dt>
	 %if len(elt.hostgroups) > 0:
         <dd> {{','.join([hg.get_name() for hg in elt.hostgroups])}}</dd>
	 %else:
         <dd> No groups </dd>
	 %end
    %# End of the host only case, so now service
    %else:
	 <dt>Host:</dt>
         <dd> {{elt.host.host_name}}</dd>
         <dt>Members of:</dt>
         %if len(elt.servicegroups) > 0:
         <dd> {{','.join([sg.get_name() for sg in elt.servicegroups])}}</dd>
         %else:
         <dd> No groups </dd>
         %end
    %end 

    </dl>
    <dl class="grid_5">
      <dt>Notes:</dt>
      %if elt.notes != '':
      <dd>{{elt.notes}}</dd>
      %else:
      <dd>(none)</dd>
      %end
      <dt>Importance</dt>
      <dd>{{!helper.get_business_impact_text(elt)}}</dd>
    </dl>

    %#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
    %if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
    <div class="grid_4 box_shadow" id="important_banner">
      <table>
	<th scope="row" class="column1"><img src="/static/images/errorMedium.png"></th>
	<td>
	  This element has got an important impact on your business, please fix it or acknowledge it.
      </td></table>
    </div>
    %# "end of the 'SOLVE THIS' highlight box"
    %end
  </div>
  <hr>
  <div id="host_overview">

    <div class="grid_6">
      <table class="box_shadow">
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
	  <tr class="odd hidden_infos">
	    <th scope="row" class="column1">Last Notification</th>
	    <td>{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
	  </tr>
	  <tr class="hidden_infos">
	    <th scope="row" class="column1">Check Latency / Duration</th>
	    <td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
	  </tr>	
	  <tr class="odd hidden_infos">						
	    <th scope="row" class="column1">Is This Host Flapping?</th>
	    <td>{{helper.yes_no(elt.is_flapping)}} ({{helper.print_float(elt.percent_state_change)}}% state change)</td>

	  </tr>
	  <tr class="hidden_infos">
	    <th scope="row" class="column1">In Scheduled Downtime?</th>
	    <td>{{helper.yes_no(elt.in_scheduled_downtime)}}</td>
	  </tr>
	  <tr id="hidden_info_button" class="opacity_hover">
	    <th></th>
	    <td class="fadein">
	      <div style="float:left;" id="hidden_info_button"><a href="javascript:show_hidden_info()"> {{!helper.get_button('More', img='/static/images/expand.png')}}</a>
	      </div>
	      <div class="clear"></div>
	    </td>
	  </tr>

	</tbody>
	<tbody class="switches">
	  <tr class="odd fadein">
	    <th scope="row" class="column1">Active/passive Checks</th>
	    %if elt_type=='host':
	       %title = 'This will also enable/disable this host services'
	    %else:
	       %title = ''
	    %end
	    <td title="{{title}}" onclick="toggle_checks('{{elt.get_full_name()}}' , '{{elt.active_checks_enabled|elt.passive_checks_enabled}}')"> {{!helper.get_input_bool(elt.active_checks_enabled|elt.passive_checks_enabled)}}</td>
	  </tr>	
	  <tr class="fadein">
	    <th scope="row" class="column1">Notifications</th>
	    <td onclick="toggle_notifications('{{elt.get_full_name()}}' , '{{elt.notifications_enabled}}')"> {{!helper.get_input_bool(elt.notifications_enabled)}}</td>
	  </tr>
	  <tr class="fadein">
	    <th scope="row" class="column1">Event Handler</th>
	    <td onclick="toggle_event_handlers('{{elt.get_full_name()}}' , '{{elt.event_handler_enabled}}')" > {{!helper.get_input_bool(elt.event_handler_enabled)}}</td>
	  </tr>
	  <tr class="fadein">
	    <th scope="row" class="column1">Flap Detection</th>
	    <td onclick="toggle_flap_detection('{{elt.get_full_name()}}' , '{{elt.flap_detection_enabled}}')" > {{!helper.get_input_bool(elt.flap_detection_enabled)}}</td>
	  </tr>
	</tbody>	
      </table>
    </div>
  </div>

    <dl class="grid_10 box_shadow">


      <div id="box_commannd" class="fadein">
	<a href="#" onclick="try_to_fix('{{elt.get_full_name()}}')">{{!helper.get_button('Try to fix it!', img='/static/images/enabled.png')}}</a>
	<a href="#" onclick="acknowledge('{{elt.get_full_name()}}')">{{!helper.get_button('Acknowledge it', img='/static/images/wrench.png')}}</a>
	<a href="#" onclick="recheck_now('{{elt.get_full_name()}}')">{{!helper.get_button('Recheck now', img='/static/images/delay.gif')}}</a>
	<a href="/depgraph/{{elt.get_full_name()}}" class="mb" title="Impact map of {{elt.get_full_name()}}">{{!helper.get_button('Show impact map', img='/static/images/state_ok.png')}}</a>
	%#{{!helper.get_button('Submit Check Result', img='/static/images/passiveonly.gif')}}
	%#{{!helper.get_button('Send Custom Notification', img='/static/images/notification.png')}}
	%#{{!helper.get_button('Schedule Downtime', img='/static/images/downtime.png')}}


	<div class="clear"></div>
      </div>

      <hr>
      
      %#    Now print the dependencies if we got somes
      %if len(elt.parent_dependencies) > 0:
      <a id="togglelink-{{elt.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{elt.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
      <div class="clear"></div>
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

    </dl>    

    
    <div class="grid_16 opacity_hover">
    <script type="text/javascript">
		document.write('<style type="text/css">');    
		document.write('div.domtab div{display:none;}<');
		document.write('/s'+'tyle>');    
    </script>
    
    <div class="domtab fadein">
		<ul class="domtabs">
			<li class="box_gradient_vertical"><a href="#graph">Graphs</a></li>
			<li class="box_gradient_vertical"><a href="#comment">Comments</a></li>
			<li class="box_gradient_vertical"><a href="#downtime">Downtimes</a></li>
		</ul>

		<div class="tabcontent">
			<h2 style="display: none"><a name="graphs" id="graph">Graphs</a></h2>
			%uris = app.get_graph_uris(elt, graphstart, graphend)
			%if len(uris) == 0:
			  <p>No graphs</p>
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
			
			%img_id = 0
			%for g in uris:
			   %img_id += 1
			   %img_src = g['img_src']
			   %link = g['link']
			<p><a href="{{link}}"><img src="{{img_src}}" class="graphimg" id="graphimg-{{img_id}}"></img></a></p>
			%end
		</div>

		<div class="tabcontent">
			<h2 style="display: none"><a name="comment" id="comment">Comments</a></h2>
				<ul class="tabmenu">
				  <li>
						<a href="#" class="">Add Comments</a>
					</li>
					<li>
						<a onclick="delete_all_comments('{{elt.get_full_name()}}')" href="#" class="">Delete Comments</a>
					</li>
				</ul>
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
			  <p>None</p>
			%end
		</div>
		<div>
			<h2  style="display: none"><a name="downtime" id="downtime">Downtimes</a></h2>

				<ul class="tabmenu">
					<li>
						<a href="#" class="">Add Downtime</a>
					</li>
					<li>
						<a onclick="delete_all_downtimes('{{elt.get_full_name()}}')" href="#" class="">Delete Downtimes</a>
					</li>
				</ul>
			%if len(elt.downtimes) > 0:
			  <table>
			    <tr>
			      <td class="tdBorderLeft tdCriticity" style="width:30px;"><b>Author</b></td>
			      <td class="tdBorderLeft tdCriticity" style="width:350px;"><b>Comment</b></td>
			      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>Start</b></td>
			      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>End</b></td>
			      <td class="tdBorderLeft tdCriticity" style="width:100px;"><b>Delete</b></td>
			    </tr>
			    %for dt in elt.downtimes:
			    <tr>
			      <td class="tdBorderTop tdCriticity" >{{dt.author}}</td>
			      <td class="tdBorderTop tdBorderLeft tdBorderLeft tdCriticity" >{{dt.comment}}</td>
			      <td class="tdBorderTop tdBorderLeft tdCriticity">{{helper.print_date(dt.start_time)}}</td>
			      <td class="tdBorderTop tdBorderLeft tdCriticity">{{helper.print_date(dt.end_time)}}</td>
			      <td class="tdBorderTop tdBorderLeft tdCriticity"><a href="#" onclick="delete_downtime('{{elt.get_full_name()}}', '{{dt.id}}')"><img src="/static/images/delete.png"/></a></td>
			    </tr>
			    %end
			  </table>
			%else:
			  <p>None</p>
			%end
	
		</div>
	</div>
	
      <br/>


	
      </div>
    </div>
    
    
  </div>

  <div class="clear"></div>





%# We link tabs and real code here
<script type="text/javascript">
  window.addEvent('domready',function(){
  this.tabs = new MGFX.Tabs('.tab','.feature', {
  autoplay: false
  });
  });
  </script>

</div>
</div>
<div class="clear"></div>


%#End of the Host Exist or not case
%end
</div>


