%helper = app.helper
%datamgr = app.datamgr

%rebase layout title='All problems', js=['dashboard/js/sl_slider.js','dashboard/js/functions.js'], css=['dashboard/css/fullscreen.css'], menu_part='/'+page, user=user, print_menu=False, print_header=False

%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>

%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end

			<div id="top_container" class="grid_16">
				<div class="grid_16">
					<script language="JavaScript">
						//Refresh page script- By Brett Taylor (glutnix@yahoo.com.au)
						//Modified by Dynamic Drive for NS4, NS6+
						//Visit http://www.dynamicdrive.com for this script

						//configure refresh interval (in seconds)
						var countDownInterval=108;
						//configure width of displayed text, in px (applicable only in NS4)
						var c_reloadwidth=200
					</script>


					<ilayer id="c_reload" width=&{c_reloadwidth}; ><layer id="c_reload2" width=&{c_reloadwidth}; left=0 top=0></layer></ilayer>

					<script>
						var countDownTime=countDownInterval+1;
						function countDown(){
						countDownTime--;
						if (countDownTime <=0){
						countDownTime=countDownInterval;
						clearTimeout(counter)
						window.location.reload()
						return
						}
						if (document.all) //if IE 4+
						document.all.countDownText.innerText = countDownTime+" ";
						else if (document.getElementById) //else if NS6+
						document.getElementById("countDownText").innerHTML=countDownTime+" "
						else if (document.layers){ //CHANGE TEXT BELOW TO YOUR OWN
						document.c_reload.document.c_reload2.document.write('Next <a href="javascript:window.location.reload()">refresh</a> in <b id="countDownText">'+countDownTime+' </b> seconds')
						document.c_reload.document.c_reload2.document.close()
						}
						counter=setTimeout("countDown()", 1000);
						}

						function startit(){
						if (document.all||document.getElementById) //CHANGE TEXT BELOW TO YOUR OWN
						document.write('<p>Next <a href="javascript:window.location.reload()">refresh</a> in <b id="countDownText">'+countDownTime+' </b> seconds</p>')
						countDown()
						}

						if (document.all||document.getElementById)
						startit()
						else
						window.onload=startit
					</script>
					
				</div>
			</div>
<div id="dash_container" class="grid_16">
    %# " We will print Business impact level of course"
    %imp_level = 10

    %# " We remember the last hname so see if we print or not the host for a 2nd service"
    %last_hname = ''

    %# " We try to make only importants things shown on same output "
    %last_output = ''
    %nb_same_output = 0

    %for pb in pbs:
    
    %if pb.business_impact != imp_level:
    
     <div class="grid_16 item">
     <h2>{{!helper.get_business_impact_text(pb)}} </h2>
     <ul>
     	<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">localhost</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">orca</a> </li>
		<li class="grid_3"> <a class="box_round_small spezial_state_critical" href="#">delphi</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">router 1</a> </li>
		<li class="grid_3"> <a class="box_round_small" href="#">router lu</a> </li>
		<li class="grid_3"> <a class="box_round_small spezial_state_unreachable" href="#">backbone router</a> </li>
     <ul>
     </div>
       %# "We reset the last_hname so we won't overlap this feature across tables"
       %last_hname = ''
       %last_output = ''
       %nb_same_output = 0
      %end
      %imp_level = pb.business_impact

      %# " We check for the same output and the same host. If we got more than 3 of same, make them opacity effect"
      %if pb.output == last_output and pb.host_name == last_hname:
          %nb_same_output += 1
      %else:
          %nb_same_output = 0
      %end
      %last_output = pb.output
		%end 
</div>