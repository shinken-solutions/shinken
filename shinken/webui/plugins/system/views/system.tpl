%rebase layout globals(), css=['system/css/system.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

<div class="row-fluid">
  <div class="span12">
    <h3><i class="icon-cogs"> General Informations </i></h3>
    <div class="span4 well general-box">
      <h4><i class="icon-cog"></i> Start Time</h4>
      <span class="general">{{helper.print_duration(app.datamgr.get_program_start())}}</span>
    </div>
    <div class="span4 well general-box">
      <h4><i class="icon-cog"></i> Version</h4>
      <span class="general">Shinken {{VERSION}}</span>
    </div>
    <!--
    <div class="row-fluid">
      <div class="span6">Level 2</div>
      <div class="span6">Level 2</div>
    </div> -->

    <div class="row-fluid">
      <div class="span9">
        <h3><i class="icon-cogs"> Shinken Daemons</i></h3>
        %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
        %for (sat_type, sats) in types:
        <h4><i class="icon-bullhorn"></i> {{sat_type.capitalize()}}</h4>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>State</th>
              <th>Alive</th>
              <th>Attemts</th>
              <th>Last Check</th>
              <th>Realm</th>
            </tr>
          </thead>
          <tbody>
          %for s in sats:
            <tr>
              <td>1</td>
              <td><img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" /></td>
              <td>{{s.alive}}</td>
              <td>{{s.attempt}}/{{s.max_check_attempts}}</td>
              <td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
              <td>{{s.realm}}</td>
            </tr>
          </tbody>
          %end  
        </table>
        %end
      </div>
      <div class="span3">
        <span></span>
      </div>
    </div>
  </div>
</div>


<!-- 	<div class="row-fluid shell">
		    %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
	    	%for (sat_type, sats) in types:
	        <div class="span4 well daemon-box box-cheat">
            <h4><i class="icon-th"></i> {{sat_type.capitalize()}}:</h4>
            %for s in sats:
            <table class="table">
              <tr>
                <td class="column1"><b>State:</b></td>
                <td><img style="width: 16px; height: 16px;" src="{{helper.get_icon_state(s)}}" /></td>
              </tr>
              <tr>
                <td class="column1"><b>Name:</b></td>
                <td> {{s.get_name()}}</td>
              </tr>
              <tr>
                <td class="column1"><b>Alive:</b></td>
                <td>{{s.alive}}</td>
              </tr>
              <tr>
                <td class="column1"><b>Attemts:</b></td>
                <td>{{s.attempt}}/{{s.max_check_attempts}}</td>
                <tr>
                  <td class="column1"><b>Last Check:</b></td>
                  <td title='{{helper.print_date(s.last_check)}}'>{{helper.print_duration(s.last_check, just_duration=True, x_elts=2)}}</td>
                </tr>
                <tr>
                  <td class="column1"><b>Realm:</b></td>
                  <td>{{s.realm}}</td>
                </tr>
              </tr>
            </table>
            %end
          </div>
          %end
	</div> -->
