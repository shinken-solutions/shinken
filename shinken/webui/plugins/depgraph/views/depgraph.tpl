

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


%rebase layout globals(), title='Dependencies graph of ' + elt.get_full_name(),  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js'],  css=['depgraph/css/eltdeps.css'],  print_menu=False, refresh=True




<script type="text/javascript">

  // Now we hook teh global search thing
  $('.typeahead').typeahead({
    // note that "value" is the default setting for the property option
    source: function (typeahead, query) {
      $.ajax({url: "/lookup/"+query,
        success: function (data){
          typeahead.process(data)}
        });
      },
    onselect: function(obj) {
      $("ul.typeahead.dropdown-menu").find('li.active').data(obj);
    }
  });


$(document).ready(init_graph('{{elt.get_full_name()}}', {{!helper.create_json_dep_graph(elt, levels=4)}},700, 700,'{{helper.get_html_id(elt)}}'));

</script>


<div id="infovis-{{helper.get_html_id(elt)}}"> </div>
<div id="right-container" class="border">
  <div id="inner-details-{{helper.get_html_id(elt)}}">
</div>

<div id="log">Loading element informations...</div>


<div class="clear"></div>


%#End of the Host Exist or not case
%end



