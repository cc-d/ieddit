$(document).ready(function() {
	$('#generateNewPublicKey').click(function(){
		generateKeyPairFromText('{{ session["username"] }}');
	});
	$('#replacePrivateKey').click(function(){
		generateKeyPairFromText('{{ session["username"] }}');
	});
});

var privKey = undefined;
var pubKey = undefined;
var loadedKeys = false;

function callbackKey(secret, username) {
	var options = {
		userIds: [{ name: username, email: username + '@ieddit.com' }],
		numBits: 4096,
		curve: 'ed25519',
		passphrase: secret
	}

	openpgp.generateKey(options).then(key => {
		privKey = key.privateKeyArmored
		pubKey = key.publicKeyArmored
	}).then(
		setTimeout(function() {
			$('#privkey').text(privKey);
			$('#pubkey').text(pubKey);
			$('#passphrase').css('display', 'block');
			$('#gen-key-btn').css('display', 'none');
			/*
			openpgp.key.readArmored(privKey).then(function(pkey) {
				console.log(pkey.keys[0]);
				pkey.keys[0].decrypt(secret).then(function(decrypted) {
					console.log(decrypted);
				});
			});
			*/
		})
	);

}

/* to generate a mnemonic */
function generatePassphrase() {
	let phrase = '';
	for (i=0; i<6; i++) {
		if (i == 5) {
			phrase = phrase + wordList[Math.floor(Math.random()*wordList.length)];
		} else {
			phrase = phrase + wordList[Math.floor(Math.random()*wordList.length)] + ' ';
		}
	}
	return phrase;
}

function generateKeyPairFromText(username) {
	var secret = generatePassphrase();
	$('#secret').val(secret);
	callbackKey(secret, username);
}
