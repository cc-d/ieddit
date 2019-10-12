$(document).ready(function() {

});

var privKey = undefined;
var pubKey = undefined;
var loadedKeys = false;

function checkKeys() {
	if (!loadedKeys) {
		if (privKey == undefined || pubKey == undefined) {
			
		} else {
			$('#privkey').text(privKey);
			$('#pubkey').text(pubKey);
			loadedKeys = true;
		}
	} 
}

window.setInterval(function(){
	checkKeys();
}, 500);

function callbackKey(key, username) {
	var options = {
		userIds: [{ name: username, email: username + '@ieddit.com' }],
		numBits: 4096,
		curve: "ed25519", 
		passphrase: key
	}

	openpgp.generateKey(options).then(key => {
		privKey = key.privateKeyArmored
		pubKey = key.publicKeyArmored
	});

}

function generateKeyPairFromText(username) {
	var key = $('#secret').val();
	callbackKey(key, username);
	//$('#privkey').text(privKey);
	//$('#pubkey').text(pubKey);
}