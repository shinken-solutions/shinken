
%rebase layout_hostd globals()




<script TYPE="text/javascript">

function submit(){
   document.forms['register'].submit();
}

function user_name_is_available(arg1, arg2, arg3){
   console.log('Arg1'+arg1+'Arg2'+arg2+'arg3'+arg3);
   if(arg1){
      $('#name_ok').show();
      $('#name_bad').hide();
   }else{
      $('#name_ok').hide();
      $('#name_bad').show();
   }
}

function check_username(username){
   if(username.length > 2){
      $.ajax({
        type: 'POST',
        url: '/availability',
        data: {'value' : username},
        success: user_name_is_available
      });
   }
}

$(document).ready(function(){
  $('#name_ok').hide();
  $('#name_bad').hide();
});

</script>

Please register <br/>

<form class='well span5 offset2' name='register' action='/register' METHOD='POST'>
    <input type="textarea" name='username' class="span3" placeholder="Username" onChange="check_username(this.value)">  
    <span class="help-inline">Username <i id='name_ok' class="icon-ok"></i> <i id='name_bad' class="icon-remove"></i> </span>

    <div class="input-prepend">
      <span class="add-on"><i class="icon-envelope"></i></span><input class="span2" nae="email" type="text">
      <span class="help-inline"> Email </span>
    </div>

    <a href='javascript:submit();' class='btn'> submit</a>
    
</form>
