<script type="text/javascript">
function submit_local_form() {
	var form = document.forms['modal_form'];

	var comment = form.downtime.value;

	delete_all_downtimes('{{name}}');
	$('#modal').modal('hide')
}
</script>

<div class="modal-header">
	<a class="close" data-dismiss="modal">×</a>
	<h3>Delete Confirmation</h3>
</div>
<div class="modal-body">
	<form class="well" name='modal_form'>
		<textarea type="textarea" name='downtime' class="span4 hide" rows=5 placeholder="Comment…"/>
		<span class="help-inline">Are you sure you want to delete all downtimes?</span>
	</form>
</div>
<div class="modal-footer">
	<a href="javascript:submit_local_form();" class="btn btn-danger"> <i class="icon-trash"></i> Delete</button></a>
	<a href="#" class="btn" data-dismiss="modal">Close</a>
</div>