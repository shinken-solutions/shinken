%rebase layout globals(), css=['system/css/log.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper

%#  "Left Container Start"
<div id="left_container" class="grid_2">
	<div id="nav_left">
		<ul>
			<li><a href="/system">System</a></li>
			<li><a href="/system/log">Log</a></li>
		</ul>
	</div>
</div>
%#  "Left Container End"

<div id="system_overview" class="grid_14 item">
	
	<div id="messagebox" class="gradient_alert" style="margin-top: 20px;">
		<img src="/static/images/icons/alert.png" alt="some_text" style="height: 40px; width: 40px" class="grid_4"/> 
		<p><strong>Mockup</strong></p>
	</div>
	
	<h2>Log</h2>
	<!-- stats overview start -->

	<!-- stats overview end -->
</div>

<!-- Log Contaier START -->

<div id="log_container" class="grid_14">
	<h2>Datum 1</h2>
	<ol>
		<li>Ent 1</li>
		<li class="row_alt">Ent 2</li>
		<li>Ent 3</li>
	</ol>
					
	<h2>Datum 2</h2>
	<ol>
		<li>Ent 1</li>
		<li class="row_alt">Ent 2</li>
		<li>Ent 3</li>
		<li class="row_alt">Ent 3</li>
		<li>Ent 4</li>
		<li class="row_alt">Ent 6</li>
		<li>Ent 7</li>
		<li class="row_alt">Ent 8</li>
		<li>Ent 9</li>
		<li class="row_alt">Ent 10</li>
	</ol>
</div>
<!-- Log Contaier START -->