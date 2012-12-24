%rebase layout globals(), css=['eue/css/eue.css','eue/css/datepicker.css','eue/css/bootstrap-timepicker.css'], js=['eue/js/jsquery.sparkline.js','eue/js/bootstrap-datepicker.js','eue/js/bootstrap-collapse.js','eue/js/bootstrap-modal.js','eue/js/bootstrap-tabs.js','eue/js/raphael.js','eue/js/morris.js','eue/js/bootstrap-timepicker.js'], title='End user experience reporting', menu_part='/apm'

%from shinken.bin import VERSION
%import datetime
%flag = platform["localization"].capitalize()

<!-- 
time picker is from : https://github.com/jdewit/bootstrap-timepicker/tree/master/js
    
-->


<!-- Log Contaier START -->
<div class="row well">
    <div class="span8">
        <h3>
        History : {{application}} {{feature}}
        </h3>
        <h5>{{description}}</h5>
    </div>
    <div class="span4">
        <table>
            <thead>
                <tr>
                    <th>OS</th><th>Browser</th><th>Localization</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>
                        <img alt="Feature run on {{platform["os"]}} platform" src="/static/eue/img/os/{{platform["os"]}}.png" style="width:32px;"/>
                    </td>
                    <td>
                        <img alt="Feature run on {{platform["browser"]}} browser" src="/static/eue/img/browser/{{platform["browser"]}}.png" style="width:32px;"/>
                    </td>
                    <td>
                        <img alt="Feature run in {{flag}}" src="/static/eue/img/flag/{{flag}}.png" style="width:32px;"/>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<button class="btn btn-danger" data-toggle="collapse" data-target="#graph">
  Graph
</button>
<div id="graph" class="collapse in"></div>

<div class="pagination">
    <ul>
        <li><a href="/eue_feature_history/{{eueid}}?lastts={{lastts}}&direction=prev">Prev</a></li>
        <li><a href="/eue_feature_history/{{eueid}}?lastts={{lastts}}&direction=next">Next</a></li>
    </ul>
</div>


<table class="table table-condensed"> 
    <thead>
        <tr>
            <th>Timestamp</th>
            <th>Date</th>
            <th>Duration</th>
            <th>State</th>
            <th>Succeed</th>
            <th>Failed</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        %for element in history:
        %if element["state"] == 0:
        %   badge = "badge-success"
        %else:
        %   badge = "badge-important"
        %end
        <tr>
            <td>{{element["timestamp"]}}</td>
            <td><a href="/eue_report/{{element["key"]}}">{{element["date"]}}</a></td>
            <td>{{element["duration"]}}</td>
            <td><span class="badge {{badge}}"></span></td>
            <td><span class="badge badge-success">{{element["succeed"]}}</span></td>
            <td><span class="badge badge-important">{{element["failed"]}}</span></td>
            <td><span class="badge badge-info">{{element["total"]}}</span></td>
        </tr>
        %end
    </tbody>
</table>

<div class="pagination">
    <ul>
        <li><a href="/eue_feature_history/{{eueid}}?lastts={{lastts}}&direction=prev">Prev</a></li>
        <li><a href="/eue_feature_history/{{eueid}}?lastts={{lastts}}&direction=next">Next</a></li>
    </ul>
</div>


<div class="modal hide" id="filter">
  <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal">×</button>
    <h3>Filter result</h3>
  </div>
  <div class="modal-body">
    <form class="well">
        <ul id="filtertabs" class="nav nav-tabs">
            <li class="active">
                <a href="#tabstates" data-toggle="tab">States</a>
            </li>
            <li>
                <a href="#tabdaterange" data-toggle="tab">Date range</a>
            </li>
            <li>
                <a href="#tabpagination" data-toggle="tab">Pagination</a>
            </li>
        </ul>
        <div id="filtertabscontent" class="tab-content">
            <div class="tab-pane fade in active" id="tabstates">
                <input type="hidden" id="daterangevalue" name="daterangevalue" value=""> 
                <fieldset>
                    <h5>States</h5>
                    <label class="radio">
                        <input type="radio" name="optionsStates" id="statesucceed" value="succeed"/> Succeed
                    </label>
                    <label class="radio">
                        <input type="radio"  name="optionsStates" id="statesfailed" value="failed"/> Failed
                    </label>
                    <label class="radio">
                        <input type="radio"  name="optionsStates" id="statesboth" value="both" /> Both
                    </label>
                </fieldset>
            </div>
            <div class="tab-pane fade" id="tabdaterange">
<!--                 From : 
                <div class="input-append date" id="date-from" data-date="12-02-2012" data-date-format="dd-mm-yyyy">
                    <input class="span2" size="16" type="text" value="12-02-2012" id="datefromval" readonly>
                    <span class="add-on"><i class="icon-th"></i></span>
                </div> 
                &nbsp;               
                <input class="time-from" type="text" style="width: 75px;" />
                <i class="icon-time" style="margin: -2px 0 0 -22.5px; pointer-events: none; position: relative;"></i>   --> 
                <div class="btngroup">
                    <a class="btn" href="javascript:setdaterange('1h')">1h</a>
                    <a class="btn" href="javascript:setdaterange('4h')">4h</a>
                    <a class="btn" href="javascript:setdaterange('1d')">1d</a>
                    <a class="btn" href="javascript:setdaterange('1w')">1w</a>                    
                    <a class="btn" href="javascript:setdaterange('2w')">2w</a>
                    <a class="btn" href="javascript:setdaterange('1m')">1m</a>
                    <a class="btn" href="javascript:setdaterange('6m')">6m</a>
                    <a class="btn" href="javascript:setdaterange('6m')">1y</a>
                </div>
            </div>
            <div class="tab-pane fade" id="tabpagination">
                <p>Howdy, I'm in Section 3.</p>
            </div>                
        </div>
        <button type="submit" class="btn">Filter</button>        
    </form>
  </div>
</div>

<script type="text/javascript">
var timestamp_data = {{morris}};
Morris.Line({
  element: 'graph',
  data: timestamp_data,
  xkey: 'period',
  ykeys: ['duration'],
  labels: ['duration'],
  dateFormat: function (x) { return new Date(x).toDateString(); }
});

$(document).ready(function () { 
    $('.time-from').timepicker({
        minuteStep: 1,
        secondStep: 5,
        showInputs: false,
        template: 'modal',
        modalBackdrop: true,
        showSeconds: true,
        showMeridian: false
    });

    $('.time-to').timepicker({
        minuteStep: 1,
        secondStep: 5,
        showInputs: false,
        template: 'modal',
        modalBackdrop: true,
        showSeconds: true,
        showMeridian: false
    });
});

function setdaterange(daterange){
    $('input[id=daterangevalue]').val(daterange)
    alert($('input[id=daterangevalue]').val())
}

$('#date-from').datepicker();

$(".collapse").collapse()

</script>

<!-- Log Contaier End -->