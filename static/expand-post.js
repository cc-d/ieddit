







var maxWidth = 0;
var widthBreak = 768;

$(document).ready(function() {
	maxWidth = $('.posts-media-body').first().width();
	if (maxWidth <= widthBreak) {
		maxWidth = maxWidth + 80; // thumbnail will be hidden on expansion, it is 80px
	}
	$("<style type='text/css'> .expanded-post-image { max-width: " + maxWidth + "px; max-height: " + 
		(maxWidth) + "px; } </style>").appendTo("body");

	pe = $('#is-pre-expanded');
	if (pe != undefined) {
		pid = pe.attr('vidid');
		post = $('#post-thumb-' + pid);
		post.css('display', 'none');
		post.parent().css('margin-left', '0.75rem');
	}

	maxVidSize();

});

width = 0;

function maxVidSize() {
	maxW = 550;

	widtha = $('.sub-post');
	if (widtha.length > 1) {
		widtha = widtha[0]
	}

	// 16 because each side is 0.5rem
	width = parseInt(($(widtha).width() - 4));
	console.log(width);

	if (width > maxW) {
		width = maxW;
	}


	if (true) {
		// 4:3 ratio
		height = (width * (0.75));
		vids = $('.vidembed');
		if (vids.length == 1) {
			vids = [vids]
		}
		for (i=0; i<vids.length; i++) {
			vids[i].attr('height', parseInt(height));
			vids[i].attr('width', parseInt(width));
		}
	}
}

function pauseVideo(pid) {
	vid = $('#vid-' + pid);
	vid.removeAttr('src');
}

function expandPost(pid, ptype, vid) {
	if (vid == false) {
		realsource = $('#expand-src-' + pid);
		src = realsource.attr('realsrc');
		realsource.attr('src', src);
		realsource.html(realsource);
	} else {
		v = $('#vid-' + pid);
		src = v.attr('realsrc');
		console.log(src)
		v.attr('src', src);
		v.html(v);
		v.css('display', '');

		$('#post-thumb-' + pid).css('display', 'none');
		post.parent().css('margin-left', '0.75rem');
	}

	post = $('#post-' + pid);
	post.css('display', 'inline-block');

	if (maxWidth <= widthBreak) {
		$('#post-thumb-' + pid).css('display', 'none');
		post.parent().css('margin-left', '0.75rem');
	}

	button = $('#expand-button-' + pid);
	button.attr('class', '');
	button.children('i').attr('class', 'fa fa-minus-square-o');
	button.attr('href', "javascript:collapsePost(pid=" + pid + ", ptype='" + ptype + "', vid=" + vid + ");");
}

function collapsePost(pid, ptype, vid) {
	post = $('#post-' + pid);
	post.css('display', 'none');

	if (maxWidth <= widthBreak) {
		$('#post-thumb-' + pid).css('display', 'block');
		post.parent().css('margin-left', '0');
	}

	button = $('#expand-button-' + pid);

	button.attr('class', "video-play-btn rounded");

	if (vid) {
		button.children('i').attr('class', 'fa fa-play');
	} else {
		button.children('i').attr('class', 'fa fa-plus-square-o');
	}

	pauseVideo(pid);	

	button.attr('href', "javascript:expandPost(pid=" + pid + ", ptype='" + ptype + "', vid=" + vid + ");");
}
