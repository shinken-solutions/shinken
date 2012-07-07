%helper = app.helper
%datamgr = app.datamgr

%rebase layout title='Business impacts', print_menu=False, print_header=False, css=['threedimpacts/css/threedimpacts.css'], js=['threedimpacts/js/Three.js', 'threedimpacts/js/Detector.js', 'threedimpacts/js/RequestAnimationFrame.js', 'threedimpacts/js/Stats.js', 'threedimpacts/js/Tween.js', 'threedimpacts/js/optimer_bold.typeface.js', 'threedimpacts/js/3dmanager.js']

%# " If the auth got problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here."
%end



		<div id="container"></div>

		%# " all_impacts is what the 3dmanager.js will take it's impacts "
		%imp_id = 0
		%for imp in impacts:

		   Impact {{imp_id}} {{imp.get_full_name()}}<br>
		  %# "Now we add this impact in our all_impacts array to give"
		  %# "3d manager true objects"
		   <script type="text/javascript">
		     var current_impact = {'name': '{{imp.get_full_name()}}',
		     'state': '{{imp.state.lower()}}',
		     'business_impact': {{imp.business_impact}}
		     };
		     all_impacts.push(current_impact);
                   </script>
		   <div id='objinfo-{{imp_id}}' class='objinfo'><div class='inner-objinfo'>
		       %for i in range(2, imp.business_impact):
		         <img src="static/images/star.png">
		       %end
			 <h2 class="state_{{imp.state.lower()}}"><img style="width: 64px; height:64px" src="{{helper.get_icon_state(imp)}}" />{{imp.state}}: {{imp.get_full_name()}}</h2>
		       <p>since {{helper.print_duration(imp.last_state_change, just_duration=True, x_elts=2)}}</p>
		       <div style="float:right;"> <a href="{{!helper.get_link_dest(imp)}}">{{!helper.get_button('Go to details', img='/static/images/search.png')}}</a></div>
		   </div></div>
		   %imp_id += 1
		%end

		<div id="info">You can click on an object to get more information.</div>



		<script id="fragmentShader" type="x-shader/x-fragment">

			uniform float time;
			uniform vec2 resolution;

			uniform float fogDensity;
			uniform vec3 fogColor;

			uniform sampler2D texture1;
			uniform sampler2D texture2;

			varying vec2 vUv;

			void main( void ) {

				vec2 position = -1.0 + 2.0 * vUv;

				vec4 noise = texture2D( texture1, vUv );
				vec2 T1 = vUv + vec2( 1.5, -1.5 ) * time  *0.02;
				vec2 T2 = vUv + vec2( -0.5, 2.0 ) * time * 0.01;

				T1.x += noise.x * 2.0;
				T1.y += noise.y * 2.0;
				T2.x -= noise.y * 0.2;
				T2.y += noise.z * 0.2;

				float p = texture2D( texture1, T1 * 2.0 ).a;

				vec4 color = texture2D( texture2, T2 * 2.0 );
				vec4 temp = color * ( vec4( p, p, p, p ) * 2.0 ) + ( color * color - 0.1 );

				if( temp.r > 1.0 ){ temp.bg += clamp( temp.r - 2.0, 0.0, 100.0 ); }
				if( temp.g > 1.0 ){ temp.rb += temp.g - 1.0; }
				if( temp.b > 1.0 ){ temp.rg += temp.b - 1.0; }

				gl_FragColor = temp;

				float depth = gl_FragCoord.z / gl_FragCoord.w;
				const float LOG2 = 1.442695;
				float fogFactor = exp2( - fogDensity * fogDensity * depth * depth * LOG2 );
				fogFactor = 1.0 - clamp( fogFactor, 0.0, 1.0 );

				gl_FragColor = mix( gl_FragColor, vec4( fogColor, gl_FragColor.w ), fogFactor );

			}
		</script>

		<script id="vertexShader" type="x-shader/x-vertex">

			uniform vec2 uvScale;
			varying vec2 vUv;

			void main()
			{

				vUv = uvScale * uv;
				vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );
				gl_Position = projectionMatrix * mvPosition;

			}

		</script>

