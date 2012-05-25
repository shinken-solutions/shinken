%import hashlib

%rebase layout_hostd globals(), js=['user/js/user.js']

%uname = user.get('username')
Your account {{uname}}

<span id='message' class='alert span10'></span>

<form class='span10 well' name='user' action='/user'>
  <div class='span2 pull-right'>
    %emailhash = hashlib.md5(user.get('email').strip().lower()).hexdigest()
    <img src='http://www.gravatar.com/avatar/{{emailhash}}' class=''/>
  </div>
  <div class="control-group">
    <label class="control-label" for="username">Username</label>
    <div class="controls">
      <input class="input-large disabled" id="username" type="text" placeholder="{{uname}}" disabled="">
    </div>
  </div>
  <div class="control-group">
    <label>Password</label>
    <input type="password" name="password" class="span3" placeholder="Set new password.">
    <span class="help-block">Fill to change your current password.</span>
    <input type="password" name="password2"class="span3" placeholder="Verify" onChange="check_pass_match();">
    <span id='pass_ok'><i class="icon-ok"></i> OK </span>
    <span id='pass_bad'><i class="icon-remove"></i> Password mismatch! </span>
  </div>
  
  <div class="control-group">
    <label>Email</label>
    <input type="text" name="email" class="span3" placeholder="Set new password." value="{{user.get('email')}}">
  </div>
  <a href='javascript:submit_user_form();' class='btn'> Submit</a>
</form>



<div class='well span8'>
  <h4> API KEY : </h4> <h3>{{user.get('api_key')}}</h3>
</div>


<div class='well span8'>
  %if len(pending_packs) == 0:
  No pending packs
  %else:
    %for p in pending_packs:
     <span class='span8 alert alert-info'> {{p.get('filename')}} was uploaded and is still in analysing phase.</span>
    %end
  %end
</div>

<div class='well span8'>
  %if len(validated_packs) == 0:
  No validated packs
  %else:
    %for p in validated_packs:
      <span class='span8 alert alert-success'> {{p.get('filename')}} is validated.</span>
    %end
  %end
</div>

<div class='well span8'>
  %if len(refused_packs) == 0:
  No refused packs
  %else:
    %for p in refused_packs:
      <span class='span8 alert alert-error'> {{p.get('filename')}} is refused. Reason : {{p.get('moderation_comment', 'none')}}.</span>
    %end
  %end
</div>

