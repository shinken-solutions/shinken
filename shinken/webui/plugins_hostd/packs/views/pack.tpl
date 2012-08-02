
%pname = pack.get('pack_name')
%rebase layout_hostd globals(), title='Pack %s' % pname

<!-- PACK {{pack}} -->


%pid = pack.get('_id')
%pstate = pack.get('state')
<span class='span10 well'>
  <span class='span5'>
    <img class="imgsize4" onerror="$(this).hide()" src="/static/{{pid}}/images/sets/{{pname}}/tag.png" /> <h2>Pack {{pname}}</h2>
  </span>
  <span class='span5'>
    <b>Publisher</b>: {{pack.get('user')}}
  </span>
  <span class='span5'>
    <b>Description</b>: {{pack.get('description')}}
  </span>
  <span class='span5'>
    <b>Documentation</b>:
    %doc = pack.get('doc_link')
    %if not doc:
       %doc = 'http://www.shinken-monitoring.org/wiki/packs/'+pname
    %end
    <a href='{{doc}}'> Link </a>
  </span>

  <span class='span5'>
    <a class='btn btn-success' href='/getpack/{{pid}}'> <i class="icon-download"></i> Download it!</a>
  </span>

</span>

<!-- PACK -->

%if pstate == 'obsolete':
    %by = pack.get('obsoleted_by')
    <span class='alert alert-warning span10'> Warning: this pack is obsoleted by a newer version. <a href='/pack/{{by}}'>Please look the new one here.</a></span>
%end

%if pstate == 'refused':
    %reason = pack.get('moderation_comment', '')
    <span class='alert alert-error span10'> Error: this pack have been refused by a moderator. Reason: {{reason}}</span>
%end

<span class='span10 well'>
  <h3> Host tags </h3>
  <ul>
  %for t in pack.get('templates', []):
     <li>
       	<span class="label">
	  <img class="imgsize3" onerror="$(this).hide()" src="/static/{{pid}}/images/sets/{{t}}/tag.png" /> {{t}}
	</span>
     </li>
     <h5> Services linked </h5>
     <ul>
     %for (s, e) in pack.get('services').iteritems():
        %tpls = e.get('templates')
        %if t in tpls:
          <li> {{s}}</li>
        %end
     %end
     </ul>
  %end
  </ul>
</span>
