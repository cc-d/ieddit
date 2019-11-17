"""
the bot that posts to /i/changelog
"""
from bot import Api
import requests
import json
import os.path
import time
from datetime import datetime


bot = None

def get_new_commits():
    global bot
    with open('commits.txt', 'r') as c:
        commit_urls = c.read().splitlines()

    r = requests.get('https://api.github.com/repos/civicsoft/ieddit/commits')
    

    try:
        sleep_for = int(r.headers['X-RateLimit-Reset']) - int(datetime.utcnow().strftime('%s'))
        print('bot is rate limited. sleeping for', sleep_for)
        return False
    except Exception as e:
        pass


    commits_json = json.loads(r.text)

    for commit in commits_json:
        if commit['html_url'] not in commit_urls:
            bot.create_post(sub='changelog', url=commit['html_url'],
                title='%s: %s' % (commit['author']['login'], commit['commit']['message']))

            with open('commits.txt', 'a+') as c:
                c.write(commit['html_url'] + '\n')


def populate_commit_list():
    r = requests.get('https://api.github.com/repos/civicsoft/ieddit/commits')
    commits_json = json.loads(r.text)

    with open('commits.txt', 'w') as c:
        for commit in commits_json:
            c.write(commit['html_url'] + '\n')

    return True

def main():
    global bot
    if os.path.exists('commits.txt') is False:
        populate_commit_list()

    with open('commits.txt', 'r') as c:
        commit_urls = c.read().splitlines()

    with open('bot.config', 'r') as b:
        clines = b.read().splitlines()
    bot = Api(username=clines[0], key=clines[1])


    while True:
        get_new_commits()
        time.sleep(600)

if __name__ == '__main__':
    main()
