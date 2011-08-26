

%print 'Host value?', host
%import time

%# If got no Host, bailout
%if not host:
%include header title='Invalid host'

Invalid host
%else:

%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%include header title='Host detail about ' + host.host_name,  js=['eltdetail/js/hide.js', 'eltdetail/js/switchbuttons.js', 'eltdetail/js/multibox.js', 'eltdetail/js/multi.js'],  css=['eltdetail/tabs.css', 'eltdetail/eltdetail.css', 'eltdetail/switchbuttons.css', 'eltdetail/hide.css', 'eltdetail/multibox.css'], top_right_banner_state=top_right_banner_state 



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
  <div id="host_preview">
    <h2 class="icon_{{host.state.lower()}}">{{host.state}}: {{host.host_name}}</h2>

    <dl class="grid_6">
      <dt>Alias:</dt>
      <dd>{{host.alias}}</dd>
      
      <dt>Parents:</dt>
      %if len(host.parents) > 0:
      <dd> {{','.join([h.get_name() for h in host.parents])}}</dd>
      %else:
      <dd> No parents </dd>
      %end
      <dt>Members of:</dt>
      %if len(host.hostgroups) > 0:
      <dd> {{','.join([hg.get_name() for hg in host.hostgroups])}}</dd>
      %else:
      <dd> No groups </dd>
      %end
    </dl>
    <dl class="grid_6">
      <dt>Notes:</dt>
      <dd>{{host.notes}}</dd>
    </dl>
    <div class="grid_4">
      <img class="box_shadow host_img_80" src="/static/images/no_image.png">
    </div>
  </div>
  <hr>
  <div id="host_overview">
    <h2>Host Overview</h2>

    <div class="grid_6">
      <table class="box_shadow">
	<tbody>
	  <tr>
	    <th scope="row" class="column1">Host Status</th>
	    <td><span class="state_{{host.state.lower()}} icon_{{host.state.lower()}}">{{host.state}}</span> (since {{helper.print_duration(host.last_state_change, just_duration=True, x_elts=2)}}) </td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Status Information</th>
	    <td>{{host.output}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Performance Data</th>	
	    <td>{{host.perf_data}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Business impact</th>	
	    <td>{{host.business_impact}}</td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Current Attempt</th>
	    <td>{{host.attempt}}/{{host.max_check_attempts}} ({{host.state_type}} state)</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Last Check Time</th>
	    <td title='Last check was at {{time.asctime(time.localtime(host.last_chk))}}'>was {{helper.print_duration(host.last_chk)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Check Latency / Duration</th>
	    <td>{{'%.2f' % host.latency}} / {{'%.2f' % host.execution_time}} seconds</td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Next Scheduled Active Check</th>
	    <td title='Next active check at {{time.asctime(time.localtime(host.next_chk))}}'>{{helper.print_duration(host.next_chk)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Last State Change</th>
	    <td>{{time.asctime(time.localtime(host.last_state_change))}}</td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Last Notification</th>
	    <td>{{helper.print_date(host.last_notification)}} (notification {{host.current_notification_number}})</td>
	  </tr>	
	  <tr>						
	    <th scope="row" class="column1">Is This Host Flapping?</th>
	    <td>{{helper.yes_no(host.is_flapping)}} ({{helper.print_float(host.percent_state_change)}}% state change)</td>

	  </tr>
	  <tr class="odd">
	    <th scope="row" class="column1">In Scheduled Downtime?</th>
	    <td>{{helper.yes_no(host.in_scheduled_downtime)}}</td>
	  </tr>	
	</tbody>
	<tbody class="switches">
	  <tr class="odd">
	    <th scope="row" class="column1">Active/passive Checks</th>
	    <td title='This will also enable/disable this host services' onclick="toggle_checks('{{host.host_name}}' , '{{host.active_checks_enabled|host.passive_checks_enabled}}')"> {{!helper.get_input_bool(host.active_checks_enabled|host.passive_checks_enabled)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Notifications</th>
	    <td onclick="toggle_notifications('{{host.host_name}}' , '{{host.notifications_enabled}}')"> {{!helper.get_input_bool(host.notifications_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Event Handler</th>
	    <td onclick="toggle_event_handlers('{{host.host_name}}' , '{{host.event_handler_enabled}}')" > {{!helper.get_input_bool(host.event_handler_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Flap Detection</th>
	    <td onclick="toggle_flap_detection('{{host.host_name}}' , '{{host.flap_detection_enabled}}')" > {{!helper.get_input_bool(host.flap_detection_enabled)}}</td>
	  </tr>
	</tbody>	
      </table>
    </div>
  

    <dl class="grid_10 box_shadow">


      <div id="box_commannd">
	<a href="#" onclick="try_to_fix('{{host.host_name}}')">{{!helper.get_button('Try to fix it!', img='/static/images/enabled.png')}}</a>
	<a href="#" onclick="acknoledge('{{host.host_name}}')">{{!helper.get_button('Acknowledge it', img='/static/images/wrench.png')}}</a>
	<a href="#" onclick="recheck_now('{{host.host_name}}')">{{!helper.get_button('Recheck now', img='/static/images/delay.gif')}}</a>
	<a href="/depgraph/{{host.host_name}}" class="mb" title="Impact map of {{host.host_name}}">{{!helper.get_button('Show impact map', img='/static/images/state_ok.png')}}</a>
	{{!helper.get_button('Submit Check Result', img='/static/images/passiveonly.gif')}}
	{{!helper.get_button('Send Custom Notification', img='/static/images/notification.png')}}
	{{!helper.get_button('Schedule Downtime For This Host', img='/static/images/downtime.png')}}


	<div class="clear"></div>
      </div>
      <hr>
      
      %#    Now print the dependencies if we got somes
      %if len(host.parent_dependencies) > 0:
      <a id="togglelink-{{host.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{host.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
      <div class="clear"></div>
      {{!helper.print_business_rules(datamgr.get_business_parents(host))}}
      <hr>
      %end

      <div class='host-services'>
	%for s in helper.get_host_services_sorted(host):
	  <div class="service">
	    <div class="divstate{{s.state_id}}">
	      %for i in range(0, s.business_impact-2):
	        <img src='/static/images/star.png'>
	      %end
		
		<span style="font-size:125%">{{s.service_description}}</span> is <span style="font-size:125%">{{s.state}}</span> since {{helper.print_duration(s.last_state_change, just_duration=True, x_elts=2)}}, last check was {{helper.print_duration(s.last_chk)}}
	    </div>
	  </div>
	  %# End of this service
	  %end
      </div>
      
    </dl>
  </div>
  <div class="clear"></div>
  <hr>
  <div id="host_more">
    <dl class="grid_6">
      <ul id="tabs">
	<li><a class="tab" href="#" id="tabone">Comments</a></li>
	<li><a class="tab" href="#" id="tabtwo">Downtimes</a></li>
      </ul>
      <div>
	<div class="feature">
	  1
	</div>
      
	<div class="feature">
	  adv
	</div>
	
      </div>
      blabla
    </dl>
  </div>


  <div class="clear"></div>
  <div id="footer" class="grid_16">




%# We link tabs and real code here
<script type="text/javascript">
  window.addEvent('domready',function(){
  this.tabs = new MGFX.Tabs('.tab','.feature', {
  autoplay: false
  });
  });
  </script>

</div>
<div class="clear"></div>
</div>

%#End of the Host Exist or not case
%end

%include footer

