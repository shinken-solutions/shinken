%rebase layout title='Shinken UI login', print_menu=False



%# " If the auth succeed, we go in the /problems page "
%if sid is not None:
<script type="text/javascript">
  window.location.replace("/problems");
</script>
%else: # " Ok, not good, came back at login page."
<script type="text/javascript">
  window.location.replace("/login");
</script>
%end
