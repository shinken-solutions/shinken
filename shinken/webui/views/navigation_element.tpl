%if not 'app' in locals() : app = None

<ul id="menu">

                %menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All'), ('/system', 'System') ]
                %for (key, value) in menu:

                            %# Check for the selected element, if there is one
                                %if menu_part == key:
                                        <li><a href="{{key}}" id="selected">{{value}}</a></li>
                                        %else:
                                                <li class="normal"><a href="{{key}}">{{value}}</a></li>
                                        %end
                                %end



    <li class="menu_right"><a href="#" class="drop">Impacts <span class="tac_impacts">1 / 2 /3</span></a><!-- Begin 3 columns Item -->

        <div class="dropdown_3columns align_right"><!-- Begin 3 columns container -->

            <div class="col_3">
                <h2>Lists in Boxes</h2>
            </div>

            <div class="col_1">

                <ul class="greybox">
                    <li><a href="#">FreelanceSwitch</a></li>
                    <li><a href="#">Creattica</a></li>
                    <li><a href="#">WorkAwesome</a></li>
                    <li><a href="#">Mac Apps</a></li>
                    <li><a href="#">Web Apps</a></li>
                </ul>   

            </div>

            <div class="col_1">

                <ul class="greybox">
                    <li><a href="#">ThemeForest</a></li>
                    <li><a href="#">GraphicRiver</a></li>
                    <li><a href="#">ActiveDen</a></li>
                    <li><a href="#">VideoHive</a></li>
                    <li><a href="#">3DOcean</a></li>
                </ul>   

            </div>

            <div class="col_1">

                <ul class="greybox">
                    <li><a href="#">Design</a></li>
                    <li><a href="#">Logo</a></li>
                    <li><a href="#">Flash</a></li>
                    <li><a href="#">Illustration</a></li>
                    <li><a href="#">More...</a></li>
                </ul>   

            </div>

            <div class="col_3">
                <h2>Here are some image examples</h2>
            </div>

            <div class="col_3">
                <img src="img/02.jpg" width="70" height="70" class="img_left imgshadow" alt="" />
                <p>Maecenas eget eros lorem, nec pellentesque lacus. Aenean dui orci, rhoncus sit amet tristique eu, tristique sed odio. Praesent ut interdum elit. Maecenas imperdiet, nibh vitae rutrum vulputate, lorem sem condimentum.<a href="#">Read more...</a></p>

                <img src="img/01.jpg" width="70" height="70" class="img_left imgshadow" alt="" />
                <p>Aliquam elementum felis quis felis consequat scelerisque. Fusce sed lectus at arcu mollis accumsan at nec nisi. Aliquam pretium mollis fringilla. Vestibulum tempor facilisis malesuada. <a href="#">Read more...</a></p>
            </div>

        </div><!-- End 3 columns container -->

    </li><!-- End 3 columns Item -->

</ul>
<div class="clear"></div>