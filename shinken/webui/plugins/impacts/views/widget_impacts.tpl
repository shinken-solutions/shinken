%helper = app.helper
%datamgr = app.datamgr


%rebase widget globals()

%# %rebase layout globals(), js=['impacts/js/impacts.js', 'impacts/js/multi.js'], title='All critical impacts for your business', css=['impacts/css/impacts.css'], refresh=True, menu_part = '/impacts', user=user


%impacts = impacts.values()
%in_pb = [i for i in impacts if i.state_id in [1, 2, 3]]

%if len(impacts) == 0:
  <span> You don't have any business apps. Maybe you should define some?</span>
%end

%if len(impacts) !=0 and len(in_pb) == 0:
  <span>No business impacts! Congrats.</span>
%end

%for impact in impacts:

  <div class="tableCriticity pull-left row-fluid">
    <div class='img_status pull-left' style='width: 64px;'>
      <div class="big-pulse aroundpulse">
	%# " We put a 'pulse' around the elements if it's an important one "
	%if impact.business_impact > 2 and impact.state_id in [1, 2, 3]:
	<span class="big-pulse pulse"></span>
	%end
	<img style="width: 64px;height: 64px;" src="{{helper.get_icon_state(impact)}}" />
      </div>
    </div>


    <span class="alert-small alert-{{impact.state.lower()}}">{{impact.state}}</span> for {{!helper.get_link(impact)}}
    <div class='pull-right'>
      %for j in range(0, impact.business_impact-2):
      <img src='/static/images/star.png' alt="star">
      %end
    </div>

  </div>
  <div style="clear:both;"/>
%end
