
var all_impacts = new Array();

/* The main 3d code that will be call when we got objets :) */
window.addEvent('domready', function(){
	if ( ! Detector.webgl ) Detector.addGetWebGLMessage();

	var container, stats;

	var start_time;

	var camera, scene, renderer, projector;

	var uniforms, material, mesh;

	var theta = 0;

	var windowHalfX = window.innerWidth / 2;
	var windowHalfY = window.innerHeight / 2;

	var postprocessing = { enabled : true };
	var all_items = new Array();

	var radius = 2;
	var theta = 45;
	var theta_offset = 0.01;

	var active_object = null;

	var PI2 = Math.PI * 2;

	/* Let create and init all things*/
	init();
	/* And start the animation loop*/
	animate();


	function init() {

	    container = document.getElementById( 'container' );

	    camera = new THREE.Camera( 0, windowHalfX / windowHalfY, 1, 60000 );
	    camera.position.z = 3;

	    scene = new THREE.Scene();
	    projector = new THREE.Projector();

	    start_time = new Date().getTime();

	    uniforms = {

		fogDensity: { type: "f", value: 0.45 },
		fogColor: { type: "v3", value: new THREE.Vector3( 0, 0, 0 ) },
		time: { type: "f", value: 1.0 },
		resolution: { type: "v2", value: new THREE.Vector2() },
		uvScale: { type: "v2", value: new THREE.Vector2( 3.0, 1.0 ) },
		texture1: { type: "t", value: 0, texture: THREE.ImageUtils.loadTexture( "/static/threedimpacts/cloud.png" ) },
		texture2: { type: "t", value: 1, texture: THREE.ImageUtils.loadTexture( "/static/threedimpacts/greentile.jpg" ) }

	    };
	    uniforms.texture1.texture.wrapS = uniforms.texture1.texture.wrapT = THREE.Repeat;
	    uniforms.texture2.texture.wrapS = uniforms.texture2.texture.wrapT = THREE.Repeat;
	    material = new THREE.MeshShaderMaterial( {

		    uniforms: uniforms,
		    vertexShader: document.getElementById( 'vertexShader' ).textContent,
		    fragmentShader: document.getElementById( 'fragmentShader' ).textContent

		} );

	    uniforms_crit = {

		fogDensity: { type: "f", value: 0.45 },
		fogColor: { type: "v3", value: new THREE.Vector3( 0, 0, 0 ) },
		time: { type: "f", value: 1.0 },
		resolution: { type: "v2", value: new THREE.Vector2() },
		uvScale: { type: "v2", value: new THREE.Vector2( 3.0, 1.0 ) },
		texture1: { type: "t", value: 0, texture: THREE.ImageUtils.loadTexture( "/static/threedimpacts/cloud.png" ) },
		texture2: { type: "t", value: 1, texture: THREE.ImageUtils.loadTexture( "/static/threedimpacts/lavatile.jpg" ) }

	    };
	    uniforms_crit.texture1.texture.wrapS = uniforms_crit.texture1.texture.wrapT = THREE.Repeat;
	    uniforms_crit.texture2.texture.wrapS = uniforms_crit.texture2.texture.wrapT = THREE.Repeat;
	    material_crit = new THREE.MeshShaderMaterial( {

		    uniforms: uniforms_crit,
		    vertexShader: document.getElementById( 'vertexShader' ).textContent,
		    fragmentShader: document.getElementById( 'fragmentShader' ).textContent

		} );
	    var NB = all_impacts.length;/*5;*/
	    for ( var i = 0; i < NB; i ++ ) {
		impact = all_impacts[i];
		//alert('impact' + impact.name);
		/* The impact state can change the colormaterial*/
		if(impact.state == 'critical' || impact.state == 'down'){
		    mat = material_crit;
		}else{
		    mat = material;
		}

		mesh = new THREE.Mesh( new THREE.SphereGeometry( 0.2, 30, 30 ), [ mat ] );

		// We setup some flags
		mesh.fixed = false; //Is in a fixed forefront position?

		mesh.id = i;
		/* There are shepre and text :)*/
		mesh.is_sphere = true;

		all_items.push(mesh);
		scene.addObject( mesh );

		// Part TEXT
		var textGeo = new THREE.TextGeometry( impact.name, {
			size: 10, height: 10,	curveSegments: 20,
			font: "optimer", weight: "bold", style: "normal",
			bezelThickness: 5, bezelSize: 0.5,bezelEnabled: false
		    });
		var textMaterial = new THREE.MeshBasicMaterial( { color: Math.random() * 0xffffff, opacity: 1 } );
		var textMesh = new THREE.Mesh( textGeo, [ textMaterial ] );

		textMesh.scale.x = 0.005;
		textMesh.scale.y = 0.005;
		textMesh.scale.z = 0.0001;

		// Now put it below the mesh
		mesh.y_offset = 0.3;

		textMesh.position.x = mesh.position.x;
		textMesh.position.y = mesh.position.y - mesh.y_offset;
		textMesh.position.z = mesh.position.z;

		mesh.text = textMesh;

		// We put good position values
		update_mesh(mesh);

		scene.addObject( textMesh);

		// Make sure the info panel is hide!
		objinfo = document.getElementById('objinfo-'+i);
		new Fx.Tween(objinfo, {property: 'opacity'}).start(0);




	    }

	    renderer = new THREE.WebGLRenderer( { antialias: true } );
	    container.appendChild( renderer.domElement );

	    initPostprocessing();
	    renderer.autoClear = false;

	    stats = new Stats();
	    stats.domElement.style.position = 'absolute';
	    stats.domElement.style.top = '0px';
	    container.appendChild( stats.domElement );

	    onWindowResize();

	    window.addEventListener( 'resize', onWindowResize, false );
	    document.addEventListener( 'mousedown', onDocumentMouseDown, false );

	}




	function onWindowResize( event ) {

	    uniforms.resolution.value.x = window.innerWidth;
	    uniforms.resolution.value.y = window.innerHeight;

	    renderer.setSize( window.innerWidth, window.innerHeight );

	    camera.aspect = window.innerWidth / window.innerHeight;
	    camera.updateProjectionMatrix();

	}

	function onDocumentMouseDown( event ) {

	    event.preventDefault();

	    var vector = new THREE.Vector3( ( event.clientX / window.innerWidth ) * 2 - 1, - ( event.clientY / window.innerHeight ) * 2 + 1, 0.5 );
	    projector.unprojectVector( vector, camera );

	    var ray = new THREE.Ray( camera.position, vector.subSelf( camera.position ).normalize() );

	    var intersects = ray.intersectScene( scene );
	    //alert("clique sur"+intersects.length);
	    if ( intersects.length > 0 ) {
		//alert("move from"+intersects[ 0 ].object.position.x+"to"+Math.random());
		var object = intersects[ 0 ].object;

		// We only act if it's a sphere
		if(!object.is_sphere){
		    return;
		}

		if(active_object != null && active_object != object){
		    toggle_object(active_object);
		}
		// Ok, change the state of this object
        	toggle_object(object);
        	// Only set active if it's really active


	    }

	}


	function toggle_object(object){
	    // If we are fixed, we were in front. So came back to our saved position
	    // and in the "normal" size
	    if(object.fixed){
		off = object.id + 1;
		new TWEEN.Tween( object.position ).to( {
			x : Math.cos((theta+30*theta_offset)+off)*0.95,
			    y : Math.sin((theta+30*theta_offset)/2+off)/5,
			    z : Math.sin(theta+off+30*theta_offset)/2
			    /*x: object.save_position_x,
			      y: object.save_position_y,
			      z: object.save_position_z*/}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();

		new TWEEN.Tween( object.scale).to( {
			x : object.scale.x / 3,
			    y : object.scale.y / 3,
			    z : object.scale.z / 3,}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();

		// Get back the text near us
		new TWEEN.Tween( object ).to( {y_offset : object.y_offset / 3}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();
		//And smaller
		new TWEEN.Tween( object.text.scale).to( {
			x : object.text.scale.x / 3,
			    y : object.text.scale.y / 3,
			    z : object.text.scale.z / 3,}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();

		// There is no more active object
		active_object = null;


		// Make the objinfo panel disapear
		objinfo = document.getElementById('objinfo-'+object.id);
		new Fx.Tween(objinfo, {property: 'opacity'}).start(0);

	    }else{ // Not already in front. go in front
		// Save the original position
		object.save_position_x = object.position.x;
		object.save_position_y = object.position.y;
		object.save_position_z = object.position.z;
		new TWEEN.Tween( object.position ).to( {
			x: -1.65,
			    y: 0,
			    z: 0.25}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();
		// And go bigger
		new TWEEN.Tween( object.scale).to( {
			x : object.scale.x * 3,
			    y : object.scale.y * 3,
			    z : object.scale.z * 3,}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();

		// Put the text far away from us
		new TWEEN.Tween( object ).to( {y_offset : object.y_offset * 3}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();
		// And bigger
		new TWEEN.Tween( object.text.scale).to( {
			x : object.text.scale.x * 3,
			    y : object.text.scale.y * 3,
			    z : object.text.scale.z * 3,}, 1000 ).easing( TWEEN.Easing.Cubic.EaseInOut).start();

		// It's now the new active object
		active_object = object;

		objinfo = document.getElementById('objinfo-'+object.id);
		//objinfo.style.display = 'block';
		new Fx.Tween(objinfo, {property: 'opacity'}).start(1);

	    }

	    // Inverse the Object state
	    object.fixed = !object.fixed;
	}


	function initPostprocessing() {

	    postprocessing.scene = new THREE.Scene();

	    postprocessing.camera = new THREE.Camera();
	    postprocessing.camera.projectionMatrix = THREE.Matrix4.makeOrtho( window.innerWidth / - 2, window.innerWidth / 2,  window.innerHeight / 2, window.innerHeight / - 2, -10000, 10000 );
	    postprocessing.camera.position.z = 100;

	    var pars = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBFormat };
	    postprocessing.rtTexture1 = new THREE.WebGLRenderTarget( window.innerWidth, window.innerHeight, pars );
	    postprocessing.rtTexture2 = new THREE.WebGLRenderTarget( 512, 512, pars );
	    postprocessing.rtTexture3 = new THREE.WebGLRenderTarget( 512, 512, pars );

	    var screen_shader = THREE.ShaderUtils.lib["screen"];
	    var screen_uniforms = THREE.UniformsUtils.clone( screen_shader.uniforms );

	    screen_uniforms["tDiffuse"].texture = postprocessing.rtTexture1;
	    screen_uniforms["opacity"].value = 1.0;

	    postprocessing.materialScreen = new THREE.MeshShaderMaterial( {

		    uniforms: screen_uniforms,
		    vertexShader: screen_shader.vertexShader,
		    fragmentShader: screen_shader.fragmentShader,
		    blending: THREE.AdditiveBlending,
		    transparent: true

		} );

	    var convolution_shader = THREE.ShaderUtils.lib["convolution"];
	    var convolution_uniforms = THREE.UniformsUtils.clone( convolution_shader.uniforms );

	    postprocessing.blurx = new THREE.Vector2( 0.001953125, 0.0 ),
		postprocessing.blury = new THREE.Vector2( 0.0, 0.001953125 );

	    convolution_uniforms["tDiffuse"].texture = postprocessing.rtTexture1;
	    convolution_uniforms["uImageIncrement"].value = postprocessing.blurx;
	    convolution_uniforms["cKernel"].value = THREE.ShaderUtils.buildKernel( 4.0 );

	    postprocessing.materialConvolution = new THREE.MeshShaderMaterial( {

		    uniforms: convolution_uniforms,
		    vertexShader:   "#define KERNEL_SIZE 25.0\n" + convolution_shader.vertexShader,
		    fragmentShader: "#define KERNEL_SIZE 25\n"   + convolution_shader.fragmentShader

		} );

	    var film_shader = THREE.ShaderUtils.lib["film"];
	    var film_uniforms = THREE.UniformsUtils.clone( film_shader.uniforms );

	    film_uniforms["tDiffuse"].texture = postprocessing.rtTexture1;

	    postprocessing.materialFilm = new THREE.MeshShaderMaterial( { uniforms: film_uniforms, vertexShader: film_shader.vertexShader, fragmentShader: film_shader.fragmentShader } );
	    postprocessing.materialFilm.uniforms.grayscale.value = 0;
	    postprocessing.materialFilm.uniforms.nIntensity.value = 0.35;
	    postprocessing.materialFilm.uniforms.sIntensity.value = 0.95;
	    postprocessing.materialFilm.uniforms.sCount.value = 2048;

	    postprocessing.quad = new THREE.Mesh( new THREE.PlaneGeometry( window.innerWidth, window.innerHeight ), postprocessing.materialConvolution );
	    postprocessing.quad.position.z = - 500;
	    postprocessing.scene.addObject( postprocessing.quad );

	}

	//

	function animate() {

	    requestAnimationFrame( animate );

	    /* move objects */
	    for ( var i = 0; i < all_items.length; i ++ ) {
		mesh = all_items[i];
		update_mesh(mesh);

		// And for all, upadte their text mesh
		txt = mesh.text;
		txt.position.x = mesh.position.x;
		txt.position.y = mesh.position.y - mesh.y_offset;
		txt.position.z = mesh.position.z;

	    }

	    render();
	    stats.update();

	}


	function update_mesh(mesh){
	    var off = mesh.id + 1;
	    if(!mesh.fixed){
		mesh.position.x = Math.cos(theta+off)*0.95;
		mesh.position.y = Math.sin(theta/2+off)/5;
		mesh.position.z = Math.sin(theta+off)/2;
            }

	}


	function render() {
	    TWEEN.update();
	    uniforms.time.value += 0.02;

	    theta += theta_offset;

	    if ( postprocessing.enabled ) {

		renderer.clear();

		// Render scene into texture

		renderer.render( scene, camera, postprocessing.rtTexture1, true );

		// Render quad with blured scene into texture (convolution pass 1)

		postprocessing.quad.materials = [ postprocessing.materialConvolution ];

		postprocessing.materialConvolution.uniforms.tDiffuse.texture = postprocessing.rtTexture1;
		postprocessing.materialConvolution.uniforms.uImageIncrement.value = postprocessing.blurx;

		renderer.render( postprocessing.scene, postprocessing.camera, postprocessing.rtTexture2, true );

		// Render quad with blured scene into texture (convolution pass 2)

		postprocessing.materialConvolution.uniforms.tDiffuse.texture = postprocessing.rtTexture2;
		postprocessing.materialConvolution.uniforms.uImageIncrement.value = postprocessing.blury;

		renderer.render( postprocessing.scene, postprocessing.camera, postprocessing.rtTexture3, true );

		// Render original scene with superimposed blur to texture

		postprocessing.quad.materials = [ postprocessing.materialScreen ];

		postprocessing.materialScreen.uniforms.tDiffuse.texture = postprocessing.rtTexture3;
		postprocessing.materialScreen.uniforms.opacity.value = 1.25;

		renderer.render( postprocessing.scene, postprocessing.camera, postprocessing.rtTexture1, false );

		// Render to screen

		postprocessing.materialFilm.uniforms.time.value += 0.01;
		postprocessing.quad.materials = [ postprocessing.materialFilm ];

		postprocessing.materialScreen.uniforms.tDiffuse.texture = postprocessing.rtTexture1;
		renderer.render( postprocessing.scene, postprocessing.camera );

	    } else {

		renderer.clear();
		renderer.render( scene, camera );

	    }


	}
    });
