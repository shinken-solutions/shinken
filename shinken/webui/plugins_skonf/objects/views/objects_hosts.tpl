
%rebase layout_skonf globals(), css=['objects/css/hosts.css'], js=['objects/js/hosts.js']


<div class='span2 pull-right'>
  <a class='btn btn-info' href="/objects/add/host"><i class="icon-plus"></i> Add new host</a>
</div>

<div class='offset1 span10'>
  <h3>All your hosts</h3>
  %for h in hosts:
  <div class='object_host span12'>

    <div class='hostname cut-long pull-left'>{{h.get_name()}}</div>
    <div class='display pull-left'>{{getattr(h, 'display_name', h.get_name())}}</div>
    <div class='address pull-left'>{{getattr(h, 'address', h.get_name())}}</div>
    <div class='realm pull-left'>{{getattr(h, 'realm', '')}}&nbsp;</div>
    <div class='poller pull-left'>{{getattr(h, 'poller_tag', '')}}&nbsp;</div>
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
    <!--{{h}} {{h.customs}}-->
  </div>
  %end
</div>

