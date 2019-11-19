import requests
from bot import Api
import praw
import random
import json
from bot_config import *
import os.path
from os import path
import time

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

def get_top_reddit_post(sub=None):
    global reddit_posts
    global reddit

    if sub is None:
        sub = random.choice(bot_subreddits)

    sub_posts = reddit.subreddit(sub).top('all')
    posts = []
    for p in sub_posts:
        if str(p) not in reddit_posts['posts'] and p.selftext == '':
            posts.append(p)


    post = random.choice(posts)

    return post


def main():
    global reddit
    global reddit_posts

    ruser, rkey = reddit_api.split(':')
    reddit = praw.Reddit(client_id=ruser, client_secret=rkey, user_agent='Greetings from ieddit.')

    if path.exists('posts.json') is False:
        reddit_posts = {'posts':[], 'comments':[]}
        with open('posts.json', 'w') as p:
            p.write(json.dumps(reddit_posts))

    with open('posts.json', 'r') as p:
        reddit_posts = json.loads(p.read())

    while True:
        bot = choose_bot()
        post = get_top_reddit_post()

        bot.create_post(sub=post.subreddit, title=post.title, url=post.url)
        new_reddit('posts', str(post.id))

        time.sleep(bot_interval)

if __name__ == '__main__':
    main()