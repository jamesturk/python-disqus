""" Python library for interacting with the Disqus API.
 
The Disqus API (http://wiki.disqus.net/API) allows for interaction with
the Disqus comment system.
"""

__author__ = "James Turk (james.p.turk@gmail.com)"
__version__ = "0.0.2"
__copyright__ = "Copyright (c) 2009 James Turk"
__license__ = "BSD"
 
import urllib, urllib2
import time
try:
    import json
except ImportError:
    import simplejson as json

api_url = 'http://disqus.com/api/%s/'

def deunicode(ad):
    return dict((str(k),v) for k,v in ad.iteritems())

class DisqusError(Exception):
    ''' base class for Disqus API errors '''

def apicall(method, params, http_method='GET'):
    params['api_version'] = 1.1
    params = urllib.urlencode(params)
    if http_method == 'GET':
        url = '?'.join((api_url % method, params))
        response = urllib2.urlopen(url).read()
    else:
        response = urllib2.urlopen(api_url % method, params).read()
    obj = json.loads(response)
    if not obj['succeeded']:
        raise DisqusError(obj['message'])
    return obj['message']

class Post(object):
    def __init__(self, d, user_api_key):
        for k,v in d.iteritems():
            setattr(self, k, v)
        self.user_api_key = user_api_key

    def moderate(self, action):
        params = {'user_api_key':self.user_api_key, 'post_id':self.id,
                  'action':action}
        apicall('moderate_post', params, 'POST')

class Thread(object):
    def __init__(self, d, user_api_key, forum_api_key):
        for k,v in d.iteritems():
            setattr(self, k, v)
        self.user_api_key = user_api_key
        self.forum_api_key = forum_api_key

    def get_posts(self, limit=25, start=0, filter=None, exclude=None):
        params = {'user_api_key':self.user_api_key, 'thread_id':self.id, 
                  'limit':limit, 'start':start}
        if filter:
            params['filter'] = filter
        if exclude:
            params['exclude'] = exclude
        return [Post(p, self.user_api_key) for p in apicall('get_thread_posts', params)]

    def update(self, title=None, slug=None, url=None, allow_comments=None):
        params = {'forum_api_key': self.forum_api_key, 'thread_id': self.id}
        if title:
            params['title'] = title
        if slug:
            params['slug'] = slug
        if url:
            params['url'] = url
        if allow_comments is not None:
            params['allow_comments'] = allow_comments
        return apicall('update_thread', params, 'POST')

    def create_post(self, message, author_name, author_email, parent_post=None,
                    created_at=None, author_url=None, ip_address=None, 
                    state=None):
        params = {'forum_api_key': self.forum_api_key, 'thread_id':self.id,
                  'message':message, 'author_name':author_name,
                  'author_email':author_email}
        if parent_post:
            params['parent_post'] = parent_post
        if created_at:
            if isinstance(created_at, time.struct_time):
                created_at = time.strftime('%Y-%m-%dT%H:%M', created_at)
            params['created_at'] = created_at
        if author_url:
            params['author_url'] = author_url
        if ip_address:
            params['ip_address'] = ip_address
        if state:
            params['state'] = state
        return apicall('create_post', params, 'POST')

class Forum(object):
    def __init__(self, forum_api_key=None, id=None, name=None, shortname=None,
                 created_at=None, description=None, user_api_key=None):
        self.__dict__['api_key'] = forum_api_key
        self.id = id
        self.name = name
        self.shortname = shortname
        self.created_at = created_at
        self.user_api_key = user_api_key

    @property
    def api_key(self):
        if not self.__dict__['api_key']:
            msg = apicall('get_forum_api_key', {'user_api_key':self.user_api_key,
                                                 'forum_id':self.id})
            self.__dict__['api_key'] = msg
        return self.__dict__['api_key']

    def get_posts(self, limit=25, start=0, filter=None, exclude=None):
        params = {'user_api_key':self.user_api_key, 'forum_id':self.id,
                  'limit':limit, 'start':start}
        if filter:
            params['filter'] = filter
        if exclude:
            params['exclude'] = exclude
        return [Post(p, self.user_api_key) for p in apicall('get_forum_posts', params)]

    def get_threads(self):
        msg = apicall('get_thread_list', {'user_api_key':self.user_api_key, 'forum_id':self.id})
        return [Thread(t, self.user_api_key, self.api_key) for t in msg]

    def get_num_posts(self, *thread_ids):
        params = {'user_api_key': self.user_api_key, 'thread_ids': ','.join(thread_ids)}
        return apicall('get_num_posts', params)

    def get_updated_threads(self, since):
        params = {'user_api_key': self.user_api_key, 'forum_id': self.id, 'since':since}
        return apicall('get_updated_threads', params)

    def get_thread_by_url(self, url):
        msg = apicall('get_thread_by_url', {'forum_api_key': self.api_key, 'url': url})
        if msg:
            return Thread(msg, self.user_api_key, self.api_key)

    def thread_by_identifier(self, title, identifier):
        msg = apicall('thread_by_identifier', {'forum_api_key': self.api_key, 'title': title, 'identifier': identifier}, 'POST')
        return Thread(msg['thread'], self.user_api_key, self.api_key), msg['created']

def get_user_name(user_api_key):
    return apicall('get_user_name', {'user_api_key':user_api_key}, 'POST')

def get_forums(user_api_key):
    msg = apicall('get_forum_list', {'user_api_key':user_api_key})
    return [Forum(user_api_key=user_api_key, **deunicode(f)) for f in msg]
