

%print 'Elt value?', elt
%import time

%# If got no Elt, bailout
%if not elt:
%include header title='Invalid name'

Invalid element name
%else:

%helper = app.helper
%datamgr = app.datamgr

%elt_type = elt.__class__.my_type

%top_right_banner_state = datamgr.get_overall_state()


%include header title=elt_type.upper() + ' detail about ' + elt.get_full_name(),  js=['eltdetail/js/hide.js', 'eltdetail/js/switchbuttons.js', 'eltdetail/js/multibox.js', 'eltdetail/js/multi.js'],  css=['eltdetail/tabs.css', 'eltdetail/eltdetail.css', 'eltdetail/switchbuttons.css', 'eltdetail/hide.css', 'eltdetail/multibox.css'], top_right_banner_state=top_right_banner_state 



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
    <h2 class="icon_{{elt.state.lower()}}">{{elt.state}}: {{elt.get_full_name()}}</h2>

    <dl class="grid_6">
      %#Alias, apretns and hostgroups arefor host only
      %if elt_type=='host':
         <dt>Alias:</dt>
         <dd>{{elt.alias}}</dd>

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
    <dl class="grid_4">
      <dt>Notes:</dt>
      %if elt.notes != '':
      <dd>{{elt.notes}}</dd>
      %else:
      <dd>(none)</dd>
      %end
      <dt>Importance</dt>
      <dd>{{!helper.get_business_impact_text(elt)}}</dd>
    </dl>
    <div class="grid_2">
      <img class="box_shadow host_img_80" src="/static/images/no_image.png">
    </div>
    %#   " If the elements is a root problem with a huge impact and not ack, ask to ack it!"
    %if elt.is_problem and elt.business_impact > 2 and not elt.problem_has_been_acknowledged:
    <div class="grid_4 box_shadow" id="important_banner">
      <table>
	<th scope="row" class="column1"><img src="/static/images/errorMedium.png"></th>
	<td>
	  This element got an important impact on your business, please fix it or acknoledge it.
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
	    <th scope="row" class="column1">Host Status</th>
	    <td><span class="state_{{elt.state.lower()}} icon_{{elt.state.lower()}}">{{elt.state}}</span> (since {{helper.print_duration(elt.last_state_change, just_duration=True, x_elts=2)}}) </td>
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
	  <tr>
	    <th scope="row" class="column1">Check Latency / Duration</th>
	    <td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Next Scheduled Active Check</th>
	    <td title='Next active check at {{time.asctime(time.localtime(elt.next_chk))}}'>{{helper.print_duration(elt.next_chk)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Last State Change</th>
	    <td>{{time.asctime(time.localtime(elt.last_state_change))}}</td>
	  </tr>	
	  <tr class="odd">
	    <th scope="row" class="column1">Last Notification</th>
	    <td>{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
	  </tr>	
	  <tr>						
	    <th scope="row" class="column1">Is This Host Flapping?</th>
	    <td>{{helper.yes_no(elt.is_flapping)}} ({{helper.print_float(elt.percent_state_change)}}% state change)</td>

	  </tr>
	  <tr class="odd">
	    <th scope="row" class="column1">In Scheduled Downtime?</th>
	    <td>{{helper.yes_no(elt.in_scheduled_downtime)}}</td>
	  </tr>	
	</tbody>
	<tbody class="switches">
	  <tr class="odd">
	    <th scope="row" class="column1">Active/passive Checks</th>
	    <td title='This will also enable/disable this host services' onclick="toggle_checks('{{elt.get_full_name()}}' , '{{elt.active_checks_enabled|elt.passive_checks_enabled}}')"> {{!helper.get_input_bool(elt.active_checks_enabled|elt.passive_checks_enabled)}}</td>
	  </tr>	
	  <tr>
	    <th scope="row" class="column1">Notifications</th>
	    <td onclick="toggle_notifications('{{elt.get_full_name()}}' , '{{elt.notifications_enabled}}')"> {{!helper.get_input_bool(elt.notifications_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Event Handler</th>
	    <td onclick="toggle_event_handlers('{{elt.get_full_name()}}' , '{{elt.event_handler_enabled}}')" > {{!helper.get_input_bool(elt.event_handler_enabled)}}</td>
	  </tr>
	  <tr>
	    <th scope="row" class="column1">Flap Detection</th>
	    <td onclick="toggle_flap_detection('{{elt.get_full_name()}}' , '{{elt.flap_detection_enabled}}')" > {{!helper.get_input_bool(elt.flap_detection_enabled)}}</td>
	  </tr>
	</tbody>	
      </table>
    </div>
  

    <dl class="grid_10 box_shadow">


      <div id="box_commannd">
	<a href="#" onclick="try_to_fix('{{elt.get_full_name()}}')">{{!helper.get_button('Try to fix it!', img='/static/images/enabled.png')}}</a>
	<a href="#" onclick="acknoledge('{{elt.get_full_name()}}')">{{!helper.get_button('Acknowledge it', img='/static/images/wrench.png')}}</a>
	<a href="#" onclick="recheck_now('{{elt.get_full_name()}}')">{{!helper.get_button('Recheck now', img='/static/images/delay.gif')}}</a>
	<a href="/depgraph/{{elt.get_full_name()}}" class="mb" title="Impact map of {{elt.get_full_name()}}">{{!helper.get_button('Show impact map', img='/static/images/state_ok.png')}}</a>
	{{!helper.get_button('Submit Check Result', img='/static/images/passiveonly.gif')}}
	{{!helper.get_button('Send Custom Notification', img='/static/images/notification.png')}}
	{{!helper.get_button('Schedule Downtime', img='/static/images/downtime.png')}}


	<div class="clear"></div>
      </div>
      <hr>
      
      %#    Now print the dependencies if we got somes
      %if len(elt.parent_dependencies) > 0:
      <a id="togglelink-{{elt.get_dbg_name()}}" href="javascript:toggleBusinessElt('{{elt.get_dbg_name()}}')"> {{!helper.get_button('Show dependency tree', img='/static/images/expand.png')}}</a>
      <div class="clear"></div>
      {{!helper.print_business_rules(datamgr.get_business_parents(elt))}}
      <hr>
      %end

      %# " Only print host service if elt is an host of course"
      %# " If the host is a problem, services will be print in the impacts, so don't"
      %# " print twice "
      %if elt_type=='host' and not elt.is_problem:
        <div class='host-services'>
	  <h3> Services </h3>
	  %for s in helper.get_host_services_sorted(elt):
	    <div class="service">
	      <div class="divstate{{s.state_id}}">
	        %for i in range(0, s.business_impact-2):
	          <img src='/static/images/star.png'>
		%end
		
		  <span style="font-size:125%">{{!helper.get_link(s, short=True)}}</span> is <span style="font-size:125%">{{s.state}}</span> since {{helper.print_duration(s.last_state_change, just_duration=True, x_elts=2)}}, last check was {{helper.print_duration(s.last_chk)}}
	      </div>
	    </div>
	    %# End of this service
	    %end
	</div>
     %end #of the only host part
	

     %if elt.is_problem:
	<div class='host-services'>
	<h3> Impacts </h3>
	  
	%for i in helper.get_impacts_sorted(elt):
          <div class="service">
            <div class="divstate{{i.state_id}}">
              %for j in range(0, i.business_impact-2):
                <img src='/static/images/star.png'>
	      %end
		  
	      <span style="font-size:125%">{{i.get_full_name()}}</span> is <span style="font-size:125%">{{i.state}}</span> since {{helper.print_duration(i.last_state_change, just_duration=True, x_elts=2)}}, last check was {{helper.print_duration(i.last_chk)}}
            </div>
          </div>
          %# End of this impact
          %end
	  </div>
	%# end of the 'is problem' if
	%end

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

