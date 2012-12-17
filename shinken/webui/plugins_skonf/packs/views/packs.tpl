%rebase layout_skonf globals(), js=['packs/js/packs.js']

<div class='span10'>
  <h1> Packs </h1>
  <a href='/getpacks' class='btn btn-success pull-right'> <i class="icon-search"></i>Get new packs</a>
</div>

<div class='span12'>
  %treename = ''
  %tree_path = []
  %for e in app.datamgr.get_pack_tree(app.packs):
  %print "ENTRY", e
  %if e['type'] == 'new_tree':
  %treename = e['name']
  %tree_path.append(treename)
  %is_well = 'well'
  %# For 2nd and more level, do not put well again.
  %if len(tree_path) > 1:
  %is_well = ''
  %end
  <div class='{{is_well}}'> {{!' <i class="icon-chevron-right"></i> '.join(['<b>%s</b>' % p.capitalize() for p in tree_path])}}
    %elif e['type'] == 'end_tree':
    %# We remove the last element
    %tree_path.reverse()
    %tree_path.pop()
    %tree_path.reverse()
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
      <div> Host tag: <a href='/elements/hosts/{{tname}}'> {{tname}}</a>
        <a class='pull-right' href="javascript:show_services_list('{{tname}}');"> <i class="icon-chevron-down"></i></a>
      </div>
      %else:
      <div class="alert">No host template for this pack!</div>
      %end
      %end
    </div>
    <div class='pull-right'>
      %lnk = p.doc_link
      %if not lnk:
      %lnk = "http://www.shinken-monitoring.org/wiki/packs/"+pname
      %end
      <a class='pull-right' href="{{lnk}}" target='_blank'> <i class="icon-question-sign"></i></a>
    </div>

    <div class='span10'>
      %for _t in lst:
      %if len(services) != 0:
      %(tpl, services) = _t
      <div id="services-{{tpl.get('name', '')}}" class='services_list'>
        %if len(services) == 0:
        <div class="alert">No services enabled for this pack</div>
        %else:
        <b> {{tpl.get('name', '')}} services: </b>
        %end

        %for s in services:
        %sid = s.get('_id', '')
        %sname = s.get('service_description', 'unknown')
        <div class=''><a href='/elements/services/{{sid}}'> {{sname}}</a></div>
        %end
      </div>
      %end
    </div>
  </div>
  %end
  %end
</div>

