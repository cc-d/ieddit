var finalPhrase = undefined;

$(document).ready(function() {
	$('#generateNewPublicKey').click(function(){
		makeKeys();
	});
	$('#replacePrivateKey').click(function(){
		makeKeys();
	});

	$('#readEncryptedMessages').click(function(){
		privKey = $('#self-pgp-privkey').val();
		emsgs = $('.emessage');
		decryptMessage(emsg, phrase, privKey, mid, pubk);
	})

	$('.readEncryptedMessage').click(function(e){
		var msgid = e.target.attributes['aria-msgid'].value;
		decryptMessage(msgid);
	});

	$('#encryptMessageButton').click(function(){
		encryptMessage();
	})

	$('#copyToClipboard').click(function() {
		var c = document.getElementById('secret');
		c.select();
		c.setSelectionRange(0,99999);
		document.execCommand('copy');
		$('#copyText').css('display', 'block');
		window.setTimeout(function() {
			$('#copyText').fadeOut();
			$('#copyText').css('display', 'none');
			//$('#copyToClipboard').text(
		}, 3000);
	});

	$('#decrypt-button').click(function() {
		decryptAll();
	});


});


function decryptAll() {
	passPhrase = localStorage.getItem('pgp_passphrase');
	if (passPhrase == undefined) {
		passPhrase = prompt('could not find phrase in local storage. please enter');
	}
	console.log('passphrase is ' + passPhrase);
	var emsgs = $('.emessage');
	for(i=0; i<emsgs.length; i++) {
		try {
			eid = $(emsgs[i]).attr('id').split('-')[2]
			console.log('trying to decrypt ' + eid);
			decryptMessage(eid, passPhrase);
		} catch (err) {
			console.log(err);
		}
	}
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


const decryptMessage = async(msgid, passphrase) => {
	let privkey = $('#self-pgp-privkey').val();
	let pubkey = $('#self-pgp-pubkey').val();
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
			$('#decryptedContent-' + msgid).prev().css('display', 'none');
		});
	}catch (e) {
		$('#decryptedContent-' + msgid).text("There was an error decrypting the message. Please ensure you have the correct passphrase.").fadeIn();
	}
};

function makeKeys(pphrase){
	$('#copyToClipboard').css('display', 'inline-block');
	$('#copyContainer').css('display', 'inline-block');

	if (pphrase == undefined) {
		passphrase = generatePassphrase();
	} else {
		passphrase = pphrase;
	}
	
	finalPhrase = pphrase;

	$('#secret').val(passphrase);

	useremail = $('#useremail').val();
	username = $('#username').val();

	$('#generateNewPublicKey').attr('id', 'replacePrivateKey');

	var options = {
		userIds: [{ name:username, email:useremail }],
		curve: "ed25519",
		passphrase: passphrase
	};

	openpgp.generateKey(options).then(function(key) {
		var privkey = key.privateKeyArmored; // '-----BEGIN PGP PRIVATE KEY BLOCK ... '
		var pubkey = key.publicKeyArmored;   // '-----BEGIN PGP PUBLIC KEY BLOCK ... '
		var revocationCertificate = key.revocationCertificate; // '-----BEGIN PGP PUBLIC KEY BLOCK ... '

		$('#hideThisText').remove();

		$('#privkey').text(privkey);
		$('#pubkey').text(pubkey);
		$('#passphrase').css('display', 'block');
		$('#gen-key-btn').css('display', 'none');
		$('#scrollDownText').css('display', 'block');

		$('#replacePrivateKey').text('use a custom passphrase');
		$('#replacePrivateKey').attr('class', 'rounded btn btn-danger');
		$('#replacePrivateKey').unbind();
		$('#replacePrivateKey').click(function() {
			customPhrase();
		});
//
//		$('#secret').css('background-color', 'white!important');
//		$('#secret')
//
	});
}

function customPhrase() {
	$('#secret').removeAttr('readonly');
	$('#secret').before($('<style>#secret{background-color: white!important;}</style>'));
	$('#secret').css('border', '1px dotted red');

	$('#secret').css('height', ($('#secret').height() * 1.5) + 'px');
	$('#secret').css('width', ($('#secret').width() * 1.5) + 'px');

	$('#secret').before($('<h5 style="color: red;"> You are responsible for whichever custom passphrase you choose</h5>'));
	$('#secret').before($('<h6 style="color: red;"> Please do not choose a weak passphrase. </h6>'));
	$('#secret').val('');
	$('#replacePrivateKey').text('save custom passphrase');
	//$('#secret').unbind('click');
	$('#replacePrivateKey').unbind('click');
	$('#replacePrivateKey').attr('onclick', 'saveCustom()');
}


function saveCustom() {
	$('#replacePrivateKey').css('opacity', '0.3');
	if ($('#secret').val() == '') {
		alert('no passphrase entered');
		return;
	}
	pphrase = $('#secret').val();
	makeKeys(pphrase);
	$('#secret').before($('<style>#secret{background-color: dimgrey!important;}</style>'));
	$('#secret').attr('readonly', '');
	$('replacePrivateKey').css('opacity', '0.35');
}

function savePhrase(phrase) {
	if (phrase === undefined) {
		phrase = finalPhrase;
	}

	if (phrase === undefined) {
		phrase = $('#secret').val();
	}
	console.log('saving ' + phrase);
	localStorage.setItem('pgp_passphrase', phrase);
	$('#saveForm').submit();
	return true;
}


