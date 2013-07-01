%helper = app.helper

%rebase layout css=['flow/css/zflow.css', 'flow/css/wall.css'], title='Flow view', js=['flow/js/zflow.js', 'flow/js/init.js'], refresh=True, user=user, print_menu=False, print_header=True




<div class="zflow centering">
    <div id="tray" class="tray"></div>
</div>


<script type="text/javascript">
var images = {{!impacts}};
</script>


