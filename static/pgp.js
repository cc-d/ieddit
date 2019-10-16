$(document).ready(function() {
	$('#generateNewPublicKey').click(function(){
		makeKeysMothaFucka($("#generateNewPublicKey").attr('aria-label'));
	});
	$('#replacePrivateKey').click(function(){
		makeKeysMothaFucka($("#generateNewPublicKey").attr('aria-label'));
	});

	$("#secret").click(function(e){
		e.target.select();
		document.execCommand("copy");
		$('#secret').parent().append("<div id=\'copiedText\''>copied to clipboard</div>")
		window.setTimeout(function(){
			$('#copiedText').fadeOut();
			$('#copiedText').remove();
		}, 2000)
	});

	$('#readEncryptedMessages').click(function(){
		privKey = $('#self-pgp-privkey').val();
		emsgs = $('.emessage');
		var phrase = prompt('enter passphrase');
		decryptMessage(emsg, phrase, privKey, mid, pubk);
	})

	$('.readEncryptedMessage').click(function(e){
		var msgid = e.target.attributes['aria-msgid'].value;
		decryptMessage(msgid);
	});

	$('#encryptMessageButton').click(function(){
		encryptMessage();
	})
});


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


const encryptMessage = async() => {
	$('#msgencrypted').val(true);
	var privkey = $('#self-pgp-privkey').val();
	var pubkey = $('#other-pgp-pubkey').val();
	var passphrase = prompt("passphrase");
	var msg = $('#message-textarea').val()

	try{
		const privKeyObj = (await openpgp.key.readArmored(privkey)).keys[0]
		await privKeyObj.decrypt(passphrase)

		const options = {
			message: openpgp.message.fromText(msg),
			publicKeys: (await openpgp.key.readArmored(pubkey)).keys,
			privateKeys: [privKeyObj]
		};

		openpgp.encrypt(options).then(ciphertext => {
			encrypted = ciphertext.data;
			$('#message-textarea').val(encrypted);
		});
	}catch (e) {
		alert("There was an error using your key. Please ensure you have the correct passphrase or reset it in your profile");
	}

};


const decryptMessage = async(msgid) => {
	let privkey = $('#self-pgp-privkey').val();
	let pubkey = $('#self-pgp-pubkey').val();
	let passphrase = prompt("passphrase");
	let msg = $('#encrypted-message-' + msgid)[0].textContent;
	const privKeyObj = (await openpgp.key.readArmored(privkey)).keys[0];

	try {
		await privKeyObj.decrypt(passphrase);
		const options = {
			message: await openpgp.message.readArmored(msg),
			publicKeys: (await openpgp.key.readArmored(pubkey)).keys,
			privateKeys: [privKeyObj]
		};
		openpgp.decrypt(options).then(plaintext => {
			$('#decryptedContent-' + msgid).text(plaintext.data).fadeIn();
		});
	}catch (e) {
		$('#decryptedContent-' + msgid).text("There was an error decrypting the message. Please ensure you have the correct passphrase.").fadeIn();
	}
};

function makeKeysMothaFucka(){
	passphrase = prompt("some words plox")
	useremail = $('#useremail').val();
	username = $('#username').val();
	var options = {
		userIds: [{ name:username, email:useremail }],
		curve: "ed25519",
		passphrase: passphrase
	};
	openpgp.generateKey(options).then(function(key) {
		var privkey = key.privateKeyArmored; // '-----BEGIN PGP PRIVATE KEY BLOCK ... '
		var pubkey = key.publicKeyArmored;   // '-----BEGIN PGP PUBLIC KEY BLOCK ... '
		var revocationCertificate = key.revocationCertificate; // '-----BEGIN PGP PUBLIC KEY BLOCK ... '
		$('#privkey').text(privkey);
		$('#pubkey').text(pubkey);
		$('#passphrase').css('display', 'block');
		$('#gen-key-btn').css('display', 'none');
	});
}