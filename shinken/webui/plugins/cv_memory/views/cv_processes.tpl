
<link href="/static/cv_memory/css/memory.css" rel="stylesheet">

<div id='cv_processes_cont'>
  <table>
    <th>User</th>
    <th>Pid</th>
    <th>%CPU</th>
    <th>%Mem</th>
    <th>VSZ</th>
    <th>RSS</th>
    <th>Status</th>
    <th>Command</th>
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
