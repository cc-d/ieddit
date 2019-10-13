$(document).ready(function() {

});

function getPhrase() {
	var privKey = $('#self-pgp-privkey').val();
	var pubKey = $('#self-pgp-pubkey').val();
	var otherPubKey = $('#other-pgp-pubkey').val();

	var phrase = prompt('enter passphrase');

	var r = openpgp.key.readArmored(privKey).then(function(pkey) {
		pkey.keys[0].decrypt(phrase).then(function(decrypted) {
			if (decrypted) {
				return true;
			} else {
				return false;
			}
		});
	});

	if (r) {
		return phrase;
	} else {
		return false;
	}
}

function getKeys() {
	return new Promise(function(resolve, reject) {
		setTimeout(function() {
			resolve(openpgp.key.readArmored($('#other-pgp-pubkey').val()));
		}, 200);
	});
}

var options = {};

function getOptions() {
	return new Promise(function(resolve, reject) {
		setTimeout(function() {
			getKeys().then(function(keys) {
				options = {
					message: openpgp.message.fromText($('#message-textarea').val()),
					publicKeys: keys.keys
				}
				resolve(options);
			});
		}, 400);
	});
}

function encryptText() {
	if (getPhrase()) {
		getOptions().then(function(opts) {
			console.log(opts);
			openpgp.encrypt(opts).then(encryptedData => {
				console.log(encryptedData);
				$('#message-textarea').val(encryptedData.data);
			});
		});
	}
}