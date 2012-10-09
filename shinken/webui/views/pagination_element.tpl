%if navi is not None:
%from urllib import urlencode
<div class="pagination {{div_class}}">
    <ul class="pull-right">
        %for name, start, end, is_current in navi:
            %if is_current:
                %#<li><a href="#">Prev</a></li>
                <li class="active"><a href="#">{{name}}</a></li>
            %elif start == None or end == None:
                <li class="disabled"> <a href="#">...</a> </li>
            %else:
                %# Include other query parameters like search and global_search
                %query = app.request.query
                %query['start'] = start
                %query['end'] = end
                %query_string = urlencode(query)
                <li><a href='/{{page}}?{{query_string}}' class='page larger'>{{name}}</a></li>
            %end
        %end
    </ul>
</div>
%# end of the navi part
%end
