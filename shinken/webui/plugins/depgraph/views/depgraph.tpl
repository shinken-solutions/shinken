

%print 'Host value?', host
%import time

%# If got no Host, bailout
%if not host:
%include header title='Invalid host'

Invalid host
%else:

%helper = app.helper
%datamgr = app.datamgr


%include header title='Dependenci graph of ' + host.host_name,  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js', 'depgraph/js/hide.js', 'depgraph/js/switchbuttons.js', 'depgraph/js/multibox.js', 'depgraph/js/multi.js' ],  css=['depgraph/eltdeps.css', 'depgraph/tabs.css', 'depgraph/hostdetail.css', 'depgraph/switchbuttons.css', 'depgraph/hide.css', 'depgraph/multibox.css'],  print_menu=False




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

