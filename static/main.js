$(document).on('click', '.comment-reply', function () {
	var replycommid = $(this).attr('comment_id');
	if ($('#parent_id').val() == replycommid) {
		return;
	}

	if ($('#comment-reply-box').css('display') != 'hidden') {
		if ($('#comment-reply-box').parent().children('a')[0] !== undefined) {
			$($('#comment-reply-box').parent().children('a')[0]).css('display', '');
		}
	}

	$('#comment-reply-box').css('display', 'block');
	$(this).parent().parent().after($('#comment-reply-box'));
	$('#parent_id').val($(this).attr('comment_id'));
	$(this).css('display', 'none');

	if($('#reply-box').parent().attr('comment_id') !== undefined) {
		$('#reply-box').parent().text('reply');
	}
});

$(document).on('click', '.fa-arrow-up', function() {
	if($(this).css('color') != 'rgb(255, 165, 0)') {
		$(this).css('color', 'orange');
		$(this).parent().parent().children('a').children('.fa-arrow-down').css('color', '#212529');
	} else if ($(this).css('color') == 'rgb(255, 165, 0)') {
		$(this).css('color', '#212529');
	}
});

$(document).on('click', '.fa-arrow-down', function() {
	if($(this).css('color') == 'rgb(33, 37, 41)') {
		$(this).css('color', 'rgb(173, 216, 230)');
		$(this).parent().parent().children('a').children('.fa-arrow-up').css('color', '#212529');
	} else if ($(this).css('color') == 'rgb(173, 216, 230)') {
		$(this).css('color', '#212529');
	}
});

console.log('loaded');