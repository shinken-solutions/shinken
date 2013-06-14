

<script type="text/javascript">
	function submit_local_form()
	{
	var form = document.forms['modal_form'];

	var output = form.output.value;
	var return_code = form.return_code.value;

	//form.submit();
	submit_check("{{name}}", return_code, output);
	$('#modal').modal('hide')
	}
</script>


<div class="modal-header">
  <a class="close" data-dismiss="modal">×</a>
  <h3>Submit check for {{name}}</h3>
</div>
<div class="modal-body">
  <form class="well" name='modal_form'>
    <select name='return_code'>
	%if obj_type == 'host':
        <option value='0'>UP</option>
        <option value='1'>DOWN</option>
	%else:
	<option value='0'>OK</option>
        <option value='1'>WARNING</option>
        <option value='2'>CRITICAL</option>
        <option value='3'>UNKNOWN</option>
	%end
    </select>
    <span class="help-inline">Status</span>

    <input type="text" name='output' class="span3" placeholder="Output…">
    <span class="help-inline">Text output</span>

</form>

</div>
<div class="modal-footer">
  <a href="javascript:submit_local_form();" class="btn btn-primary">Submit</button>
  <a href="#" class="btn" data-dismiss="modal">Close</a>
</div>
