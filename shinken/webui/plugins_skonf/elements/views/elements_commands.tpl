%rebase layout_skonf globals(), css=['elements/css/hosts.css'], js=['elements/js/hosts.js'], title='All commands'

<div class="row-fluid">
  <h3 class="span10 no-topmargin">All your commands</h3>
  <a class="span2 btn btn-small btn-spezial btn-success" href="/elements/add/command"><i class="icon-plus"></i> Add new command</a>
</div>

<div class="row-fluid">
  <div class="span12">
    <table class="table table-condensed table-hover">
      <thead>
        <tr>
          <th> </th>
          <th>Poller Tag</th>
          <th>Reactionner Tag</th>
          <th>Module Type</th>
          <th>Status</th>
        </tr>
      </thead>
      %for h in elts:
      %hname = h.get_name()
      <tbody>
        <tr>
          <td><a href='/elements/timeperiods/{{hname}}'>{{hname}}</a> </td>
          <td>{{getattr(h, 'poller_tag', '')}}&nbsp;</td>
          <td>{{getattr(h, 'reactionner_tag', '')}}&nbsp;</td>
          <td>{{getattr(h, 'module_type', '')}}&nbsp;</td>
          <td class="span2">
              %state = h.customs.get('_STATE', 'enabled')
              %editable = ''
              %print "EDIABLE?", getattr(h,'editable', '1')
              %if getattr(h,'editable', '1') == '0':
              %editable = 'disabled'
              %end
              %if state == 'enabled':
                 %ena_state = ''
                 %disa_state = 'hide'
              %else:
                 %ena_state = 'hide'
                 %disa_state = ''
              %end
              <a id='btn-enabled-{{hname}}' class='{{ena_state}} {{editable}} btn btn-mini btn-success' href="javascript:disable_element('timeperiods', '{{h.get_name()}}')">Enabled</a>
              <a id='btn-disabled-{{hname}}' class='{{disa_state}} {{editable}} btn btn-mini btn-warning' href="javascript:enable_element('timeperiods', '{{h.get_name()}}')">Disabled</a>
          </td>
        </tr>
      </tbody>
      %end
    </table>
  </div>
</div>