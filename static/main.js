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
	var oType = $(this).parent().parent().attr('vote-obj-type');
	var voteId = $(this).parent().parent().attr('vote-obj-id');
	var voteDiv = $(this).parent().parent().children('vote');

	if($(this).css('color') != 'rgb(255, 165, 0)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'1', 'post_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'1', 'comment_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}

		$(this).css('color', 'orange');
		$(this).parent().parent().children('a').children('.fa-arrow-down').css('color', '#212529');
	} else if ($(this).css('color') == 'rgb(255, 165, 0)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'0', 'post_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'0', 'comment_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}

		$(this).css('color', '#212529');
	}
});

$(document).on('click', '.fa-arrow-down', function() {
	var oType = $(this).parent().parent().attr('vote-obj-type');
	var voteId = $(this).parent().parent().attr('vote-obj-id');
	var voteDiv = $(this).parent().parent().children('vote');

	if($(this).css('color') == 'rgb(33, 37, 41)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'-1', 'post_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'-1', 'comment_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}

		$(this).css('color', 'rgb(173, 216, 230)');
		$(this).parent().parent().children('a').children('.fa-arrow-up').css('color', '#212529');
	} else if ($(this).css('color') == 'rgb(173, 216, 230)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'0', 'post_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'0', 'comment_id':voteId}, function(data) {
				if (data !== 'already voted') {
					$(voteDiv).html(data);
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
		$(this).css('color', '#212529');
	}
});

function autoFadeErrors() {
	$(".alert").alert('close');
}

$(document).ready(function() {
	setTimeout(function() {
		autoFadeErrors(); 
	}, 5000);
});

console.log('loaded');