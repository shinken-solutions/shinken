%rebase layout globals(),js=['dashboard/js/mooMasonry.js'], css=['dashboard/css/dashboard.css', 'dashboard/css/csschart.css'], title='Architecture state', menu_part='/dashboard'

%from shinken.bin import VERSION
%helper = app.helper

<script type="text/javascript">
	
	window.addEvent('domready', function(){
		document.id('secondary').masonry({columnWidth: 100});
	});
	
</script>

<div id="widget_container" class="grid_16 item">
	<div id="messagebox" class="gradient_alert" style="margin-top: 20px;">
		<img src="/static/images/icons/alert.png" alt="some_text" style="height: 40px; width: 40px" class="grid_4"/> 
		<p><strong>Mockup</strong></p>
	</div>
	<div>
		<div class="wrap">
        	<div class="box grid_12">
        		<div class="widget_head"><h3>Business Impacts</h3></div>
                <p>Donec nec justo eget felis facilisis fermentum. Aliquam porttitor mauris. </p>
			</div>

            <div class="box grid_4 hide">
            	<div class="widget_head"><h3>Charts</h3></div>
                <div class="widget_body">
                    <dl id="csschart">
						<dt>Impacts</dt>
						<dd><span class="first type1 p55"><em>55</em></span></dd>								
							
						<dt>Services</dt>
						<dd><span class="type2 p80"><em>80</em></span></dd>			
							
						<dt>Hosts</dt>
						<dd><span class="type3 p72"><em>72</em></span></dd>	
					</dl>
            	</div>
            </div>

            <div class="box grid_3">
            	<div class="widget_head"> <h3>Shinken Status</h3> </div>
                <div class="widget_body">
	                <table border="1">
						<tbody>
							<tr>
								<td class="first">Running sice</td>
								<td class="second">{{helper.print_duration(app.datamgr.get_program_start())}}</td>
							</tr>
							<tr>
								<td class="first">Version</td>
								<td class="second">{{VERSION}}</td>
							</tr>
							%types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
							%for (sat_type, sats) in types:
								<tr>
								%for s in sats:
									<td>{{sat_type.capitalize()}} State</td>
									<td>	     
							   			%if not s.alive:
											<span class="pulse"></span>
								      	%end
								      	<img style="width: 16px; height : 16px;" src="{{helper.get_icon_state(s)}}" alt="stateicon"/>
								    </td>
									%# end of this satellite type
							 		%end
								</tr>
								%# end of this satellite type
							 	%end
						</tbody>
					</table>
				</div>
			</div>

                <div class="box grid_4">
                    <div class="widget_head"><h3>IT Problems</h3></div>
                    <div class="widget_body">
	                    <table border="1">
							<tbody>
								<tr>
									<td class="first">Problems</td>
									<td class="second">{{app.datamgr.get_nb_all_problems()}}</td>
								</tr>
								<tr>
									<td class="first">Unhandled </td>
									<td class="second">{{app.datamgr.get_nb_problems()}}</td>
								</tr>
								<tr>
									<td class="first">Total </td>
									<td class="second">{{app.datamgr.get_nb_elements()}}</td>
								</tr>
							</tbody>
						</table>
					</div>
                </div>



                <div class="box col1">
                    <h5>5</h5>
                    <p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Donec odio.</p>
                </div>

            </div> <!-- /#secondary.wrap -->
        </div>  

</div>

