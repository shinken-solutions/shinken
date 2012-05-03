
%rebase layout_skonf globals(), css=['elements/css/hosts.css'], js=['elements/js/hosts.js']


<div class='span2 pull-right'>
  <a class='btn btn-info' href="/elements/add/host"><i class="icon-plus"></i> Add new host</a>
</div>

<div class='offset1 span10'>
  <h3>All your hosts</h3>
  %for h in elts:
  <div class='object_{{elt_type}} span12'>
    <div class='host_name cut-long pull-left'><a href='/elements/hosts/{{h.get_name()}}'>{{h.get_name()}}</a></div>
    <div class='display_name cut-long pull-left'>{{getattr(h, 'display_name', '')}}&nbsp;</div>
    <div class='address cut-long pull-left'>{{getattr(h, 'address', '')}}&nbsp;</div>
    <div class='realm cut-long pull-left'>{{getattr(h, 'realm', '')}}&nbsp;</div>
    <div class='poller_tag cut-long pull-left'>{{getattr(h, 'poller_tag', '')}}&nbsp;</div>
    
    <div class='use pull-left'>
      %for u in getattr(h, 'use', '').split(','):
      <span class='label'><img class='imgsize1' onerror="$(this).hide()" src="/static/images/sets/{{u}}/tag.png" />{{u}}</span>
      %end
      &nbsp;</div>
    <div class='status pull-left'>
      %state = h.customs.get('_STATE', 'enabled')
      %if state == 'enabled':
         %ena_state = ''
         %disa_state = 'hide'
      %else:
         %ena_state = 'hide'
         %disa_state = ''
      %end
        <a id='btn-enabled-{{h.get_name()}}' class='{{ena_state}} btn btn-small btn-success' href="javascript:disable_host('{{h.get_name()}}')">Enabled</a>
	<a id='btn-disabled-{{h.get_name()}}' class='{{disa_state}} btn btn-small btn-warning' href="javascript:enable_host('{{h.get_name()}}')">Disabled</a>
    </div>
    <br/>
    <!--{{h}} -->
  </div>
  %end
</div>

