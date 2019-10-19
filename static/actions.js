$(document).ready(function() {

});

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
