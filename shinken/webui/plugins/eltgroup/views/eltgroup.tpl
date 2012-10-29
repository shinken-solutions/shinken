%rebase layout globals()

<div id="" class="row-fluid">
	<div class="row-fluid box">	   
		<table class="span3">
			<tbody>
				<tr>
					<td>Name:</td>
					<td>generic-hosts</td>
				</tr>
				<tr>
					<td>Address:</td>
					<td>ERP</td>
				</tr>
			</tbody>
		</table>

		<table class="span2">
			<tbody>
				<tr>
					<td>Up: </td>
					<td> <span class="label label-success"> 42 </span> </td>
				</tr>
				<tr>
					<td>Down: </td>
					<td>  <span class="label label-important">5</span>  </td>
				</tr>
			</tbody>
		</table>

		<table class="span2">
			<tbody>
				<tr>
					<td>Unreachable: </td>
					<td> <span class="label label-important">23</span> </td>
				</tr>
				<tr>
					<td>Pending: </td>
					<td> <span class="label label-info">10</span> </td>
				</tr>
			</tbody>
		</table>

		<div class="progress span5">
			<div class="bar bar-success" style="width: 35%;"></div>
			<div class="bar bar-info" style="width: 20%;"></div>
			<div class="bar bar-danger" style="width: 10%;"></div>
			<div class="bar bar-warning" style="width: 35%;"></div>
		</div>	    

<!-- 		<div class="span4">
			<div class="alert alert-critical no-bottommargin pulsate row-fluid" style="opacity: 1;">
				<div style="font-size: 50px; padding-top: 10px;" class="span2"> <i class="icon-bolt"></i> </div>
				<p class="span10">This element has got an important impact on your business, please <b>fix it</b> or <b>acknowledge it</b>.</p>
			</div>
		</div> -->				
	</div>

	<div class="span12">
		<div class="row-fluid">
			<table class="table table-hover">
				<tbody>
					<tr>
						<th><em>Status</em></th>
						<th>Host</th>
						<th><em>Status</em></th>
						<th>Service</th>
						<th>Last Check</th>
						<th>Duration</th>
						<th>Attempt</th>
						<th>Status Information</th>
					</tr>
					<tr>
						<td ><em>UP</em></td>
						<td>
							<span><a href="#">localost</a></span>
						</td>
						<td><em>OK</em></td>

						<td style="white-space: normal">
							<span>Ping</span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>352d 23h 56m 56s</td>
						<td>1/3</td>
						<td>OK - localhost</td>	
					</tr>

					<tr>
						<td></td>
						<td>&nbsp;</td>
						<td><em>OK</em></td>
						<td>
							<span> <a href="#">Test</a> </span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>89d 17h 15m 59s</td>
						<td>1/1</td>
						<td>Service not intended for active checks</td>
					</tr>

					<tr>
						<td></td>
						<td>&nbsp;</td>
						<td><em>OK</em></td>
						<td>
							<span> <a href="#">Test</a> </span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>89d 17h 15m 59s</td>
						<td>1/1</td>
						<td>Service not intended for active checks</td>
						<td></td>
					</tr>
					<tr>
						<td ><em>UP</em></td>
						<td>
							<span><a href="#">orca</a></span>
						</td>
						<td><em>OK</em></td>

						<td style="white-space: normal">
							<span>Ping</span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>352d 23h 56m 56s</td>
						<td>1/3</td>
						<td>OK - localhost</td>
					</tr>

					<tr>
						<td></td>
						<td>&nbsp;</td>
						<td><em>OK</em></td>
						<td>
							<span> <a href="#">Test</a> </span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>89d 17h 15m 59s</td>
						<td>1/1</td>
						<td>Service not intended for active checks</td>
					</tr>

					<tr>
						<td></td>
						<td>&nbsp;</td>
						<td><em>OK</em></td>
						<td>
							<span> <a href="#">Test</a> </span>
						</td>
						<td>2012-07-30 22:53:03</td>
						<td>89d 17h 15m 59s</td>
						<td>1/1</td>
						<td>Service not intended for active checks</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="row-fluid pagination">
			<ul class="pull-right">
				<li><a href="#">Prev</a></li>
				<li><a href="#">1</a></li>
				<li><a href="#">2</a></li>
				<li><a href="#">3</a></li>
				<li><a href="#">4</a></li>
				<li><a href="#">Next</a></li>
			</ul>
		</div>
	</div>
</div>