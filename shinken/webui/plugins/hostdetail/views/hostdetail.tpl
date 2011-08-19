

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


%include header title='Host detail about ' + host.host_name,  js=['hostdetail/js/jit-yc.js', 'hostdetail/js/excanvas.js', 'hostdetail/js/eltdeps.js', 'hostdetail/js/hide.js', 'hostdetail/js/switchbuttons.js'],  css=['hostdetail/eltdeps.css', 'hostdetail/tabs.css', 'hostdetail/hostdetail.css', 'hostdetail/switchbuttons.css', 'hostdetail/hide.css'], top_right_banner_state=top_right_banner_state 




<script type="text/javascript">
  var graph_root = '{{host.get_name()}}';   /*'test_host_0';*/
  var json_graph = {{helper.create_json_dep_graph(host, levels=3)}};
</script>

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
      <table>
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
	    <th scope="row" class="column1">Active Checks</th>
	    <td> {{!helper.get_input_bool(host.active_checks_enabled)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Passive Checks</th>
	    <td> {{!helper.get_input_bool(host.passive_checks_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Obsessing</th>
	    <td> {{!helper.get_input_bool(host.obsess_over_host)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Notifications</th>
	    <td> {{!helper.get_input_bool(host.notifications_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Event Handler</th>
	    <td> {{!helper.get_input_bool(host.event_handler_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Flap Detection</th>
	    <td> {{!helper.get_input_bool(host.flap_detection_enabled)}}</td>
	  </tr>
	</tbody>	
      </table>
    </div>
  

    <dl class="grid_10">
      
      <ul id="tabs">
	
	<li><a class="tab" href="#" id="tabone">Services</a></li>
	<li><a class="tab" href="#" id="tabtwo">Actions</a></li>
	<li><a class="tab" href="#" id="tabthree">Depenencies graph</a></li>

      </ul>
      <div>
	
	%# Here print all services of this host, sorted by business impact
	<div class="feature">
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
        </div>

	<div class="feature">
	  <div id="box_commannd">
	    {{!helper.get_button('Try to fix it!', img='/static/images/find.png')}}
	    <div class="clear"></div>
	    {{!helper.get_button('Acknowledge it', img='/static/images/wrench.png')}}
	    <div class="clear"></div>
	    {{!helper.get_button('Recheck now', img='/static/images/time.png')}}
	    <div class="clear"></div>
	    {{!helper.get_button('Show advanced options', img='/static/images/accept.png', id='toggle_advanced_actions')}}
	    <div class="clear"></div>
	    <hr>
	    <div id="advanced_actions">
	      {{!helper.get_button('Submit Passive Check Result', img='/static/images/cross.png')}}
	      {{!helper.get_button('Stop Accepting Passive Checks', img='/static/images/passiv.png')}}
	      {{!helper.get_button('Start Obsessing Over', img='/static/images/tick.png')}}
	      {{!helper.get_button('Disable Notifications For This Host', img='/static/images/cross.png')}}
	      {{!helper.get_button('Send Custom Notification', img='/static/images/notification.png')}}
	      {{!helper.get_button('Schedule Downtime For This Host', img='/static/images/time.png')}}
	      {{!helper.get_button('Disable Flap Detection For This Host', img='/static/images/cross.png')}}
	      
	    </div>
	  </div>
	</div>
	


	<div class="feature">
	  <div id="infovis"> </div>
	  <div id="right-container">
	    <div id="inner-details"></div>
	  </div>

	  <div id="log">Loading host informations...</div>
	</div>
	
      </div>
    </dl>
  </div>


  <div id="host_more">
  </div>


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

