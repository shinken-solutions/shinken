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
%if not helper.can_action(user):
%global_disabled = 'disabled-link'
%end


%rebase layout_mobile title=elt_type.capitalize() + ' detail about ' + elt.get_full_name(), js=['eltdetail/js/jquery.color.js', 'eltdetail/js/jquery.Jcrop.js', 'eltdetail/js/iphone-style-checkboxes.js', 'eltdetail/js/hide.js', 'eltdetail/js/dollar.js', 'eltdetail/js/gesture.js', 'eltdetail/js/graphs.js'], css=['eltdetail/css/iphonebuttons.css', 'eltdetail/css/eltdetail.css', 'eltdetail/css/hide.css', 'eltdetail/css/gesture.css', 'eltdetail/css/jquery.Jcrop.css'], top_right_banner_state=top_right_banner_state , user=user, app=app

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

  // Now we hook teh global search thing
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


%#  "This is the background canvas for all gesture detection things "
%# " Don't ask me why, but the size must be included in the
%# canvas line here or we got problem!"
<div id='gesture_panel' class="pull-left">
  <canvas id="canvas" width="200" height="200" class="grid_10" style="border: 1px solid black;"></canvas>
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


%#  "Content Container Start"
<div data-role="collapsible-set" data-iconpos="right" class="span4">

	<h1 class="span12 no-leftmargin state_{{elt.state.lower()}} icon_down"> <img class="imgsize4" alt="icon state" src="{{helper.get_icon_state(elt)}}" width="36" height="36"/>{{elt.state}}: {{elt.get_full_name()}}</h1>

	<div class="span12 no-leftmargin box">
		<table class="span4 no-leftmargin">
		%#Alias, apretns and hostgroups arefor host only
		%if elt_type=='host':
			<tr>
		    	<td><strong>Alias:</srong></td>
		    	<td>{{elt.alias}}</td>
			</tr>
			<tr>
		    	<td><strong>Address:</strong></td>
		    	<td>{{elt.address}}</td>
			</tr>
			<tr>
		    	<td><strong>Importance:</strong></td>
		    	<td>{{!helper.get_business_impact_text(elt)}}</td>
			</tr>
		</table>

		<table class="span3">
			<tr>
		    	<td><strong>Parents:</strong></td>
		    	%if len(elt.parents) > 0:
		    	<td>{{elt.alias}}</td>
		    	%else:
		    	<td>No parents</td>
		    	%end
			</tr>
			<tr>
		    	<td><strong>Members of:</strong></td>
		    	%if len(elt.hostgroups) > 0:
		    	<td>{{','.join([hg.get_name() for hg in elt.hostgroups])}}</td>
		    	%else:
			    <td> No groups </td>
				%end
			</tr>
			%# End of the host only case, so now service
		    %else:
			<tr>
		    	<td><strong>Host: </strong></td>
		    	<td><a href="/mobile/host/{{elt.host.host_name}}" rel="external" class="link">{{elt.host.host_name}}</a></td>
			</tr>
			<tr>
		    	<td><strong>Members of: </strong></td>
		    	%if len(elt.servicegroups) > 0:
		    	<td>{{','.join([sg.get_name() for sg in elt.servicegroups])}}</td>
				%else:
			    <td> No groups </td>
				%end
			</tr>
			%end
			<tr>
			  	<td><strong>Notes: </strong></td>
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
                 onChange: function(elt, b){toggle_checks("{{elt.get_full_name()}}",!b);}
	       }
	       );

               $('#btn-not').iphoneStyle({
                 onChange: function(elt, b){toggle_notifications("{{elt.get_full_name()}}",!b);}
	       }
	       );

               $('#btn-evt').iphoneStyle({
                 onChange: function(elt, b){toggle_event_handlers("{{elt.get_full_name()}}",!b);}
	       }
	       );

               $('#btn-flp').iphoneStyle({
                 onChange: function(elt, b){toggle_flap_detection("{{elt.get_full_name()}}",!b);}
               }
               );
            });
	  </script>

    <!-- Start Host/Services-->
			<!-- Left, information part-->


      %if elt_type=='host':
	<div data-role="collapsible" data-content-theme="a" data-theme="a">
      <h3 class="span10">Host Information</h3>
      %else:
	<div data-role="collapsible" data-content-theme="a" data-theme="a">
      <h3 class="span10">Service Information</h3>
      %end:

      <table class="span10 table table-striped table-bordered table-condensed">
	<tr>
	  <td class="column1"><strong>{{elt_type.capitalize()}} Status: </strong></td>
	  <td><span class="alert-small alert-{{elt.state.lower()}}">{{elt.state}}</span> (since {{helper.print_duration(elt.last_state_change, just_duration=True, x_elts=2)}}) </td>
	</tr>
	<tr>
	  <td class="column1"><strong>Status Information: </strong></td>
	  <td>{{elt.output}}</td>
	</tr>
	<tr>
	  <td class="column1"><strong>Performance Data: </strong></td>
	  %# "If there any perf data?"
	  %if len(elt.perf_data) > 0:
	  <td>{{elt.perf_data}}</td>
	  %else:
	  <td>&nbsp;</td>
	  %end
	</tr>
	<tr>
	  <td class="column1"><strong>Current Attempt: </strong></td>
	  <td>{{elt.attempt}}/{{elt.max_check_attempts}} ({{elt.state_type}} state)</td>
	</tr>
	<tr>
	  <td class="column1"><strong>Last Check Time: </strong></td>
	  <td><span class="quickinfo" data-original-title='Last check was at {{time.asctime(time.localtime(elt.last_chk))}}'>was {{helper.print_duration(elt.last_chk)}}</span></td>
	</tr>
	<tr>
	  <td class="column1"><strong>Next Scheduled Active Check: </strong></td>
	  <td><span class="quickinfo" data-original-title='Next active check at {{time.asctime(time.localtime(elt.next_chk))}}'>{{helper.print_duration(elt.next_chk)}}</span></td>
	</tr>
	<tr>
	  <td class="column1"><strong>Last State Change: </strong></td>
	  <td>{{time.asctime(time.localtime(elt.last_state_change))}}</td>
	</tr>
   	<tr>
	  <td class="column1"><strong>Last Notification: </strong></td>
	  <td>{{helper.print_date(elt.last_notification)}} (notification {{elt.current_notification_number}})</td>
	</tr>
	<tr>
	  <td class="column1"><strong>Check Latency / Duration: </strong></td>
	  <td>{{'%.2f' % elt.latency}} / {{'%.2f' % elt.execution_time}} seconds</td>
	</tr>
	<tr>
	  <td class="column1"><strong>Is This Host Flapping?</strong></td>
	  <td>{{helper.yes_no(elt.is_flapping)}} ({{helper.print_float(elt.percent_state_change)}}% state change)</td>
	</tr>
	<tr>
	  <td class="column1"><strong>In Scheduled Downtime?</strong></td>
	  <td>{{helper.yes_no(elt.in_scheduled_downtime)}}</td>
	</tr>
      </table>
	</div>


    <!-- End Host/Service -->


	<div data-role="collapsible" data-content-theme="a" data-theme="a">
	<h3>Impacts</h3>

    <div class="tabbable span8 no-leftmargin">

	    <div class="tab-content">
	    	<!-- Tab Summary Start-->
		    <div class="tab-pane active" id="impacts">
		      <!-- Start of the Whole info pack. We got a row of 2 thing:
			   left is information, right is related elements -->
		      <div class="row-fluid">
		      <!-- So now it's time for the right part, related elements -->
		      <div class="span12">

			<!-- Show our father dependencies if we got some -->
			%#    Now print the dependencies if we got somes
			%if len(elt.parent_dependencies) > 0:
			<h3 class="span10">Root cause:</h3>
			<div class="clear"></div>
			%#{{!helper.print_business_rules(datamgr.get_business_parents(elt), source_problems=elt.source_problems, mobile =True)}}

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

			  <div class="service">

			  <div>
			    <img style="width: 16px; height:16px" alt="icon state" src="{{helper.get_icon_state(s)}}">
			    <span class='alert-small alert-{{s.state.lower()}}' style="font-size:110%">{{s.state}}</span> for <span style="font-size:110%">{{!helper.get_link_mobile(s, short=True)}}</span> since {{helper.print_duration(s.last_state_change, just_duration=True, x_elts=2)}}
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

		      <div class="service">


			  <div>
			    <img style="width: 16px; height:16px" alt="icon state" src="{{helper.get_icon_state(i)}}">
			    <span class='alert-small alert-{{i.state.lower()}}' style="font-size:110%">{{i.state}}</span> for <span style="font-size:110%">{{!helper.get_link_mobile(i, short=True)}}</span> since {{helper.print_duration(i.last_state_change, just_duration=True, x_elts=2)}}
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

		    </div>
	    </div>
	</div>
    </div>
</div>


%#End of the Host Exist or not case
%end

