
%rebase layout globals(), title="Tactical view", js=['mobile/js/mobile_main.js'], css=['mobile/css/main.css', 'mobile/css/impacts.css']

<div id="all">
<div> <h1> Shinken business apps</h1> </div>

<h2>End users apps</h2>



<img src="/static/images/state_critical.png" >
<a href="#" onclick="slide_and_go('/mobile/impacts');"><img src="/static/images/next.png"/></a>
%i = 0
<div class="impacts">
  %for imp in impacts:
    <div class="impact" style="left:{{i*250}}px">
      <p class="{{imp.state.lower()}}">{{imp.get_full_name()}} is {{imp.state}}</p>
    </div>
    %i += 1
  %end
</div>



</div>
