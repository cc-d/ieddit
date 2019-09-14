$(document).on('click', '.comment-reply', function () {
	var replycommid = $(this).attr('comment_id');
	if ($('#parent_id').val() == replycommid) {
		return;
	}
	//$(this).text('');
	$('#comment-reply-box').css('display', 'inline-block');
	$(this).after($('#comment-reply-box'));
	//$('#comment-reply-box').detach();
	if($('#reply-box').parent().attr('comment_id') !== undefined) {
		$('#reply-box').parent().text('reply');
	}/*
	$('#parent_id').val(replycommid);
	$('#post_comment_text').val('reply');*/
    //$(this).append($('#reply-box').html());
});
console.log('loaded');