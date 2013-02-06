
<link href="/static/cv_memory/css/memory.css" rel="stylesheet">

<div id='cv_processes_cont'>
  <table class='table-bordered table-striped table-hover table-condensed' id='host_processes'>
  <thead>
    <th data-sort="string">User</th>
    <th>Pid</th>
    <th id='processes_th_cpu' data-sort="float" >%CPU</th>
    <th id='processes_th_mem' data-sort="float">%Mem</th>
    <th data-sort="int">VSZ</th>
    <th data-sort="int">RSS</th>
    <th>Status</th>
    <th>Command</th>
  </thead>
    <tbody>
      %for p in ps:
      <tr>
	<td>{{p['username']}}</td>
	<td>{{p['pid']}}</td>
	<td>{{p['cpu_percent']}}</td>
	<td>{{'%.1f' % p['memory_percent']}}</td>
	<td>{{p['memory_info'][1]}}</td>
	<td>{{p['memory_info'][0]}}</td>
	<td>{{p['status']}}</td>
	<td>{{p['name']}}</td>
      </tr>
      %end
    </tbody>
  </table>
</div>


<script>
$(function(){
var table = $("#host_processes").stupidtable();

/* Add a callback to add remove arrow */
table.bind('aftertablesort', function (event, data) {
    // data.column - the index of the column sorted after a click
    // data.direction - the sorting direction (either asc or desc)

    var th = $(this).find("th");
    th.find(".arrow").remove();
    var arrow = data.direction === "asc" ? "↑" : "↓";
    th.eq(data.column).append('<span class="arrow">' + arrow +'</span>');
});

// Simulate a click on the CPU by default; twice
$('#processes_th_mem').trigger('click');
$('#processes_th_mem').trigger('click');

});

</script>

