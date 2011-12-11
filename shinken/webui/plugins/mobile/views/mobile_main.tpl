
%rebase layout globals()
<div> <h1> Shinken </h1> </div>

<h2>End users apps</h2>

%bad_business = [i for i in impacts if i.state_id != 0]


%""" All business apps are OK """
%if len(bad_business) == 0:
    <img src="/static/images/state_ok.png" >
    <img src="/static/images/next.png"/>
 """ Are, some business apps are bad!"""
%else:
    <img src="/static/images/state_critical.png" >
    <img src="/static/images/next.png"/>
    <ul>
    %for imp in bad_business:
         <li class="{{imp.state.lower()}}">{{imp.get_full_name()}} is {{imp.state}}</li>
    %end
    </ul>    
%end


<h2>Pure IT problems</h2>