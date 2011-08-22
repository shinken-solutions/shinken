

%print 'Host value?', host
%import time

%# If got no Host, bailout
%if not host:
%include header title='Invalid host'

Invalid host
%else:

%helper = app.helper
%datamgr = app.datamgr

%top_right_banner_state = datamgr.get_overall_state()


%include header title='Host detail about ' + host.host_name,  js=['hostdetail/js/jit-yc.js', 'hostdetail/js/excanvas.js', 'hostdetail/js/eltdeps.js', 'hostdetail/js/hide.js', 'hostdetail/js/switchbuttons.js', 'hostdetail/js/multibox.js', 'hostdetail/js/multi.js' ],  css=['hostdetail/eltdeps.css', 'hostdetail/tabs.css', 'hostdetail/hostdetail.css', 'hostdetail/switchbuttons.css', 'hostdetail/hide.css', 'hostdetail/multibox.css'], top_right_banner_state=top_right_banner_state,  print_menu=False




<script type="text/javascript">
  var graph_root = '{{host.get_name()}}';   /*'test_host_0';*/
  var json_graph = {{helper.create_json_dep_graph(host, levels=3)}};
</script>


<div id="infovis"> </div>
<div id="right-container">
  <div id="inner-details"></div>
</div>

<div id="log">Loading host informations...</div>
</div>
	
<div class="clear"></div>
</div>

%#End of the Host Exist or not case
%end

%include footer

