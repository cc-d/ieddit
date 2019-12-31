$(document).ready(function() {

});

function banAndDeleteAll(itype, iid) {
    $.post('/admin/ban_and_delete', itype + '=' + iid).done(function(data) {
        location.reload();
    });
}

function adminAnnouncement(itype, iid) {
    $.post('/admin/announcement', itype + '=' + iid).done(function(data) {
        location.reload();
    });
}

function blockUser(itype, iid) {
    $.post('/user/block_user', itype + '=' + iid).done(function(data) {
        location.reload();
    });
}

function addApiKey(user) {
    $.post('/admin/add_api_key', 'username' + '=' + user).done(function(data) {
        location.reload();
    });
}

function removeApiKey(user) {
    $.post('/admin/remove_api_key', 'username' + '=' + user).done(function(data) {
        location.reload();
    });
}

function addSubMute(sub) {
    $.post('/admin/add_sub_mute', 'sub' + '=' + sub).done(function(data) {
        location.reload();
    });
}

function removeSubMute(sub) {
    $.post('/admin/remove_sub_mute', 'sub' + '=' + sub).done(function(data) {
        location.reload();
    });
}

function hideObject(itype, iid) {
    itype = itype.toString();
    iid = iid.toString();

    $.post('/user/hide', {d:'{"' + itype + '":"' + iid + '"}'}).done(function(data) {
        if (data === 'ok') {
            jsalert('2blocked ' + itype + ' ' + iid, 'success');
            if (itype === 'post_id') {
                $('#top-of-post-' + iid).css('display', 'none');
            } else if (itype === 'comment_id') {
                $('#comment-' + iid).css('display', 'none');
                minHide(iid, undefined, true);
            } else if (itype === 'other_user') {
                    $('#block-user-button-u').css('display', 'none');
                    $('#block-user-button').css('display', 'inline-block');
                    jsalert('blocked user', 'success');
            }
        } else {
            jsalert('error: ' + data, 'danger');
        }
    });
}

function showObject(itype, iid) {
    itype = itype.toString();
    iid = iid.toString();

    $.post('/user/show', {d:'{"' + itype + '":"' + iid + '"}'}).done(function(data) {
        if (data === 'ok') {
            jsalert('unblocked ' + itype + ' ' + iid, 'success');
            if ('#block-user-button-u' !== undefined) {
                $('#block-user-button-u').css('display', 'none');
                $('#block-user-button').css('display', 'inline-block');

                //jsalert('unblocked user', 'success');
                /*
                location.reload();*/
            }
            $('#' + itype + '-' + iid).remove();

        } else {
            jsalert('error: ' + data, 'danger');
        }
    });
}

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

    btn = $('#btn-' + val);

    formId = val;

    val = val.split('-');

    itype = val[0]
    action = val[1]
    iid = val[2]

    if (val[2] == 'ban' || val[2] == 'unban') {
        $('#' + formId).click();
        return;
    }

    $('#btn-' + formId).click();
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

function downloadData(data, filename=null) {
    // I hate this, but if we want to support older browsers we need to do this.
    var blob = new Blob([data]);
    var link = document.createElement("a");
    $(link).css({"display": "none"})
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}

function downloadUserData(username) {
    $.get("/api/get_user/" + username).done(function (data) {
        return downloadData(data, username + "_data.json");
    });
}
