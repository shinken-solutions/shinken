%rebase layout_mobile globals(), css=['mobile/css/log.css'], title='System logs', menu_part='/log'

%from shinken.bin import VERSION
%helper = app.helper


<div data-role="collapsible-set" data-iconpos="right">

	<div data-role="collapsible" >
		<h2>Datum 1</h2>
			<ol>
				<li>Ent 1</li>
				<li>Ent 2</li>
				<li>Ent 3</li>
			</ol>
		</div>
	<div data-role="collapsible" >
		<h2>Datum 2</h2>
		<ol>
			<li>Ent 1</li>
			<li>Ent 2</li>
			<li>Ent 3</li>
			<li>Ent 3</li>
			<li>Ent 4</li>
			<li>Ent 6</li>
			<li>Ent 7</li>
			<li>Ent 8</li>
			<li>Ent 9</li>
			<li>Ent 10</li>
		</ol>
	</div>
</div>
