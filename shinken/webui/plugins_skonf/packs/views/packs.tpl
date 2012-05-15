
%rebase layout_skonf globals(), js=['packs/js/packs.js']

<div> <h1> Packs </h1> </div>


%for p in app.packs:
    <div class='well'>
      <!-- {{p}} -->
      %pname = p.get_name()
      <p> <span class="label"><img class="imgsize3" onerror="$(this).hide()" src="/static/images/sets/{{pname}}/tag.png" /> {{pname}}</span> : {{p.description}}</p>
      <br/>
      %tpl, services = app.datamgr.related_to_pack(pname)
      %if tpl:
         %tname = tpl.get('name', '')
         <div> Host template : <a href='/elemments/hosts/{{tname}}'> {{tname}}</a></div>
      %else:
         <div class="alert">No host template for this pack!</div>
      %end
      
      %if len(services) == 0:
	 <div class="alert">No services enabled for this pack</div>
      %end
      <a class='btn btn-success' href="javascript:show_services_list('{{pname}}');"> Show services</a>
      <div id='services-{{pname}}' class='services_list'>
      %for s in services:
	 %sid = s.get('_id', '')
	 %sname = s.get('service_description', 'unknown')
         <div class='offset1'><a href='/elemments/services/{{sid}}'> {{sname}}</a></div>
      %end
      </div>

    </div>
%end



