from flask import Flask, render_template, session, request, redirect, flash, url_for, Blueprint, g

import urllib.parse
import random
import json
import re
import jinja2
import html
import config
import os.path
import os
from markdown import markdown
from bleach import clean, linkify

from datetime import datetime, timedelta
from math import log
import time

abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

legal_chars = '01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'

def thumb_exists(tid):
    if os.path.exists(abspath + '/static/thumbnails/thumb-%s.PNG' % str(tid)):
        if int(os.stat(abspath + '/static/thumbnails/thumb-%s.PNG' % str(tid)).st_size) > 10:
            return True
    return False

def rstring(length1, length2=False):
    if length2 == False:
        length2 = length1
    return ''.join([random.choice(legal_chars) for n in range(random.randint(length1, length2))])

def verify_username(username):
    if len(username) > 20 or len(username) < 1:
        return False
    for c in username:
        if c not in legal_chars:
            return False
    return True

def verify_subname(subname):
    if len(subname) > 30 or len(subname) < 1:
        return False
    for c in subname:
        if c not in legal_chars:
            return False
    return True

def convert_ied(url):
    url = url.lower()
    url = url.replace(' ', '_')
    url = url.replace('/', '')
    url = urllib.parse.quote(url)[:40]
    url = url.replace('%', '')
    return url

def post_url_parse(url):
    return urllib.parse.urlparse(url).netloc

def get_time():
    from datetime import datetime
    return datetime.now()

def time_ago(dt):
    diff = get_time() - dt
    if diff.days > 0:
        return str(int(diff.days)) + 'd'#ays ago'
    if diff.seconds < 60:
        return str(int(diff.seconds)) + 's'#econds ago'
    if diff.seconds > 60 and diff.seconds < 3600:
        return str(int(diff.seconds / 60)) + 'm'#inutes ago'
    if diff.seconds > 3600 and diff.seconds < 86400:
        return str(int((diff.seconds / 60) / 60)) + 'h'#ours ago'

# horribly ineffecient function lol
# like no seriously, this is really, really bad
# will change after release
def create_id_tree(comments, parent_id=None):
    tree = {}
    if not parent_id:
        for i in [c for c in comments if c.parent_id == None]:
            tree[i.id] = {}
    else:
        tree[int(parent_id)] = {}

    paths = {0:['tree']}
    depth = 0
    limit = 50
    while len(comments) > 0:
        paths[depth+1] = []
        if depth == 0:
            for z in tree.keys():
                paths[1].append('tree[' + str(z) + ']')
                comments = [a for a in comments if a.id != z]
        else:
            for p in paths[depth-1]:
                for com in [c for c in comments]:
                    try:
                        exec(p + '[' + str(com.parent_id ) + ']')
                        exec_txt = p + '[' + str(com.parent_id ) + '][' + str(com.id) + '] = {}'
                        exec(exec_txt)
                        paths[depth].append(p + '[' + str(com.parent_id ) + ']')
                        comments.remove(com)
                    except KeyError as e:
                        pass

        depth += 1
        if depth >= limit:
            break

    return tree

def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)

def comment_structure(comments, tree):
    new = {}
    for k, v in tree.items():
        cobj = next((x for x in comments if x.id == k), None)
        new[cobj] = comment_structure(comments, v)
    return new

# i hate math
def split_link(sst, s):
    new_s = []
    sindex = s.find(sst[0])
    new_s.append(s[:sindex-1])
    new_s.append(s[sindex:sindex + len(sst[0])])
    sindex = s.find(sst[1])
    new_s.append(s[(sindex):sindex+len(sst[1])])
    new_s.append(s[sindex+len(sst[1])+1:])
    return new_s

def get_tag_count(text):


    tag_count = len(re.findall('<[a-zA-Z0-9]*>[^<>"\']*<\/[a-zA-Z0-9]*>', text))
    tag_count += text.count('<br>')
    if text.find('\n') != -1:
        tag_count += text.count('\n')
    elif text.find('\r\n') != -1:
        tag_count += text.count('\r\n')


    return tag_count


def clean_and_linkify(text):
    clean_text = clean(markdown(text), strip=True)
    clean_text = linkify(clean_text)
    return clean_text


