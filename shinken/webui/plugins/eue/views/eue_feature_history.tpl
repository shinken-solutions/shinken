%rebase layout globals(), css=['eue/css/eue.css'], js=['eue/js/jsquery.sparkline.js'], title='End user experience reporting', menu_part='/apm'

%from shinken.bin import VERSION
%import datetime
%flag = platform["localization"].capitalize()
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
<table class="table table-condensed"> 
    <thead>
        <tr>
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
<!-- Log Contaier End -->