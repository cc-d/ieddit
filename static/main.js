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
// Copy paste coding, refactor when time
$(document).on('click', '.fa-arrow-up', function() {
	var oType = $(this).parent().parent().attr('vote-obj-type');
	var voteId = $(this).parent().parent().attr('vote-obj-id');
	var voteDiv = $(this).parent().parent().children('vote');
	var self = $(this);
	if($(self).css('color') != 'rgb(255, 165, 0)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'1', 'post_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', 'orange');
					$(self).parent().parent().children('a').children('.fa-arrow-down').css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'1', 'comment_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', 'orange');
					$(self).parent().parent().children('a').children('.fa-arrow-down').css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
	} else if ($(self).css('color') == 'rgb(255, 165, 0)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'0', 'post_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'0', 'comment_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
	}
});

$(document).on('click', '.fa-arrow-down', function() {
	var oType = $(this).parent().parent().attr('vote-obj-type');
	var voteId = $(this).parent().parent().attr('vote-obj-id');
	var voteDiv = $(this).parent().parent().children('vote');
	var self = $(this);
	if($(self).css('color') == 'rgb(33, 37, 41)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'-1', 'post_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', 'rgb(173, 216, 230)');
					$(self).parent().parent().children('a').children('.fa-arrow-up').css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'-1', 'comment_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', 'rgb(173, 216, 230)');
					$(self).parent().parent().children('a').children('.fa-arrow-up').css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) - 1);
		}
	} else if ($(self).css('color') == 'rgb(173, 216, 230)') {
		if (oType == 'post') {
			$.post('/vote', {'vote':'0', 'post_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
		else if (oType == 'comment') {
			$.post('/vote', {'vote':'0', 'comment_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', '#212529');
				}
			});
			//$(voteDiv).html(parseInt(voteDiv.html()) + 1);
		}
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

// Suggest Title
var re = new RegExp('.*\..*\/create_post')

if (re.test(window.location)) {

setInterval(lookForChange, 1000);

function lookForChange()
{
	var re = new RegExp('^https?:\/\/')
    var utext = document.getElementById("create-post-url").value;
    if (re.test(utext)) {
    	if ($('#suggest-title').text() != 'suggest title') {
        	$('#suggest-title').text('suggest title');
        }
    }
}

function suggestTitle() {
	var re = new RegExp('^https?:\/\/')
	var utext = document.getElementById("create-post-url").value;
	if (re.test(utext)) {
		$.get('/suggest_title?u=' + utext, function(data, status) {
			$('#create-post-title').val(data);
			});
		}
	}
}

// Suggest Title


function setSub(sub) {
	$('#create-post-sub').val(sub.replace('/r/', ''));
}




console.log('loaded');