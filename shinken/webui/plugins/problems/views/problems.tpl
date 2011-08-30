%import time

%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%include header title='All problems', top_right_banner_state=top_right_banner_state, js=['problems/js/accordion.js']


	 
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
  <div id="accordion">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %for pb in pbs:
      
      %if pb.business_impact != imp_level:
         <h4> Business impact : {{pb.business_impact}} </h4>
      %end
      %imp_level = pb.business_impact
      <h3 class="toggler">{{pb.get_full_name()}}</h3>
      <div class="element">
	<p>{{pb.state}}</p>
      </div>
    %end
  </div>
      
</div>

<div class="clear"></div>
</div>


%include footer


