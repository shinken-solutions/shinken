
%rebase layout_mobile globals(), title="Tactical view", js=['mobile/js/mobile_main.js'], css=['mobile/css/main.css']

<div id="all">
<div> <h1> Shinken </h1> </div>

<h2>End users apps</h2>

%bad_business = [i for i in impacts if i.state_id != 0]


%# """ All business apps are OK """
%if len(bad_business) == 0:

    <a href="#" onclick="slide_and_go('/mobile/impacts');">
      <img src="/static/images/state_ok.png">
      <img src="/static/images/next.png"/>
    </a>
%# """ Are, some business apps are bad!"""
%else:

    <a href="#" onclick="slide_and_go('/mobile/impacts');">
      <img src="/static/images/state_critical.png" >
      <img src="/static/images/next.png"/>
    </a>
    <ul>
    %for imp in bad_business:
         <li class="{{imp.state.lower()}}">{{imp.get_full_name()}} is {{imp.state}}</li>
    %end
    </ul>    
%end


<h2>Pure IT problems</h2>
%if len(problems) == 0:
    <a href="#" onclick="slide_and_go('/mobile/problems');">
      <img src="/static/images/state_ok.png" >
      <img src="/static/images/next.png"/>
    </a>
%else:
    <a href="#" onclick="slide_and_go('/mobile/problems');">
      <img src="/static/images/state_warning.png" >
      <img src="/static/images/next.png"/>
    </a>
    %nb_high_critical = len([pb for pb in problems if pb.business_impact > 2 and pb.state in ['DOWN', 'CRITICAL'] ])
    %nb_high_warn = len([pb for pb in problems if pb.business_impact > 2 and pb.state in ['WARNING']])
    %nb_low_critical = len([pb for pb in problems if pb.business_impact <= 2 and pb.state in ['DOWN', 'CRITICAL'] ])
    %nb_low_warn = len([pb for pb in problems if pb.business_impact <= 2 and pb.state in ['WARNING']])
    <br/>
    <p>Production : {{nb_high_critical}} Criticals, {{nb_high_warn}} Warnings.</p>
    <p>Lower      : {{nb_low_critical}} Criticals, {{nb_low_warn}} Warnings.</p>
%end

</div>
