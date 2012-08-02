/*Copyright (C) 2009-2012 :
     Gabes Jean, naparuba@gmail.com
     Gerhard Lausser, Gerhard.Lausser@consol.de
     Gregory Starck, g.starck@gmail.com
     Hartmut Goebel, h.goebel@goebel-consult.de
     Andreas Karfusehr, andreas@karfusehr.de

 This file is part of Shinken.

 Shinken is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Shinken is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
*/


function add_new_upload(i, file){
    console.log('Add a new file upload' + file+ ' '+i);
    var fname = file.name;
    var size = file.size;
    s = '<span id="file-'+i+'" class="span10 alert alert-info"><span class="span6">Uploading <b>'+fname+'</b> with size '+size+'b</span>';

    s += '<div id="file-bar-contain-'+i+'" class="span10 progress active"> <div id="file-bar-'+i+'" class="bar" style="width: 0%;"></div></div>';

    s += '<div id="file-bar-value-'+i+'" class="span1">0%</div>'

    s += '</span>';
    var o = $(s);
    $('#files').append(o);
}


function upload_finish(i, file, response, time){
    console.log('Response'+response.state+' for file'+file+'in time'+time+ ' '+i);
    var f = $('#file-'+i);
    f.removeClass('alert-info');
    if (response.state == 'ok'){
	f.addClass('alert-success');
    }else{
	f.addClass('alert-error');
    }

}


function update_progress(i, file, percent){
    console.log('Progress for file'+file+ 'with '+percent+ ' '+i);
    var bar = $('#file-bar-'+i);
    bar.css('width', ''+percent+'%');
    var value = $('#file-bar-value-'+i);
    value.html(''+percent+'%');
    // If finish, remove the active bar
    if(percent == 100){
	var cont = $('#file-bar-contain-'+i);
	cont.removeClass('active');
    }
}

function update_speed(i, file, speed){
    console.log('File speed for'+i+' '+file+' speed'+speed+ ' '+i);
}


function file_too_large(file){
    console.log('File too large');
    var m = $('#messages');
    m.addClass('alert-error');
    m.html('Sorry this file is too large. The limit is 5mb');
    m.show();
}


$(function () {
    $('#messages').hide();
});

$(function () {
    console.log('Drop?'+$('#dropzone').length);
    $('#dropzone').filedrop({
	fallback_id: 'upload_button',    // an identifier of a standard file input element
	url: '/push',              // upload handler, handles each file separately
	paramname: 'data',          // POST parameter name used on serverside to reference file
	data: {'key':'value'},
	headers: {          // Send additional request headers
            'header': 'data'
	},
	error: function(err, file) {
            switch(err) {
            case 'BrowserNotSupported':
                alert('browser does not support html5 drag and drop')
                break;
            case 'TooManyFiles':
                // user uploaded more than 'maxfiles'
                break;
            case 'FileTooLarge':
                // program encountered a file whose size is greater than 'maxfilesize'
                // FileTooLarge also has access to the file which was too large
                // use file.name to reference the filename of the culprit file
		file_too_large(file);
                break;
            default:
                break;
            }
	},
	maxfiles: 25,
	maxfilesize: 5,    // max file size in MBs
	dragOver: function() {
            // user dragging files over #dropzone
	},
	dragLeave: function() {
            // user dragging files out of #dropzone
	},
	docOver: function() {
            // user dragging files anywhere inside the browser document window
	},
	docLeave: function() {
            // user dragging files out of the browser document window
	},
	drop: function() {
            // user drops file
	},
	uploadStarted: function(i, file, len){
            // a file began uploading
            // i = index => 0, 1, 2, 3, 4 etc
            // file is the actual file of the index
            // len = total files user dropped
            add_new_upload(i, file);
	},
	uploadFinished: function(i, file, response, time) {
            // response is the data you got back from server in JSON format.
            console.log("uploadFinished for"+file+"res"+response+"in"+time);
	    upload_finish(i, file, response, time);
	},
	progressUpdated: function(i, file, progress) {
            // this function is used for large files and updates intermittently
            // progress is the integer value of file being uploaded percentage to completion
            console.log('Progress'+progress);
	    update_progress(i, file, progress);
	},
	speedUpdated: function(i, file, speed) {
	    update_speed(i, file, speed);
            // speed in kb/s
	},
	rename: function(name) {
            // name in string format
            // must return alternate name as string
	},
	beforeEach: function(file) {
            // file is a file object
            // return false to cancel upload
	},
	afterAll: function() {
            // runs after all files have been uploaded or otherwise dealt with
	}
    });
});