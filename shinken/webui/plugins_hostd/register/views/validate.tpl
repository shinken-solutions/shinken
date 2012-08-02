
%rebase layout_hostd globals()




%if not activating_key:
    <div class='alert alert-error span5 offset2'> Please fill your activing key</div>
%end

%if activating_key and not activated:
    <div class='alert alert-error span5 offset2'> Sorry, your account is not validated. Please fill a valid activating_key </div>

%else:
    <div class='span10 offset2'>
      Congrats! Your account is validated. You can now <a class='btn btn-success' href='/login'> login</a>
    </div>
%end

