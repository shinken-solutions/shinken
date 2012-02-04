%rebase layout globals(),js=['dashboard/js/mooMasonry.js'], css=['dashboard/css/dashboard.css', 'dashboard/css/csschart.css'], title='Architecture state', menu_part='/dashboard'

%from shinken.bin import VERSION
%helper = app.helper

	<div id="messagebox" class="gradient_alert" style="margin-top: 20px;">
		<img src="/static/images/icons/alert.png" alt="some_text" style="height: 40px; width: 40px" class="grid_4"/> 
		<p><strong>Mockup</strong></p>
	</div>

	<h3>Drag n Drop Panels</h3>
	
	<div class="column" id="column1">
		<div class="dragbox" id="item1" >
			<h2>Handle 1</h2>
			<div class="dragbox-content" >
				Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vestibulum velit ultricies orci pharetra elementum. In massa mauris, varius sed tempus a, iaculis sed erat. Ut sollicitudin tellus mollis arcu laoreet semper. Suspendisse ut felis odio. Aliquam auctor, tortor sit amet suscipit elementum, nunc ante dictum lectus, ac accumsan justo nunc sed velit. Sed sollicitudin varius tortor vitae varius. Aliquam interdum, nisl consectetur laoreet commodo, metus massa sagittis nisl, non venenatis lacus mi nec tortor. Ut malesuada auctor dolor, id pulvinar est malesuada sed. Aliquam sed posuere orci. 
			</div>
		</div>
		<div class="dragbox" id="item2" >
			<h2><span class="configure" ><a href="#" >Configure</a></span>Handle 2</h2>
			<div class="dragbox-content" >
				Phasellus porttitor adipiscing lacus ac tempus. Vivamus gravida augue metus, eu cursus nisl. Etiam arcu eros, placerat sed rhoncus at, porta et elit. Aenean pharetra ante neque. Aenean id egestas orci. Suspendisse potenti. Nunc at magna leo, sed porta erat. Proin eget neque turpis, vel blandit massa. Donec vel tortor magna. Curabitur id nibh magna, nec hendrerit nibh. 
			</div>
		</div>
		<div class="dragbox" id="item3" >
			<h2>Handle 3</h2>
			<div class="dragbox-content" >
				Proin porttitor euismod condimentum. Integer suscipit nibh nec augue facilisis ut commodo nisi ornare. Nam sed mauris vitae justo convallis placerat. Curabitur viverra, ipsum id volutpat sollicitudin, mi nisi condimentum nulla, nec dapibus velit libero eget orci. Nam purus lectus, imperdiet pharetra pulvinar ac, sodales sit amet sem. Ut vel mollis ante. Vivamus consectetur varius risus eu hendrerit. Sed scelerisque euismod leo, quis accumsan justo venenatis eu. Ut risus lorem, aliquet id fermentum nec, auctor ut enim. Ut pretium elementum turpis vel dignissim. 
			</div>
		</div>
	</div>
	<div class="column" id="column2" >
		<div class="dragbox" id="item4" >
			<h2>Handle 4</h2>
			<div class="dragbox-content" >
				Nullam metus magna, tristique vel ultrices a, molestie quis dolor. Curabitur porta porta ullamcorper. Duis varius velit et dui auctor pretium bibendum urna gravida. Sed euismod dui in tellus euismod euismod. Nam convallis ornare fermentum. Aliquam libero augue, ullamcorper vitae lacinia at, vestibulum et risus. Praesent accumsan ultrices purus eu consequat. Phasellus posuere lobortis malesuada. Curabitur ac orci eu dui vulputate porttitor. Sed a urna et odio vulputate euismod. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. In volutpat, tortor eu dapibus vestibulum, risus metus eleifend ipsum, quis lobortis elit dolor vel ligula. Aliquam ultrices nunc in elit bibendum pharetra. Ut non ante sagittis arcu imperdiet posuere. Duis consectetur massa sit amet enim scelerisque consequat et eget magna. Curabitur tristique molestie sem quis vulputate. Sed eleifend urna neque. Nam placerat eros non augue consequat vestibulum. 
			</div>
		</div>
		<div class="dragbox" id="item5" >
			<h2>Handle 5</h2>
			<div class="dragbox-content" >
				Nam rhoncus sodales libero, et facilisis nisi volutpat et. Nullam tellus eros, consequat eget tristique ultricies, rhoncus vitae magna. Duis nec scelerisque orci. Nullam a enim est, et eleifend nunc. Proin dui eros, vulputate eget consectetur quis, ultrices ac sem. Nulla aliquam metus eu magna placerat placerat. Suspendisse eget tellus turpis, et ultricies nisi. Etiam in diam mi, sed tincidunt eros. Phasellus convallis aliquam arcu, vitae fringilla quam pharetra sed. In at augue at nibh placerat feugiat at id elit. Curabitur sit amet quam ut turpis molestie blandit in vel nulla. 
			</div>
		</div>
	</div>