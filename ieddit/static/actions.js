$(document).ready(function() {/*
	$('.tl-dropdown').on('hide.bs.dropdown', function () {
		$(this).css('height', '0.5rem');
	})
	$('.tl-dropdown').on('show.bs.dropdown', function () {
		$(this).css('height', '30rem');
	});*/

	//jsalert('test', 'danger');
});

function banAndDeleteAll(itype, iid) {
	$.post('/admin/ban_and_delete', itype + '=' + iid).done(function(data) {
		location.reload();
	});
}

function blockUser(itype, iid) {
	$.post('/user/block_user', itype + '=' + iid).done(function(data) {
		location.reload();
	});
}

function hideObject(itype, iid) {
	itype = itype + ''
	iid = iid + ''

	$.post('/user/hide', {d:'{"' + itype + '":"' + iid + '"}'}).done(function(data) {
		if (data === 'ok') {
			jsalert('blocked ' + itype + ' ' + iid, 'success');
			if (itype === 'post_id') {
				$('#top-of-post-' + iid).css('display', 'none');
			} else if (itype === 'comment_id') {
				//$('#comment-' + iid).css('display', 'none');
				minHide(iid, undefined, true);
			} else if (itype === 'other_user') {
					$('#block-user-button-u').css('display', 'none');
					$('#block-user-button').css('display', 'inline-block');
					location.reload();
					jsalert('blocked user', 'success');
					return;
			}
		} else {
			jsalert('error: ' + data, 'danger');
		}
	});
}

function showObject(itype, iid) {
	itype = itype + ''
	iid = iid + ''

	$.post('/user/show', {d:'{"' + itype + '":"' + iid + '"}'}).done(function(data) {
		if (data === 'ok') {
			jsalert('unblocked ' + itype + ' ' + iid, 'success');
			if ('#block-user-button-u' !== undefined) {
				$('#block-user-button-u').css('display', 'none');
				$('#block-user-button').css('display', 'inline-block');
				jsalert('unblocked user', 'success');
				location.reload();
				return;
			}
			console.log($('#' + itype + '-' + iid).html());
			$('#' + itype + '-' + iid).remove();

		} else {
			jsalert('error: ' + data, 'danger');
		}
	});
}

function jsalert(message, atype) {
	width = parseInt($('#content').width() * 0.75);
	if (atype === 'undefined') {
		atype = 'success';
	}
	html = `		
	<div id='alert-container' class='js-alert' style='margin-top: -70px; display: inline-block; z-index: 101; width: ` + width + `px; position: fixed;' class='bg-light'>
			<ul style='display: inline-block; width: 100%; margin: 0; padding: 0;' class='flashes generic-alert bg-light'>
			<div style='display: inline-block; width: 100%; margin: 0;' class="alert alert-dismissible alert-` + atype + ` fade show" role="alert">
				` + message + `
				<button type="button" class="close" data-dismiss="alert" aria-label="Close">
				<span aria-hidden="true">&times;</span>
				</button>
			</div>
			</ul>
		</div>
	</div>`
	$('#content').prepend($(html));

	setTimeout(function() {
		autoFadeErrors();
		$('.js-alert').css('display', 'none');
	}, 5000);
}

function goToLink(val) {
	var r = confirm(val);
	if (r === false) {
		return;
	}
	elem = $('#' + val);
	window.location($(elem).attr('href'));
}

function formSubmit(val) {
	var r = confirm(val);
	if (r === false) {
		return;
	}
	elem = $('#' + val);

	if ($(elem).attr('href') !== 'undefined' ) {
		window.location = $(elem).attr('href');
	}
	btn = $('#btn-' + val);
	console.log(btn);
	console.log(elem);
	val = val.split('-');
	itype = val[0]
	action = val[1]
	iid = val[2]
	console.log(val);
	$(btn).click();
}

function copyToClipboard(text) {
    var dummy = document.createElement("textarea");
    // to avoid breaking orgain page when copying more words
    // cant copy when adding below this code
    // dummy.style.display = 'none'
    document.body.appendChild(dummy);
    //Be careful if you use texarea. setAttribute('value', value), which works with "input" does not work with "textarea". – Eduard
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
}
