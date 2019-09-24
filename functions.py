from flask import Flask, render_template, session, request, redirect, flash, url_for, Blueprint, g

import urllib.parse
import random
import json
import re
import jinja2
import html
import config

from datetime import datetime, timedelta
legal_chars = '01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'

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
	url = urllib.parse.quote(url)[:40]
	return url

def post_url_parse(url):
	return urllib.parse.urlparse(url).netloc

def time_ago(dt):
	diff = datetime.now() - dt
	if diff.seconds < 60:
		return str(int(diff.seconds)) + 's'#econds ago'
	if diff.seconds > 60 and diff.seconds < 3600:
		return str(int(diff.seconds / 60)) + 'm'#inutes ago'
	if diff.seconds > 3600 and diff.seconds < 86400:
		return str(int((diff.seconds / 60) / 60)) + 'h'#ours ago'
	return str(int(diff.days)) + 'd'#ays ago'

# horribly ineffecient function lol
# like no seriously, this is really, really bad
# it just seemed like an entertaining way to write it
# will change on release
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

def psuedo_markup(text):
	mstring = ''
	while True:
		r = re.findall('\[(.*?)\]\((https?\:\/.*?)\)', text)
		if len(r) < 1:
			mstring += html.escape(text)
			break
		else:
			ntext = split_link(r[0], text)
			mstring += html.escape(ntext[0])
			mstring += '<a href="' + html.escape(ntext[2]) + '">' + html.escape(ntext[1]) + '</a>'
			text = ntext[3]
	return mstring