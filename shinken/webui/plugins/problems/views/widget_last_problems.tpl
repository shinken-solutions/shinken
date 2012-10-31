
%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%rebase widget globals(), css=['problems/css/accordion.css', 'problems/css/pagenavi.css', 'problems/css/perfometer.css', 'problems/css/img_hovering.css'], js=['problems/js/img_hovering.js']

%if len(pbs) == 0:
  <span>No IT problems! Congrats.</span>
%end

%for pb in pbs:

<div class="tableCriticity pull-left row-fluid">
  <div class='img_status pull-left'>
    <div class="aroundpulse">
      %# " We put a 'pulse' around the elements if it's an important one "
      %if pb.business_impact > 2 and pb.state_id in [1, 2, 3]:
      <span class="pulse"></span>
      %end
      <img src="{{helper.get_icon_state(pb)}}" />
    </div>
  </div>


    <span class="alert-small alert-{{pb.state.lower()}}">{{pb.state}}</span> for {{!helper.get_link(pb)}}
    <div class='pull-right'>
    %for j in range(0, pb.business_impact-2):
    <img src='/static/images/star.png' alt="star">
    %end
    </div>

</div>
<div style="clear:both;"/>
%end


