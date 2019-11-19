import requests
from bot import Api
import praw
from praw.models import MoreComments
import random
import json
from bot_config import *
import os.path
from os import path
import time
import re

reddit_posts = None
reddit = None

def choose_bot(exclude=''):
    accounts = [a for a in ieddit_accounts if a.split(':')[0] != exclude]
    iuser, ikey = random.choice(accounts).split(':')
    bot = Api(username=iuser, key=ikey)    
    return bot

def new_reddit(rtype, rid):
    global reddit_posts
    reddit_posts[rtype].append(rid)
    with open('posts.json', 'w') as p:
        p.write(json.dumps(reddit_posts))
    return True

def get_alt_title(submission):
    """
    not even close to complete, just wanted the genral concept
    """
    from difflib import SequenceMatcher
    global reddit
    original_title = submission.title
    titles = {}
    dupes = submission.duplicates()
    for d in dupes:
        similarity = SequenceMatcher(None, original_title, d.title).ratio()
        if similarity < 0.6 and d.ups > 1000:
            titles[d.title] = d.ups

    alt_title, title_ups = None, 0
    for title in titles.keys():
        if titles[title] > title_ups:
            alt_title = title
            title_ups = titles[title]

    if alt_title is None:
        alt_title = submission.title
    
    alt_title = remove_substrings(alt_title)
    return alt_title

def get_top_reddit_post(sub=None):
    global reddit_posts
    global reddit

    if sub is None:
        sub = random.choice(bot_subreddits)

    sub_posts = reddit.subreddit(sub).top('all')
    posts = []
    for p in sub_posts:
        if p.title.find('/r/') != -1:
           continue
        if str(p.title).lower().find('net neutrality') != -1:
           continue
        if str(p) not in reddit_posts['posts'] and p.selftext == '':
            posts.append(p)


    post = random.choice(posts)

    return post

def remove_substrings(title):
    subs = ['\[\d+\s?x\s?\d+\]', '\[oc\]']
    for s in subs:
        title = re.sub(s, '', title, flags=re.IGNORECASE)
    return title


def main():
    global reddit
    global reddit_posts

    ruser, rkey = reddit_api.split(':')
    reddit = praw.Reddit(client_id=ruser, client_secret=rkey, user_agent='Greetings from ieddit.')
    submission = reddit.submission(id='9gzg8s')
    
    if path.exists('posts.json') is False:
        reddit_posts = {'posts':[], 'comments':[]}
        with open('posts.json', 'w') as p:
            p.write(json.dumps(reddit_posts))

    with open('posts.json', 'r') as p:
        reddit_posts = json.loads(p.read())

    while True:
        ran = random.randint(1,post_chance)
        print(ran)
        if create_new_posts:
            if ran == 1:
                bot = choose_bot()
                print(bot)
                post = get_top_reddit_post()
                alt_title = get_alt_title(post)

                if str(post.subreddit).lower() in aliases.keys():
                    print('found alias')
                    post.subreddit = aliases[str(post.subreddit).lower()]
                print('sub', post.subreddit, 'title', alt_title)
                post_json = bot.create_post(sub=post.subreddit, title=alt_title, url=post.url)
                new_reddit('posts', str(post.id))
                print(post_json)
                if create_new_comments:
                    ran = random.randint(1, comment_chance)
                    if ran == 1:
                        try:
                            ipost = json.loads(post_json)
                            post.comment_sort = 'top'
                            comments = post.comments.list()
                            ups, comment = 0, None
                            for c in comments:
                                if isinstance(c, MoreComments):
                                    continue
                                if c.parent_id[0:3] == 't3_':
                                   if c.ups > ups:
                                       ups = c.ups
                                       comment = c.body
                            
                            if comment != None:
                                print(bot.create_comment(parent_type='post', parent_id=ipost['id'], text=comment))

                        except Exception as e:
                            print(str(e))


        print('sleeping for', bot_interval)
        time.sleep(bot_interval)

if __name__ == '__main__':
    main()
