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

	$('#comment-reply-box').css('display', 'inline-block');
	$(this).after($('#comment-reply-box'));
	$(this).css('display', 'none');

	if($('#reply-box').parent().attr('comment_id') !== undefined) {
		$('#reply-box').parent().text('reply');
	}
});
console.log('loaded');