def pseudo_markup(text, escape_only=False):
    if escape_only:
        return html.escape(text).replace('&lt;br&gt;', '').replace('\n', '<br>')

    # really hacky way of preserving newlines right now, will address the problem
    # properly after making sure it at least works currently

    random_sequence = rstring(10)
    reverse_sequence = random_sequence[::-1]

    text = text.splitlines()
    for i in range(len(text)):
        if text[i] == '':
            text[i] = random_sequence

    # empty newlines will now be preserved after clean/bleach
    text = '\n'.join(text)

    # clean code block formatting
    if text.count('```') >= 2:
        new_text = ''
        text = text.split('```')
        for t in range(len(text)):
            if t == 0:
                new_text += clean_and_linkify(text[t])
            else:
                if t % 2 != 0:
                    if (len(text) - 1) > t:
                        etext = html.escape(text[t])
                        
                        # again using random sequence as a place holder
                        etext = etext.replace('\n', reverse_sequence)
                        etext = etext.replace(random_sequence, reverse_sequence)

                        new_text += '<div class="clean-code-wrap"><code class="clean-code">' + etext + '</code></div>'
                    else:
                        new_text += clean_and_linkify(text[t])
                else:
                    new_text += clean_and_linkify(text[t])
        clean_text = new_text
    else:
        clean_text = clean_and_linkify(text)
    
    # remove the line placeholder
    clean_text = clean_text.replace(random_sequence, '')
    clean_text = clean_text.replace('\n', '<br>')

    # restore newlines for pre-wrap code blocks
    clean_text = clean_text.replace(reverse_sequence, '\n')

    # html tags that should not end in <br>
    clean_tags = ['<ol>', '</ol>', '<li>', '</li>', '<ul>', '</ul>']
    for tag in clean_tags:
        clean_text = clean_text.replace(tag + '<br>', tag)

    return clean_text

epoch = datetime(1970, 1, 1)

def epoch_seconds(date):
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)

def score(ups, downs):
    return ups - downs

def hot(ups, downs, date):
    s = score(ups, downs)
    order = log(max(abs(s), 1), 10)
    sign = 1 if s > 0 else -1 if s < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(sign * order + seconds / 45000, 7)

def get_youtube_vid_id(url):
    if url == None:
        return False
    if url.find('youtube.com/watch?v=') != -1:
        return url.split('=')[1]
    if url.find('youtube.com/v/') != -1:
            url = url.split('/v/')[1]
            if url.find('?') == -1:
                    return url.split('?')[0]
            else:
                return url
    if url.find('youtu.be/') != -1:
        return url.split('.be/')[1]

    return False

def get_youtube_embed_url(url):
    """
    converts a youtube url into an embedded link
    """
    if url.find('youtube.com/watch?v=') != -1:
        vid_id = re.findall('\?v=(.[a-zA-Z0-9\-_]*)', url)[0]
    elif url.find('youtube.com/v/') != -1:
        vid_id = re.findall('\.com\/v\/(.[a-zA-Z0-9\-_]*)', url)[0]
    elif url.find('youtu.be/') != -1:
        vid_id = re.findall('youtu\.be\/(.[a-zA-Z0-9\-_]*)', url)[0]
    else:
        return False

    qargs = (urllib.parse.urlparse(url)).query.split('&')
    strip_qargs = ['v=', 'feature=']

    for strip in strip_qargs:
        qargs = [q for q in qargs if q.find(strip) == -1]

    qargs = [html.unescape(q) for q in qargs]

    if len(qargs) > 0:
        qargs = '&' + ('&'.join(qargs))
    else:
        qargs = ''

    url = 'https://www.youtube.com/embed/%s?version=3&enablejsapi=1%s' % (vid_id, qargs)
    url = url.replace('t=', 'start=')


    return url




# convert to dict
def sqla_to_dict(obj, expunge=None, include_attrs=None, show_anon=False):
    if expunge is None:
        expunge = []

    new_obj = {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in expunge}

    if 'anonymous' in new_obj.keys():
        if new_obj['anonymous'] is True:
            new_obj['author'] = 'Anonymous'
            new_obj['author_id'] = 0
            new_obj['author_type'] = 'user'

    if include_attrs is not None:
        for a in include_attrs:
            new_obj[a] = getattr(obj, a)

    if new_obj['created']:
        new_obj['created'] = new_obj['created'].isoformat()

    return new_obj


# convert to obj and then pretty print
def sqla_to_json(obj, expunge=None, include_attrs=None):
    if expunge is None:
        expunge = []

    return json.dumps(sqla_to_dict(obj, expunge, include_attrs), sort_keys=True, indent=4, separators=(',', ': '))


# just a pretty print function
def pretty_json(obj):
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

def anonymize_dict(obj):
    for o in obj:
        if o['anonymous'] == True:
            o['author'] = 'Anonymous'
            o['author_id'] = 0
    return o
