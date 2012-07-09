
%rebase layout_skonf globals()

%if results:
  %state = results['state']
  %text = results['text']

  %if state == 200:
     <div class='alert alert-success span5 offset2'>
       {{text}}
     </div>
  %else:
     %api_error = text
  %end
%end

%if api_error:
    <div class='alert alert-error span5 offset2'>
      <div id='api_error' >{{api_error}}</div>
      <a href='/register' class='btn btn-success'> <i class="icon-user"></i> Register to the API server</a>
    </div>
%end
