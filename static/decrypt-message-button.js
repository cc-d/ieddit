$(document).ready(function() {

});

function decryptAll() {
	privKey = $('#self-pgp-privkey').val();
	emsgs = $('.emessage');
	var phrase = prompt('enter passphrase');

	for (i=0; i<emsgs.length; i++) {
		var mid = $(emsgs[i]).attr('id').split('-')[2];
		var pubk = $('#other-pgp-pubkey-' + mid).val();
		//console.log(pubk);
		var mess = $('#encrypted-message-' + mid).text()

		openpgp.key.readArmored(pubk).then(function(pk) {
			try {
				decryptMessage(mess, phrase, privKey, mid, pk);
			} catch(err) {
				console.log(err);
			}
		});
	}
}


function getOptions(emsg, phrase, pkey, mid, pubk) {
	return new Promise(function(resolve, reject) {
		setTimeout(function() {
			options = {
				message: openpgp.message.fromText(emsg),
				privateKeys: pkey.keys
			}
			resolve(options);
		}, 400);
	});
}

function decryptMessage(emsg, phrase, privKey, mid, pubk) {
	openpgp.key.readArmored(privKey).then(function(pkey) {
		pkey.keys[0].decrypt(phrase).then(function(d) {
			console.log(emsg);
			console.log(phrase);
			console.log(pkey.keys);
			console.log(mid);
			console.log(pubk);
			console.log('\n\n\n\n\n\n\n')
			getOptions(emsg, phrase, pkey, mid, pubk).then(function(options) {
				openpgp.decrypt(options).then(function(dmsg) {
					// WHY IS THIS NOT WORKING
					// what the fuck?
					// it works up until this point, but ALWAYS fails when decrypting the message?
					// we are using the right key, because the .decrypt(phrase) worked...
					// ????
				});
			});
		});
	});
}
