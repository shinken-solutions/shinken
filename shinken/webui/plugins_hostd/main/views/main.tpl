%import hashlib

%rebase layout_hostd globals(), css=['main/css/main.css'], title='Shinken community website'

<div class='row'>
  <div class='offset1 span5 front_panel'>
    <a href="/packs" class="btn btn-large btn-success"><i class="icon-cog"></i> View packs</a>
  </div>
  <div class='offset1 span5 front_panel'>
    <a href="/addpack" class="btn btn-large btn-success"><i class="icon-th"></i> Add a new pack</a>
  </div>
  <div class='offset1 span5 front_panel'>
    <h4>Last packs</h4>
    <ul>
      %for p in last_packs:
      <li>
	%authoremail = app.get_email_by_name(p.get('user')).strip().lower()
	%emailhash = hashlib.md5(authoremail).hexdigest()
	<a href="/user/{{p.get('user')}}"> <img src='http://www.gravatar.com/avatar/{{emailhash}}' class='imgsize3'/></a>
	%pname = p.get('pack_name', 'unknown')
	%pid = p.get('_id', '')

	<a href='/pack/{{pid}}'>
	  <span class="label">
	    <img class="imgsize3" onerror="$(this).hide()" src="/static/{{pid}}/images/sets/{{pname}}/tag.png" /> {{pname}}
	  </span>
	</a>
      </li>
      %end
    </ul>
  </div>

</div>
