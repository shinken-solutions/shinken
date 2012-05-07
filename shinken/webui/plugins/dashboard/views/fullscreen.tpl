%rebase layout globals(), css=['dashboard/css/fullscreen.css'], title='Architecture state', menu_part='/dashboard', print_header=False

%from shinken.bin import VERSION
%helper = app.helper

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