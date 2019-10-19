$(document).ready(function() {

});

function goToLink(val) {
	elem = $('#' + val);
	window.location($(elem).attr('href'));
}

function formSubmit(val) {
	console.log(val);
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