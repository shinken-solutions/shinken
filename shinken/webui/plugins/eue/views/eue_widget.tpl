%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%rebase widget globals(), css=['graphs/css/widget_graphs.css']

<div>
    <table class="table no-bottommargin topmmargin">
        <tbody>
            <tr>
                <td class="span7 no-border"><i class="icon-info-sign"></i> Date</td>
                <td class="no-border"><span>2012-05-23 23:15:00</span></td>
            </tr>
            <tr>
                <td class="span7"><i class="icon-ok font-green"></i> Succeed</td>
                <td><span class="badge badge-success">42</span></td>
            </tr>
            <tr>
                <td class="span7"><i class="icon-time font-yellow"></i> Pending</td>
                <td><span class="badge badge-warning">23</span></td>
            </tr>
            <tr>
                <td class="span7"><i class="icon-warning-sign font-red"></i> Failed</td>
                <td><span class="badge badge-important">43</span></td>
            </tr>
            <tr>
                <td class="span7 table-result"><i class="icon-tasks font-blue"></i><b> Totale</b></td>
                <td class="table-result"><span class="badge badge-info">108</span></td>
            </tr>
        </tbody>
    </table>
</div>