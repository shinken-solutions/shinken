

<script type="text/javascript">
	function submit_local_form()
	{
	var form = document.forms['modal_form'];

	var reason = form.reason.value;

	do_acknowledge("{{name}}", reason, '{{user.get_name()}}');
	$('#modal').modal('hide')
	}


</script>


<div class="modal-header">
  <a class="close" data-dismiss="modal">×</a>
  <h3>Acknowledge {{name}}</h3>
</div>
<div class="modal-body">
  <form class="well" name='modal_form'>
    <input type="textarea" name='reason' class="span3" placeholder="Reason…">
    <span class="help-inline">Reason</span>

</form>

</div>
<div class="modal-footer">
  <a href="javascript:submit_local_form();" class="btn btn-primary">Submit</button>
  <a href="#" class="btn" data-dismiss="modal">Close</a>
</div>
