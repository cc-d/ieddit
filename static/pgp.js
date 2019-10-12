$(document).ready(function() {

});

var privKey = undefined;
var pubKey = undefined;
var loadedKeys = false;

function callbackKey(key, username) {
	var options = {
		userIds: [{ name: username, email: username + '@ieddit.com' }],
		numBits: 4096,
		curve: 'ed25519',
		passphrase: key
	}

	openpgp.generateKey(options).then(key => {
		privKey = key.privateKeyArmored
		pubKey = key.publicKeyArmored
	}).then(
		setTimeout(function() {
			$('#privkey').text(privKey);
			$('#pubkey').text(pubKey);
			openpgp.key.readArmored(privKey).then(function(pkey) {
				pkey.keys[0].decrypt(key).then(function(decrypted) {
					console.log(decrypted);
				});
			});
		})
	);

}

function generateKeyPairFromText(username) {
	var key = $('#secret').val();
	callbackKey(key, username);
}