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
      <div class="span8">
        <h3><i class="icon-cogs"> Shinken Daemons</i></h3>
        %types = [ ('scheduler', schedulers), ('poller', pollers), ('broker', brokers), ('reactionner', reactionners), ('receiver', receivers)]
        %for (sat_type, sats) in types:
        <h4><i class="icon-bullhorn"></i> {{sat_type.capitalize()}}</h4>
        <table class="table table-hover">
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
      <div class="span4">
        <div class="thumbnail" style="margin-top: 65px;">
          <!-- <img alt="" src="http://placehold.it/300x200"> -->
          <div class="caption">
            <h3>Information</h3>
            <p><a href="http://www.shinken-monitoring.org/wiki/official/configuringshinken/configobjects/arbiter" class="" type="button">Arbiter:</a> The arbiter daemon reads the configuration, divides it into parts (N schedulers = N parts), and distributes them to the appropriate Shinken daemons.</p>
            <p><a href="http://www.shinken-monitoring.org/wiki/official/configuringshinken/configobjects/scheduler">Scheduler:</a> The scheduler daemon manages the dispatching of checks and actions to the poller and reactionner daemons respectively.</p>
            <p><a href="http://www.shinken-monitoring.org/wiki/official/configuringshinken/configobjects/poller">Poller:</a> The poller daemon launches check plugins as requested by schedulers. When the check is finished it returns the result to the schedulers.</p>
            <p><a href="http://www.shinken-monitoring.org/wiki/official/configuringshinken/configobjects/reactionner">Reactionner:</a> The reactionner daemon issues notifications and launches event_handlers. </p>
            <p><a href="http://www.shinken-monitoring.org/wiki/official/configuringshinken/configobjects/broker">Broker:</a> The broker daemon exports and manages data from schedulers. The broker uses modules exclusively to get the job done.</p>
            <p>Receiver (<b>optional</b>): The receiver daemon receives passive check data and serves as a distributed command buffer.</p>
            <p><a href="http://www.shinken-monitoring.org/wiki/shinken_10min_start" class="btn btn-success">Learn more »</a></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
