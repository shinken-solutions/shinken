%helper = app.helper

%rebase layout css=['wall/css/snowstack.css', 'wall/css/wall.css'], title='Wall view', js=['wall/js/snowstack.js', 'wall/js/wall.js'], refresh=True, user=user, print_menu=False, print_header=True



<div class="page view">
  <img src="/static/images/next.png" class="next-icon" onclick="go_right();"/>
  <img src="/static/images/previous.png" class="previous-icon" onclick="go_left();"/>
    <div class="origin view">
        <div id="camera" class="camera view"></div>
    </div>
</div>


<script type="text/javascript">
var images = {{!impacts}};
</script>


<div class="last_errors">
%if len(problems) == 0:
<h2>No new IT problems in the last 10minutes</h2>
%else:
<h3>There are {{len(problems)}} new IT problems in the last 10 minutes :</h3>
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
	   <img style="width : 32px; height:32px" src="{{helper.get_icon_state(pb)}}">
	 </div>
	 <div class="wall-problems-text">
	 %for i in range(0, pb.business_impact-2):
	 <img style="width : 16px; height:16px" src='/static/images/star.png'>
	 %end

	   <span style="font-size:110%">{{!helper.get_link(pb, short=False)}}</span> is <span style="font-size:110%">{{pb.state}}</span> since {{helper.print_duration(pb.last_state_change, just_duration=True, x_elts=2)}}
	 </div>
       </div>

%end
</div>
