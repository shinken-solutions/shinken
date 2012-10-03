%import time
%now = time.gmtime(int(time.time()))
%nxt = time.gmtime(int(time.time()) + 3600*2)

%s_now_day = time.strftime("%Y/%m/%d", now)
%s_now_hour = time.strftime("%H:%M", now)

%s_nxt_day = time.strftime("%Y/%m/%d", nxt)
%s_nxt_hour = time.strftime("%H:%M", nxt)

<script type="text/javascript">
	function submit_local_form(){
	  var form = document.forms['modal_form'];

	  var from_day = form.from_day.value;
	  var from_hour = form.from_hour.value;
	  var to_day = form.to_day.value;
	  var to_hour = form.to_hour.value;

	// BEWARE: it's ugly, but guess what? It ork like that
	// so if you want it better, take your emacs and help on this :)
	// and why parse 2 times? Becaue javascript is buggy as hell!
	// cf: http://www.breakingpar.com/bkp/home.nsf/0/87256B280015193F87256C85006A6604
	// Now parse the from date
	  var elts = from_day.split('/');
	  var from_Y = parseInt(parseFloat(elts[0]));
	  // Beware: Date start at 0...
	  var from_M = parseInt(parseFloat(elts[1])) - 1;
	  var from_D = parseInt(parseFloat(elts[2]));
	  var elts = from_hour.split(':');
	  var from_H = parseInt(parseFloat(elts[0]));
	  var from_m = parseInt(parseFloat(elts[1]));

	  var from_date = new Date(from_Y, from_M, from_D, from_H, from_m, 0);
	  var from_epoch = from_date.getTime()/1000.0;

	// And now the To date
	var elts = to_day.split('/');
          var to_Y = parseInt(parseFloat(elts[0]));
          var to_M = parseInt(parseFloat(elts[1])) - 1;
          var to_D = parseInt(parseFloat(elts[2]));
          var elts = to_hour.split(':');
          var to_H = parseInt(parseFloat(elts[0]));
          var to_m = parseInt(parseFloat(elts[1]));

	var to_date = new Date(to_Y, to_M, to_D, to_H, to_m, 0);
        var to_epoch = to_date.getTime()/1000.0;

	// Maybe the user is a moron and put before after end...
	if(from_epoch > to_epoch){
	  $('#dateinversion').animate({height: 'toggle'});//toggle();
	  return;
	}

	var reason = form.reason.value;

	// Launch and bailout this modal view
	do_schedule_downtime("{{name}}", from_epoch, to_epoch, '{{user.get_name()}}', reason);
	$('#modal').modal('hide')
	}


	$(function() {
	$('[data-datepicker]').datepicker();
	});
</script>

<div class="modal-header">
	<a class="close" data-dismiss="modal">×</a>
	<h3>Schedule downtime for {{name}}</h3>
</div>

<div class="modal-body">
	<form class="well" name='modal_form'>
		<label>Downtime date range</label>
		<div class='input'>
			<div class="inline-inputs">
				From
				<input name='from_day' data-datepicker="datepicker" class="input input-small" type="text" value="{{s_now_day}}" />
				<input name='from_hour' class="input input-mini" type="text" value="{{s_now_hour}}" />
				to
				<input name='to_day' data-datepicker="datepicker" class="input input-small" type="text" value="{{s_nxt_day}}" />
				<input name='to_hour' class="intput input-mini" type="text" value="{{s_nxt_hour}}" />
			</div>
		</div>
		<textarea type="textarea" name='reason' class="span6" placeholder="Reason…" rows=5></textarea>
	</form>
</div>

<div class="modal-footer">
	<div class="error" id='dateinversion'>
		<p><strong>Error:</strong> Your ending date is before the starting one!</p>
	</div>
	<a href="javascript:submit_local_form();" class="btn btn-primary">Submit</button>
	<a href="#" class="btn" data-dismiss="modal">Close</a>
</div>

<script type="text/javascript">
  $('#dateinversion').hide();
</script>