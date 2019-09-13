$(document).on('click', '.comment-reply', function () {
	$('#reply-box').detach().appendTo($(this));
    //$(this).append($('#reply-box').html());
});
console.log('loaded');