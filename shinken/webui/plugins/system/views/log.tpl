%rebase layout globals(), css=['system/css/log.css'], title='Architecture state', menu_part='/system'

%from shinken.bin import VERSION
%helper = app.helper
 <div class="alert alert-error alert-block span11">
    <a class="close" data-dismiss="alert" href="#">×</a>
    <h4 class="alert-heading">Warning!</h4>
    No Live Data
 </div>

<!-- Log Contaier START -->
<h2>System logs</h2>
<div class="pagination pull-right">
    <ul>
        <li><a href="#">Prev</a></li>
        <li class="active"><a href="#">1</a></li>
        <li><a href="#">2</a></li>
        <li><a href="#">3</a></li>
        <li><a href="#">4</a></li>
        <li><a href="#">Next</a></li>
    </ul>
</div>

<div id="log_container" class="tabbable tabs-left leftmargin span12">
    <ul class="nav nav-tabs span3">
        <li class="active"><a data-toggle="tab" href="#lA">Week 1</a></li>
        <li><a data-toggle="tab" href="#lB">Week 2</a></li>
        <li><a data-toggle="tab" href="#lC">Week 3</a></li>
    </ul>
    <div class="tab-content span9 pull-right no-leftmargin">
        <div id="lA" class="tab-pane active">
        	<p>I'm in Section A.</p>
       		<ol>
				<li>Ent 1</li>
				<li class="row_alt">Ent 2</li>
				<li>Ent 3</li>
			</ol>
        </div>
        <div id="lB" class="tab-pane">
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
        <div id="lC" class="tab-pane">
            <p>What up girl, this is Section C.</p>
        </div>
    </div>
</div>
<div class="pagination pull-right">
    <ul>
        <li><a href="#">Prev</a></li>
        <li class="active"><a href="#">1</a></li>
        <li><a href="#">2</a></li>
        <li><a href="#">3</a></li>
        <li><a href="#">4</a></li>
        <li><a href="#">Next</a></li>
    </ul>
</div>
<!-- Log Contaier End -->