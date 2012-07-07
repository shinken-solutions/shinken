%helper = app.helper

%rebase layout css=['wall/css/snowstack.css', 'wall/css/wall.css'], title='Wall view', js=[ 'wall/js/wall.js'], refresh=True, user=user, print_menu=False, print_header=True, menu_part='/wall'



<div class="page view">
  <img src="/static/images/next.png" class="next-icon" onclick="go_right();"/>
  <img src="/static/images/previous.png" class="previous-icon" onclick="go_left();"/>

%ind = -1
%for imp in impacts:
   %ind += 1
   %x,y = divmod(ind, 2)
       <div class="media divstate{{imp.state_id}} sliding-impacts" style="left:{{x * 400}}px; position: absolute; top:{{ y * 150}}px; i:{{ind}} {{x}} {{y}}">
         <span class="wall-pulse pulse" title=""></span>
         <div class="item-icon">
	          <img class="wall-icon" src="{{app.helper.get_icon_state(imp)}}"></img>
         </div>
	  <div class="btn-group right item-button">
	    <a href="{{app.helper.get_link_dest(imp)}}" class='btn' title="Details"> <i class="icon-plus"></i> Details</a>
	  </div>

         <div class="item-text">
          <span class="state_{{imp.state.lower()}}">{{imp.state}} <br/> {{imp.get_full_name()}}</span>
	 </div>

       </div>
%end
</div>


<script type="text/javascript">
var images = [];
</script>


<div class="last_errors">
%if len(problems) == 0:
<h2>No new IT problems in the last 10minutes</h2>
%else:
<h3>There are {{len(problems)}} new IT problems in the last 10 minutes:</h3>
%end

%ind = -1
%for pb in problems:
   %ind += 1
   %x,y = divmod(ind, 3)
       <div class="divstate{{pb.state_id}} sliding" style="left:{{x * 400}}px; position: absolute; top:{{ y * 50 + 50}}px; i:{{ind}} {{x}} {{y}}">
	 <div class="wall-aroundpulse aroundpulse">
	 %if pb.business_impact > 2:
	   <span class="wall-small-pulse pulse" title=""></span>
	 %end
	   <img style="width: 32px; height:32px" src="{{helper.get_icon_state(pb)}}">
	 </div>
	 <div class="wall-problems-text">
	 %for i in range(0, pb.business_impact-2):
	 <img style="width: 16px; height:16px" src='/static/images/star.png'>
	 %end

	   <span style="font-size:110%">{{!helper.get_link(pb, short=False)}}</span> is <span style="font-size:110%">{{pb.state}}</span> since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}
	 </div>
       </div>

%end
</div>
