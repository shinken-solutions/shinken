%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%rebase widget globals(), css=['graphs/css/widget_graphs.css']

<div>
    <table class="table table-striped table-bordered">
        <tbody>
            <tr>
                <td class="span7">Date</td>
                <td><span>2012-05-23 23:15:00</span></td>
            </tr>
            <tr>
                <td class="span7">Succeed</td>
                <td><span class="badge badge-success">42</span></td>
            </tr>
            <tr>
                <td class="span7">Pending</td>
                <td><span class="badge badge-info">23</span></td>
            </tr>
            <tr>
                <td class="span7">Failed</td>
                <td><span class="badge badge-important">43</span></td>
            </tr>
            <tr>
                <td class="span7"><b>Totale</b></td>
                <td><span class="badge">108</span></td>
            </tr>
        </tbody>
    </table>
</div>