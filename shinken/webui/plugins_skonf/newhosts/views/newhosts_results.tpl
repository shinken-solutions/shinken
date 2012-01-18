
%rebase layout_skonf globals()
<div> <h1> Discover your new hosts </h1> </div>

<p>Here are the scans :</p>
%for s in scans:
     <br/>{{s}}
%end

<p>Here are the results :</p>

%for h in pending_hosts:
     <br/>{{h}}
%end