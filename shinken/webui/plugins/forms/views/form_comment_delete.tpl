<script type="text/javascript">
	function submit_local_form() {
		var form = document.forms['modal_form'];
		var comment = form.comment.value;

		add_comment("{{name}}", '{{user.get_name()}}', comment);
		$('#modal').modal('hide')
	}
</script>

<div class="modal-header">
	<a class="close" data-dismiss="modal">×</a>
	<h3>Delete all comments on {{name}}</h3>
</div>

<div class="modal-body">
<!-- 	<form class="well" name='modal_form'>
		<textarea type="textarea" name='comment' class="span4" rows=5 placeholder="Comment…"/>
		<span class="help-inline">Comment</span>
	</form> -->
</div>

<div class="modal-footer">
	<a href="javascript:submit_local_form();" class="btn btn-danger"> <i class="icon-trash"></i> Delete</button>
	<a href="#" class="btn" data-dismiss="modal">Cancel</a>
</div>
