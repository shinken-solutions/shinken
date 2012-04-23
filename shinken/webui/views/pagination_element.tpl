%if navi is not None:
<div class="pagination span12">
	<ul class="pull-right">
	%for name, start, end, is_current in navi:
	   	%if is_current:
	   	<li><a href="#">Prev</a></li>
	   	<li class="active"><a href="#">{{name}}</a></li>
	   	%elif start == None or end == None:
	   	<li class="disabled"> <a href="#">...</a> </li>
	   	%else:
		<li><a href='/{{page}}?start={{start}}&end={{end}}' class='page larger'>{{name}}</a></li>
	   	%end
	    %end
	</ul>
</div>
%# end of the navi part
%end