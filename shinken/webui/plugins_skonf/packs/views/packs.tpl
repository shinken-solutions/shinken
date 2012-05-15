
%rebase layout_skonf globals(), js=['packs/js/packs.js']

<div> <h1> Packs </h1> </div>


%for p in app.packs:
    <div class='well row'>
      <!-- {{p}} -->
      %pname = p.get_name()
      <div class='span1'>
	<span class="label">
	  <img class="imgsize3" onerror="$(this).hide()" src="/static/images/sets/{{pname}}/tag.png" /> {{pname}}
	</span>
      </div>
      <div class='span7'>
	{{p.description}}
      </div>
      <div class='span2'>
      %tpl, services = app.datamgr.related_to_pack(pname)
      %if tpl:
         %tname = tpl.get('name', '')
         <div> Host template : <a href='/elemments/hosts/{{tname}}'> {{tname}}</a></div>
      %else:
         <div class="alert">No host template for this pack!</div>
      %end
      </div>
      %if len(services) == 0:
	 <div class="alert">No services enabled for this pack</div>
      %end
      <a class='btn btn-success pull-right' href="javascript:show_services_list('{{pname}}');"> Show services</a>
      <div id='services-{{pname}}' class='services_list span10'>
      %for s in services:
	 %sid = s.get('_id', '')
	 %sname = s.get('service_description', 'unknown')
          <div class=''><a href='/elemments/services/{{sid}}'> {{sname}}</a></div>
      %end
      </div>

    </div>
%end



