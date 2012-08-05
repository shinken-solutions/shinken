%rebase layout globals(), css=['eue/css/eue.css','eue/js/videojs/video-js.min.css','eue/css/jquery.lightbox-0.5.css'], js=['eue/js/jquery.lightbox-0.5.js','eue/js/videojs/video.js','eue/js/jsquery.sparkline.js'], title='End user experience reporting', menu_part='/apm'

%from shinken.bin import VERSION
%import datetime

%if len(eue_data) > 0:
%helper = app.helper
%total_succeed = 0
%total_failed = 0
%total = 0
%total_time = 0
%human_date = datetime.datetime.fromtimestamp(eue_data["start_time"]).strftime('%Y-%m-%d %H:%M:%S')

%for scenario,scenario_data in eue_data["scenarios"].items():
%   if int(scenario_data["status"]) != 0:
%       total_failed += 1
%   else:
%       total_succeed += 1
%   end
%end

%total = total_succeed + total_failed


%succeedmetrics = []
%failedmetrics = []
%totalmetrics = []
%for record in records:
    %succeedmetrics.append(str(record["succeed"]))
    %failedmetrics.append(str(record["failed"]))
    %totalmetrics.append(str(record["total"]))
%end

%poster=""

<!-- Log Contaier START -->
<div class="row well">
    <div class="span12">
        <div class="span8">
            <h3>
                {{eue_data["application"]}} : {{eue_data["feature"]}}
            </h3>
            <div class="span8"><span id="durations"></span></div>
            <div class="span8"><span id="states"></span></div>
        </div>
        <div class="span3 offset1">
            <table class=" well table table-condensed">
                <tbody>
                    <tr><td><i class="icon-calendar"/></i> Date :</td><td><span class="">{{human_date}}</span></td></tr>
                    <tr><td><i class="icon-ok"/></i>Succeed :</td><td><span class="badge badge-success">{{total_succeed}}</span></td></tr>
                    <tr><td><i class="icon-remove"/></i>Failed :</td><td><span class="badge badge-important">{{total_failed}}</span></td></tr>                            
                    <tr><td><i class="icon-list-alt"/></i>Total :</td><td><span class="badge badge-info">{{total}}</span></td></tr>                                                        
                </tbody>
            </table>
        </div>
    </div>
</div>
<div class="row well">
        <div class="span12">
            <div class="span8">
                <b>Scénario</b>
            </div>
            <div class="span1">
                <b>Result</b>
            </div>
            <div class="span1">
                <b>Duration</b>
            </div>
            <div class="span1">
                <b>Screenshot</b>
            </div>
        </div>
</div>
%scenarios = eue_data["scenarios"]
%for scenario_key in sorted(scenarios,key = lambda k: scenarios[k]['index']):
%   scenario = scenario_key
%   data_scenario = scenarios[scenario_key]
%
%   scenario_duration = "%.2fs" % data_scenario["duration"]
%   steps = data_scenario["steps"]
%   if int(data_scenario["status"]) == 0:
%       scenario_status = "Succeed"
%       scenario_badge = "badge-success"
%   else:
%       scenario_status = "Failed"
%       scenario_badge = "badge-important"
%   end
    <div class="row well">
        <div class="span12">
            <div class="span8">
                <span class="tgreen tbold">{{scenario}}</span>
                <blockquote>
                <ul>
                %for step in sorted(steps, key = lambda k: k['index']):
                %   if int(step["status"]) == 0:
                <i></i><span class="badge badge-success">S</span>&nbsp;<span>{{step["step"]}}</span><br/>
                %   else:
                <i></i><span class="badge badge-important">F</span>&nbsp;<span>{{step["step"]}}</span><br/>
                %   end
                %end
                </ul>
                </blockquote>
            </div>
            <div class="span1">
                <span class="badge {{scenario_badge}}">{{scenario_status}}</span>
            </div>
            <div class="span1 tbold">{{scenario_duration}}</div>
            %if poster == "":
            %   poster=data_scenario["screenshot"]
            %end
            <div class="span1">
                %if data_scenario["screenshot"]:
                <a href="/eue_media/{{data_scenario["screenshot"]}}" class="lightbox"><img src="/eue_media/{{data_scenario["screenshot"]}}" width="100" height="60" alt=""/></a>
                %end
            </div>
        </div>
    </div>
%end
    %if eue_data["video"]:
    <div class="row well">
        <div class="span12 offset4">
            <video id="replay" class="video-js vjs-default-skin" controls preload="auto" width="640" height="480" poster="/eue_media/{{poster}}" data-setup="{}">
              <source src="/eue_media/{{eue_data["video"]}}" type='video/ogg'>
            </video>
        </div>
    </div>
    %end
<script type="text/javascript">
    $(function() {
        $('a.lightbox').lightBox(); // Select all links with lightbox class
    });

    $("#durations").sparkline([{{durations}}], {
        type: 'bar',
        height: '25 ',
        barWidth: 5,
        barColor: '#007fff'});


    $("#states").sparkline([{{states}}], {
        type: 'tristate',
        height: '25',
        barWidth: 5});

</script>
%else:
<div class="row well">
    <div class="span12">
        Nothing to see ....
    </div>
</div>
%end
<!-- Log Contaier End -->