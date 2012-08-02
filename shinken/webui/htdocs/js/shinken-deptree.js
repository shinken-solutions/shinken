



/* The business rules toggle buttons*/
function toggleBusinessElt(e) {
    //alert('Toggle'+e);
    var toc = document.getElementById('business-parents-'+e);
    var imgLink = document.getElementById('business-parents-img-'+e);

    img_src = '/static/images/';

    if (toc && toc.style.display == 'none') {
	toc.style.display = 'block';
	if (imgLink != null){
	    imgLink.src = img_src+'reduce.png';
	}
    } else {
	toc.style.display = 'none';
	if (imgLink != null){
	    imgLink.src = img_src+'expand.png';
	}
    }
}

