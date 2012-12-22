%rebase layout_skonf globals(), js=['packs/js/packs.js', 'packs/js/viewswitcher.js'], css=['packs/css/packs.css'], title='Packs'

<div class="row-fluid">
  <h3 class="span9 no-topmargin">Packs</h3>
  <a href="/getpacks" class="span2 btn btn-small btn-spezial btn-success"> <i class="icon-search"></i> Get new packs</a>
  <span class="span1 btn-group">
    <a href="#" id="gridview" class="btn btn-small switcher"><i class="icon-th"></i></a>
    <a href="#" id="listview" class="btn btn-small switcher active"> <i class="icon-list"></i></a>
  </span>
</div>

<div class="row-fluid">
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

<!--   <div class='{{is_well}}'> {{!' <i class="icon-chevron-right"></i> '.join(['<b>%s</b>' % p.capitalize() for p in tree_path])}} -->
  <div class=''> {{!' <i class="icon-chevron-right"></i> '.join(['<h4>%s</h4>' % p.capitalize() for p in tree_path])}}
    %elif e['type'] == 'end_tree':
    %# We remove the last element
    %tree_path.reverse()
    %tree_path.pop()
    %tree_path.reverse()
  </div>
  %else:
  
  %p = e['pack']
  <ul id="products" class="{{treename}} list clearfix">
    <li class="clearfix">
      <!-- {{p}} -->
      %pname = p.get_name()
      <section class="left span10">
        <h3><img class="imgsize3" onerror="$(this).hide()" src="/static/images/sets/{{pname}}/tag.png" /> {{pname}}</h3>
        <p><b>Description:</b>
        {{p.description}}
        </p>
        <span class="meta">
          %lst = app.datamgr.related_to_pack(p)
          %print "LST", lst
          %for _t in lst:
          %(tpl, services) = _t
          %if tpl:
          %tname = tpl.get('name', '')
          <div style="position: relative;"> Host tag: <a href='/elements/hosts/{{tname}}'> {{tname}}</a>

          </div>
          %else:
          <div class="alert alert-info">No host template for this pack!</div>
          %end
          %end
        </span>
        %for _t in lst:
        %if len(services) != 0:
        %(tpl, services) = _t
        <div id="services-{{tpl.get('name', '')}}" class='services_list'>
          %if len(services) == 0:
          <p class="alert">No services enabled for this pack</p>
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
        %end
      </section>

      <section class="right span2">
        <span class="darkview">
        %lnk = p.doc_link
        %if not lnk:
          %lnk = "http://www.shinken-monitoring.org/wiki/packs/"+pname
        %end
        <a class="firstbtn" href="{{lnk}}" target='_blank'> <i class="icon-question-sign"></i></a>

        <a class='pull-right' href="javascript:show_services_list('{{tname}}');"> <i class="icon-chevron-down pull-right"></i></a>
        </span>
      </section>
    </li>
  </ul>
  %end
  %end
</div>

