"""
Example bot for interracting with the api
"""
import requests

class Api:
    def __init__(self, username=None, key=None, site_url='https://ieddit.com'):
        if username is None or key  is None:
            raise ValueError('empty username or key')
        self.username = username
        self.key = key
        self.site_url = site_url
        self.headers = {'ieddit-username':username, 'ieddit-api-key':key}

    def create_post(self, sub='', url='', self_text='', title=''):
        """
        creates a new post on ieddit, need url/self_text, title, and sub
        """
        r = requests.post(self.site_url + '/api/new_post', headers=self.headers, 
            data={'url':url, 'self_post_text':self_text, 'title':title, 'sub':sub})

        return r.text

    def create_comment(self, parent_type=None, parent_id=None, text=None, override=None, anonymous=None):
        """
        replies to a post/comment
        """
        r = requests.post(self.site_url + '/api/new_comment', headers=self.headers,
            data={'parent_id':parent_id, 'parent_type':parent_type, 'text':text, 'override':override, 'anonymous':anonymous})
        
        return r.text

def main():
    bot = Api(username='bot', key='L7sUR2uBtfLFvERQHoJ3bmQP03HcoR')
    #bot.create_post(sub='bot', url='https://google.com', title='this was created by a bot')
    #bot.create_comment(parent_type='comment', parent_id=1, text='reply to comment 1')
    #bot.create_comment(parent_type='post', parent_id=1, text='reply to post 1')

if __name__ == '__main__':
    main()
