%rebase layout_mobile globals(), css=['mobile/css/details.css'], title='Details'

<div data-role="collapsible-set" data-iconpos="right" >

	<div data-role="collapsible" data-collapsed="false" >
	<h2>Informations</h2>
		<table>
			<tbody><tr>
			  <td>Alias:</td>
			  <td>sw-bldg2-floor2</td>
			</tr>
		 	<tr>
			  <td>Address:</td>
			  <td>66.66.66.66</td>
			</tr>
			<tr>
			  <td>Parents:</td>
			  <td>rt-bldg2</td>
			</tr>
			<tr>
			  <td>Members of: </td>
			  <td>switches</td>
			</tr>
		</tbody></table>
	</div>
	<div data-role="collapsible" >
	<h2>Service Information:</h2>

		<table>
			<tbody>
			<tr>
			  <td>Service Status</td>
			  <td><span class="alert-small alert-critical">CRITICAL</span> (since 18m 44s) </td>
			</tr>
			<tr>
			  <td>Status Information</td>
			  <td>/bin/sh: /usr/lib/nagios/plugins/check_disk: not found</td>
			</tr>
			<tr>
			  <td>Performance Data</td>
			  <td>&nbsp;</td>
			</tr>
			<tr>
			  <td>Current Attempt</td>
			  <td>1/1 (HARD state)</td>
			</tr>
			<tr>
			  <td>Last Check Time</td>
			  <td><span class="quickinfo" data-original-title="Last check was at Fri Apr 13 19:45:30 2012">was 2m 33s ago</span></td>
			</tr>
			<tr>
			  <td>Next Scheduled Active Check</td>
			  <td><span class="quickinfo" data-original-title="Next active check at Fri Apr 13 19:50:31 2012">in 2m 28s</span></td>
			</tr>
			<tr>
			  <td>Last State Change</td>
			  <td>Fri Apr 13 19:29:19 2012</td>
			</tr>
		    </tbody>
		</table>

		      <div data-role="collapsible" >
			      <h3>Additonal Informations:</h3>
			      	<table>
						<tbody><tr>
						  <td>Last Notification</td>
						  <td>Fri Apr 13 19:30:22 2012 (notification 1)</td>
						</tr>
						<tr>
						  <td>Check Latency / Duration</td>
						  <td>1.07 / 0.05 seconds</td>
						</tr>
						<tr>
						  <td>Is This Host Flapping?</td>
						  <td>No (2.71% state change)</td>
						</tr>
						<tr>
						  <td>In Scheduled Downtime?</td>
						  <td>No</td>
						</tr>
						</tbody>
					</table>

		   	 </div>
	</div>
	<div data-role="collapsible" >
	<h2>Show dependency tree</h2>
		<p>rt-bldg2 is UP since 3w 12h 9m 2s</p>
	</div>
	<div data-role="collapsible" >
	<h2>Impact</h2>
	     <p>websrv1/WWW is CRITICAL since 3w 11h</p>
		 <p>sw-bldg2-floor2/os_ios_default_check_hardware is CRITICAL since 3w 12h</p>
		 <p>dbsrv1/os_linux_default_check_cron is CRITICAL since 3w 12h</p>
		 <p>dbsrv1/app_db_oracle_WWW_tbs_USERS_check_free is CRITICAL since 3w 12h</p>
		 <p>dbsrv1/os_linux_default_check_shell is CRITICAL since 3w 12h</p>
		 <p>dbsrv1/os_linux_default_check_inetd is CRITICAL since 3w 12h</p>
		 <p>dbsrv1/app_db_oracle_WWW_check_connect is CRITICAL since 3w 12h</p>
	</div>
</div>
