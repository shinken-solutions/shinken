
%rebase layout_skonf globals(), title="Discovery scan results", css=['newhosts/css/results.css', 'newhosts/css/token-input.css', 'newhosts/css/token-input-facebook.css'], js=['newhosts/js/results.js', 'newhosts/js/jquery.tokeninput.js']

<div class='span10 offset2 well'>
  <p>Here are the scans:</p>
  %for s in scans:
  %if s['state'] == 'done':
  <div class="alert alert-info">
  %elif s['state'] in ['preparing', 'launched']:
  <div class="alert alert-success">
  %else:
  <div class="alert alert-error">
  %end
  <a class="close" data-dismiss="alert" href="#">x</a>
    {{s}}
  </div>

  %end
</div>

<p class='span8 pull-left'>Here are the results:</p>



%for h in pending_hosts:
     %hname = h['host_name']
     <div id="host-{{h['host_name']}}" class="span7 offset1 discovered_host well">
      <!-- "{{h}}" -->
     <a id='show_form-{{hname}}' class='show_form btn pull-left' href='javascript:show_form("{{h['host_name']}}")'>
         <i class="icon-chevron-down"></i>
       </a>
     <div id='delete-host-{{hname}}' class="btn-group pull-right">
       <a class="btn btn-warning dropdown-toggle" data-toggle="dropdown" href="#">
	 <i class="icon-remove"></i>
	 <span class="caret"></span>
       </a>
       <ul class="dropdown-menu">
	 <a href='javascript:delete_discovery_host("{{hname}}");'>
	   <i class="icon-minus"></i> Delete
	 </a>
	 <a href='javascript:delete_forever_discovery_host("{{hname}}");'>
	   <i class="icon-remove"></i> Delete forever
	 </a>
       </ul>
     </div>
     <form id="form-{{h['host_name']}}" method="post" name="form-{{h['host_name']}}" action="/newhosts/validatehost">
       <span class="row">
	 <input name="_id" type="hidden" value="{{h['_id']}}"/>
	 <span class="span10">

           <input name="host_name" type="text" tabindex="1" value="{{h['host_name']}}" id="form-host_name-{{h['host_name']}}"/>
	   <span class="help-inline"> Hostname</span>
         </span>
	 <span class="span10">
	   <input id='input-{{h['host_name']}}' class='to_use_complete' data-use='{{h['use']}}' name="use" type="text" tabindex="2"  />
	   <span class="help-inline"> Tags</span>
	 </span>
       </span>
     </form>
     <span class="span10">
       <span id='loading-'{{h['host_name']}} class='ajax-loading pull-right'></span>
       <a id='btn-validate-{{h['host_name']}}'  class='btn btn-info pull-right' href='javascript:validatehostform("{{h['host_name']}}")'>
	 <i class="icon-ok"></i> Validate
       </a>
       <div id="push-result-{{hname}}" class='span8 alert push-result'>
       </div>

     </span>


     </div>


%end



