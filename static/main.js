var fontColor = '#bbb';
var rgbFontColor = 'rgb(187, 187, 187)';

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
					$(self).parent().parent().children('a').children('.fa-arrow-down').css('color', fontColor);
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
					$(self).parent().parent().children('a').children('.fa-arrow-down').css('color', fontColor);
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
					$(self).css('color', fontColor);
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
					$(self).css('color', fontColor);
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
	if($(self).css('color') == rgbFontColor) {
		if (oType == 'post') {
			$.post('/vote', {'vote':'-1', 'post_id':voteId}).done( function(data) {
				if (data == 'not logged in') {
					alert('please login to vote');
				} else if (isNaN(data) == false) {
					$(voteDiv).html(data);
					$(self).css('color', 'rgb(173, 216, 230)');
					$(self).parent().parent().children('a').children('.fa-arrow-up').css('color', fontColor);
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
					$(self).parent().parent().children('a').children('.fa-arrow-up').css('color', fontColor);
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
					$(self).css('color', fontColor);
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
					$(self).css('color', fontColor);
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






/* I have no idea what is going on, but it works. */


/* Score a list of strings based on how many characters they share in common with
the input string */

var q = false
function sortSearch(a, az) {
	console.log(a, az)
	aza = {}
	for (i=0; i<az.length; i++) {
		aza[az[i]] = 0;
	}
	newa = '';
	for (i=0; i<a.length; i++) {
		newa = newa + a[i];

		for (ii=0; ii<az.length; ii++) {
			console.log(az[ii].indexOf(newa))
			if (az[ii].indexOf(newa) != -1) {
				aza[az[ii]] += 1
			}
		}
	}
	return aza
}

/* wait for keychange event in the sub select searchbox andthen
send the entered string to sortSearch */

function listReady() {

$(document).ready(function(){
	aza = []
	drop = $('.sublist-dropdown');
	for(i=0; i<drop.length; i++) {
		aza.push($(drop[i]).text())
	}
	q = aza
  $("#sub-dropdown-search").on("keyup", function() {
  	aza = q
    var value = $(this).val().toLowerCase();
    z = swap(sortSearch(value, q));

  });
});


/* search in menu for a match */

function search() {
	$("#sub-dropdown-search").on("keyup", function() {
		var value = $(this).val().toLowerCase();
	});
}

/* swap menu objects */


function swap(sS) {
var items = Object.keys(sS).map(function(key) {
  return [key, sS[key]];
});
items.sort(function(first, second) {
  return second[1] - first[1];
});
z = ''
for(i=0; i<items.length; i++){
	console.log(items[i])
	z = z +'<a class="dropdown-item sublist-dropdown" href="javascript:setSub(\'' + items[i][0] + '\')">' + items[i][0] + '</a>';
}
$('#menu-items').html($(z));
}


/* Not complaining. */

}

function getAttributes ( $node ) {
	if ($node[0] == undefined) {
		return 0;
	}
    var attrs = {};
    $.each( $node[0].attributes, function ( index, attribute ) {
        attrs[attribute.name] = attribute.value;
    } );

    return attrs;
}


var re = new RegExp('.*\..*\/create_post')

if (re.test(window.location)) {
	function getSubLinks() {
		$.get('/get_sub_list', function(data, status) {
			$('#menu-items').html(data);

			listReady();
		});
	}

	getSubLinks();
}

function hideComments(comment) {
	parent = $(comment).parents('.sub-comment')

	if ($(parent) != undefined) {
		$(parent).css('overflow','hidden');
		$(parent).css('height','2rem');

		$(comment).text('[+]');
		$(comment).removeClass('hide-comment')
		$(comment).addClass('show-comment')

		plevel = $(parent).attr('level')


		child = $(parent).next()

		if (child != undefined) {
			clevel = $(child).attr('level');
			console.log(clevel, plevel);
			if (clevel >= plevel ) {
				hideComments($(child).find('.hide-comment'));
			}
		}

	}

	$('.show-comment').on('click', function() {
		showComments($(this));
	});

}


function showComments(comment) {
	parent = $(comment).parents('.sub-comment')

	if (parent != undefined) {
		parent.css('overflow','');
		parent.css('height','');

		comment.text('[-]');
		comment.removeClass('show-comment')
		comment.addClass('hide-comment')

		plevel = parent.attr('level')


		child = parent.next()
		
		if (child != undefined) {
			clevel = child.attr('level');
			console.log(clevel, plevel);
			if (clevel >= plevel ) {
				showComments(child.find('.show-comment'));
			}
		}

	}

	$('.hide-comment').on('click', function() {
		hideComments($(this));
	});

}


$(document).ready(function() {
	$('.hide-comment').on('click', function() {
		hideComments($(this));
	});
});

console.log('loaded');