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

        customFade($('#copyText'));
    });

    $('#decrypt-button').click(function() {
        decryptAll();
    });
});

var cf = undefined;

function customFade(element) {
    counter = 0;
    cf = window.setInterval(function() {
        counter += 4;
        setOpacity(element, counter);   
    }, 100);
}


function setOpacity(element, fadeLevel) {
        if (fadeLevel == undefined) {
            fadeLevel = 1;
        }
        op = (100 - fadeLevel);
        if (('' + op).length == 1) {
            op = '0' + (op + '')
        }
        op = '0.' + op;

        $(element).css('opacity', op);
        
        if (fadeLevel >= 100) {
            clearInterval(cf);
        }
}

function autoGetPhrase(ask=false) {
    passPhrase = localStorage.getItem('pgp_passphrase');
    console.log(passPhrase, ask)
    if (passPhrase === 'undefined' || ask === true) {
        console.log('asking');
        passPhrase = prompt('could not find phrase in local storage. please enter');
        localStorage.setItem('pgp_passphrase', passPhrase);
    }
    return passPhrase;
}

var success = false;

function decryptAll(attempts) {
    var emsgs = $('.emessage');
    var passPhrase = autoGetPhrase(ask=false);

    if (attempts === undefined) {
        console.log('first setting 0');
        var attempts = 0;
    } else {
        if (attempts === 1) {
            console.log('second asking');
            passPhrase = autoGetPhrase(ask=true);
        } else {
            console.log(attempts);
            alert('could not get passphrase');
            return false;
        }
    }


    for(i=0; i<emsgs.length; i++) {
        try {
            eid = $(emsgs[i]).attr('id').split('-')[2]
            console.log('trying to decrypt ' + eid);
            decryptMessage(eid, passPhrase);
            success = true;
        } catch (err) {
            console.log(err);
        }
    }

    if (success === false) {
        decryptAll(attempts=attempts + 1);
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


const encryptMessage = async(ask=false) => {
    $('#msgencrypted').val(true);
    var privkey = $('#self-pgp-privkey').val();
    var pubkey = $('#other-pgp-pubkey').val();
    var passphrase = autoGetPhrase(ask=ask);
    var msg = $('#message-textarea').val()
    console.log(ask);
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
            $('#encryptMessageButton').replaceWith($('<button type="button" class="btn btn-sm btn-success" ' + 
                'id="encryptMessageButton" disabled><i class="fa fa-lock"></i> message encrypted</button>'));
            $('#msgencrypted').val('true');
        });

    }catch (e) {
        if (ask === false) {
            console.log('invalid passphrase');
            encryptMessage(ask=true);
        } else {

            alert('could not decrypt');
        }
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
//      $('#secret').css('background-color', 'white!important');
//      $('#secret')
//
    });
}

function customPhrase() {
    $('#secret-lock').css('display', 'none');
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


