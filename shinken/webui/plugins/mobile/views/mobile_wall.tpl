%rebase layout_mobile globals(), title="Wall", js=['mobile/js/mobile_main.js', 'mobile/js/mobile_problems.js'], css=['mobile/css/main.css', 'mobile/css/problems.css'], menu_part='/wall'

%helper = app.helper

<div class="page view">

%ind = -1
%for imp in impacts:
   %ind += 1
   %x,y = divmod(ind, 2)
       <a href="/mobile{{app.helper.get_link_dest(imp)}}" class="media divstate{{imp.state_id}} sliding-impacts wall_element ui-btn-active" rel="external">
         <div class="item-icon">
	          <img class="wall-icon" src="{{app.helper.get_icon_state(imp)}}" width="48" height="48"></img>
         </div>
         <div class="item-text">
          <span class="state_{{imp.state.lower()}}">{{imp.state}} <br/> {{imp.get_full_name()}}</span>
	 </div>

       </a>
%end
</div>


