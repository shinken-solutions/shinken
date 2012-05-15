
%rebase layout_skonf globals(), js=['packs/js/packs.js']

<div> <h1> Packs </h1> </div>

%treename = ''
%for e in app.datamgr.get_pack_tree(app.packs):
    %print "ENTRY", e
    %if e['type'] == 'new_tree':
       %treename = e['name']
       <div class='well'> {{e['name'].capitalize()}}  <a href='javascript:toggle_tree("{{e['name']}}")';> <i class="icon-chevron-up"></i> </a>
    %elif e['type'] == 'end_tree':
       </div>
    %else:
       %p = e['pack']
  
    <div class='row {{treename}}'>
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
      %lst = app.datamgr.related_to_pack(p)
      %print "LST", lst
      %for _t in lst:
        %(tpl, services) = _t
        %if tpl:
           %tname = tpl.get('name', '')
           <div> Host tag : <a href='/elemments/hosts/{{tname}}'> {{tname}}</a>
	     <a class='pull-right' href="javascript:show_services_list('{{tname}}');"> <i class="icon-chevron-down"></i></a>      
	   </div>
        %else:
           <div class="alert">No host template for this pack!</div>
        %end
      %end
      </div>

      <div class='span10'>
      %for _t in lst:
         %(tpl, services) = _t
	 <div id="services-{{tpl.get('name', '')}}" class='services_list'>
         %if len(services) == 0:
	   <div class="alert">No services enabled for this pack</div>
	 %else:
	   <b> {{tpl.get('name', '')}} services : </b>
         %end

	 %for s in services:
	   %sid = s.get('_id', '')
	   %sname = s.get('service_description', 'unknown')
           <div class=''><a href='/elemments/services/{{sid}}'> {{sname}}</a></div>
	 %end
	</div>
      %end
      </div>

    </div>

   %end
%end



