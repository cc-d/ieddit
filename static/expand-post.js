var maxWidth = 0;
var widthBreak = 768;

$(document).ready(function() {
	maxWidth = $('.posts-media-body').first().width();
	if (maxWidth <= widthBreak) {
		maxWidth = maxWidth + 80; // thumbnail will be hidden on expansion, it is 80px
	}
	$("<style type='text/css'> .expanded-post-image { max-width: " + maxWidth + "px; max-height: " + 
		(maxWidth) + "px; } </style>").appendTo("body");
	console.log(maxWidth);
});

function expandPost(pid, ptype) {
	realsource = $('#expand-src-' + pid);
	src = realsource.attr('realsrc');
	realsource.attr('src', src);
	realsource.html(realsource);

	post = $('#post-' + pid);
	post.css('display', 'inline-block');

	if (maxWidth <= widthBreak) {
		$('#post-thumb-' + pid).css('display', 'none');
		post.parent().css('margin-left', '0.75rem');
	}

	button = $('#expand-button-' + pid);
	button.children('i').attr('class', 'fa fa-minus-square-o');
	button.attr('href', "javascript:collapsePost(pid=" + pid + ", ptype='" + ptype + "');");
}

function collapsePost(pid, ptype) {
	post = $('#post-' + pid);
	post.css('display', 'none');

	if (maxWidth <= widthBreak) {
		$('#post-thumb-' + pid).css('display', 'block');
		post.parent().css('margin-left', '0');
	}

	button = $('#expand-button-' + pid);
	button.children('i').attr('class', 'fa fa-plus-square-o');
	button.attr('href', "javascript:expandPost(pid=" + pid + ", ptype='" + ptype + "');");
}
