

%print 'Elt value?', elt
%import time

%# If got no Element, bailout
%if not elt:
%rebase layout title='Invalid element name'

Invalid element

%# " If we got auth problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here." 
%end


%else:

%helper = app.helper
%datamgr = app.datamgr


%rebase layout title='Dependencies graph of ' + elt.get_full_name(),  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js'],  css=['depgraph/css/eltdeps.css'],  print_menu=False




<script type="text/javascript">
  var graph_root = '{{elt.get_full_name()}}';
  var json_graph = {{!helper.create_json_dep_graph(elt, levels=4)}};
</script>


<div id="infovis"> </div>
<div id="right-container" class="border">
%#  <div class="border"></div>
  <div id="inner-details"></div>
</div>

<div id="log">Loading element informations...</div>
</div>
	
<div class="clear"></div>
</div>

%#End of the Host Exist or not case
%end

%include footer

