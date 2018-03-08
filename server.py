#-*- coding: utf-8 -*-
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import hashlib
import os.path
import json
import time
import datetime
import re
from tornado.options import define, options

from conf import conf
from cache import cache

define("port", default=conf.sys_port, help="run on the given port", type=int)


class PCDataCtxHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        cookie = self.get_argument('cookie', None)
        if not cookie:
            r = {'code': -1, 'data': {}, 'msg': 'cookie is null'}
            r = json.dumps(r)
            self.write(r)
        else:
            val = cache.get(cookie)
            if val:
                cache.set(cookie, val, conf.redis_timeout)
                v = {}
                try:
                    v = json.loads(val)
                except:
                    v = {}
                r = {'code': 0, 'data': v, 'msg': 'ok'}
                r = json.dumps(r)
                self.write(r)
            else:
                carr = cookie.split('_')
                if len(carr) != 3:
                    r = {'code': -2, 'data': {}, 'msg': 'cookie is invalid'}
                    r = json.dumps(r)
                    self.write(r)
                else:
                    [user, name, password] = carr
                    url = 'http://%s:%s/ctx' % (conf.dbserver_ip, conf.dbserver_port)
                    headers = self.request.headers
                    http_client = tornado.httpclient.AsyncHTTPClient()
                    body = 'username=%s&password=%s' % (name, password)
                    resp = yield tornado.gen.Task(
                            http_client.fetch,
                            url,
                            method="POST",
                            headers=headers,
                            body=body,
                            validate_cert=False)
                    b = resp.body
                    d = err = {'code': -4, 'data': {}, 'msg': 'dbsever inner error'}
                    try:
                        d = json.loads(b)
                    except:
                        d = err
                    r = json.dumps(d)
                    if d.get('code', -1) == 0:
                        v = d.get('data', {})
                        v = json.dumps(v)
                        cache.set(cookie, v, conf.redis_timeout)
                    self.write(r)
        self.finish()
#username, passwd
class PCDataLoginHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        name     = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if not name or not password:
            r = {'code': -1, 'msg': 'username or password is null'}
            r = json.dumps(r)
            self.write(r)
            self.finish()
        else:
            r = self.__query_cache(name, password)
            if r:
                d = {'code':0, 'msg':'ok', 'data': r}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/login' % (conf.dbserver_ip, conf.dbserver_port)
                headers = self.request.headers
                http_client = tornado.httpclient.AsyncHTTPClient()
                body = 'username=%s&password=%s' % (name, password)
                resp = yield tornado.gen.Task(
                        http_client.fetch,
                        url,
                        method="POST",
                        headers=headers,
                        body=body,
                        validate_cert=False)
                r = resp.body
                d = None
                try:
                    d = json.loads(r)
                except:
                    d = None
                self.__store_cache(d, name, password)
                if not d:
                    d = {'code': -1, 'msg':'inner error', 'data':{}}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                elif d.get('code', -1) == -1:
                    d = {'code': -1, 'msg':'用户名或密码错误', 'data':{}}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    self.write(r)
                    self.finish()
    #store data in cache
    def __store_cache(self, r, name, password):
        if not r:
            return False
        code = r.get('code', -1)
        data = r.get('data')
        if code == 0 and data:
            key = 'user_%s_%s' % (name, password)
            data = json.dumps(data)
            cache.set(key, data, conf.redis_timeout)
    #return dic
    def __query_cache(self, name, password):
        key = 'user_%s_%s' % (name, password)
        val = cache.get(key)
        d   = None
        if val:
            try:
                d = json.loads(val)
            except:
                d = None
            if d:
                cache.set(key, val, conf.redis_timeout)
        return d

class PCIndexDataHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        url = 'http://%s:%s/indexdata' % (conf.dbserver_ip, conf.dbserver_port)
        headers = self.request.headers
        http_client = tornado.httpclient.AsyncHTTPClient()
        body = 'a=1'
        resp = yield tornado.gen.Task(
                http_client.fetch,
                url,
                method="POST",
                headers=headers,
                body=body,
                validate_cert=False)
        r = resp.body
        self.write(r)
        self.finish()
class IndexNewHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        sex   = int(self.get_argument('sex', 0))
        limit = int(self.get_argument('limit', 0))
        page  = int(self.get_argument('page',  0))
        next_ = int(self.get_argument('next',  0))
        if sex not in [1, 2] or limit < 1 or page < 1 or next_ != 0:
            d = {'code':-1, 'msg':'error', 'data':{}}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            if sex == 1:
                key = 'user_new_male'
            else:
                key = 'user_new_female'
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                data = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data':data}
                print('sex=%d'%sex)
                print(d)
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/new' % (conf.dbserver_ip, conf.dbserver_port)
                headers = self.request.headers
                body = 'sex=%d&limit=%d&page=%d&next=%d'%(sex,limit, page, next_)
                http_client = tornado.httpclient.AsyncHTTPClient()
                resp = yield tornado.gen.Task(
                        http_client.fetch,
                        url,
                        method="POST",
                        headers=headers,
                        body=body,
                        validate_cert=False)
                d = None
                try:
                    d = json.loads(resp.body)
                except:
                    d = None
                print('sex=%d'%sex)
                print(d)
                r = None
                if not d or d.get('code', -1) < 0:
                    r = {'code': -1, 'msg':'failed', 'data':{}}
                else:
                    r = {'code': 0, 'msg': 'ok', 'data':d['data']}
                    self.__store_cache(d, sex)
                r = json.dumps(r)
                self.write(r)
                self.finish()
    def __store_cache(self, d, sex):
        if d['code'] == 0 and d.get('data'):
            key = 'user_new_male' if sex == 1 else 'user_new_female'
            val = d['data']
            val = json.dumps(val)
            cache.set(key, val, conf.redis_timeout)
class FindHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        sex          = int(self.get_argument('sex',     -1))
        agemin       = int(self.get_argument('agemin',  -1))
        agemax       = int(self.get_argument('agemax',  -1))
        cur1         = self.get_argument('cur1',    None)
        cur2         = self.get_argument('cur2',    None)
        ori1         = self.get_argument('ori1',    None)
        ori2         = self.get_argument('ori2',    None)
        degree       = int(self.get_argument('degree', -1))
        salary       = int(self.get_argument('salary', -1))
        xz           = self.get_argument('xingzuo', None)
        sx           = self.get_argument('shengxiao', None)
        limit        = int(self.get_argument('limit', -1))
        page         = int(self.get_argument('page', -1))
        next_        = int(self.get_argument('next', -1))
        key          = 'user_index_find'
        val          = cache.get(key)
        if agemin > agemax:
            agemin, agemax = agemax, agemin
        if sex < 0 and agemin < 0 and agemax < 0 and not cur1 and not cur2 and not ori1 and not ori2 and degree < 0 and salary < 0 and not xz and not sx and limit < 0 and page < 0 and next_ < 0 and val:
            cache.set(key, val, conf.redis_timeout)
            d = json.loads(val)
            data = {'code':0, 'msg':'ok', 'data':d}
            data = json.dumps(data)
            self.write(data)
            self.finish()
        else:
            url = 'http://%s:%s/find' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = self.request.body
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            d = None
            try:
                d = json.loads(resp.body)
            except:
                d = None
            if not d or d.get('code', -1) != 0 or not d.get('data'):
                d = {'code':-1, 'msg':'error', 'data':{}}
                d = json.dumps(d)
                self.write(d)
                self.finish(d)
            else:
                if sex < 0 and agemin < 0 and agemax < 0 and not cur1 and not cur2 and not ori1 and not ori2 and degree < 0 and salary < 0 and not xz and not sx and limit < 0 and page < 0 and next_ < 0:
                    v = d['data']
                    v = json.dumps(v)
                    k = 'user_index_find'
                    cache.set(k, v, conf.redis_timeout)
                d = {'code':0, 'msg':'ok', 'count':d.get('count', 0),
                     'data':d['data']}
                d = json.dumps(d)
                self.write(d)
                self.finish()

class PCDataRegistHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        name    = self.get_argument('username', None)
        passwd   = self.get_argument('password', None)
        if not name or not passwd:
            self.write('-1')
            self.finish()
        else:
            url = 'http://%s:%s/regist' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'username=%s&password=%s' % (name, passwd)
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            self.write(r)
            self.finish()
class PCDataBasicEditHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        url = 'http://%s:%s/basic_edit' % (conf.dbserver_ip, conf.dbserver_port)
        headers = self.request.headers
        body = self.request.body
        http_client = tornado.httpclient.AsyncHTTPClient()
        resp = yield tornado.gen.Task(
                http_client.fetch,
                url,
                method="POST",
                headers=headers,
                body=body,
                validate_cert=False)
        r = resp.body
        d = {'code':-2, 'msg':'error'}
        try:
            d = json.loads(r)
        except:
            d = {'code':-2, 'msg':'error'}
        if d.get('code', -1) == 0:
            data = d['data']
            u = data['user']
            key = 'user_%s_%s' % (u['nick_name'], u['password'])
            data = json.dumps(data)
            cache.set(key, data, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataStatementEditHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        url = 'http://%s:%s/statement_edit' % (conf.dbserver_ip, conf.dbserver_port)
        headers = self.request.headers
        body = self.request.body
        http_client = tornado.httpclient.AsyncHTTPClient()
        resp = yield tornado.gen.Task(
                http_client.fetch,
                url,
                method="POST",
                headers=headers,
                body=body,
                validate_cert=False)
        r = resp.body
        d = {'code': -1, 'msg': 'error'}
        try:
            d = json.loads(r)
        except:
            d = {'code': -1, 'msg': 'error'}
        if d.get('code', -1) == 0:
            data = d['data']
            u = data['user']
            key = 'user_%s_%s' % (u['nick_name'], u['password'])
            data = json.dumps(data)
            cache.set(key, data, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataOtherEditHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        ctx = self.get_argument('ctx', None)
        mo  = self.get_argument('mobile', None)
        wx  = self.get_argument('wx', None)
        qq  = self.get_argument('qq', None)
        em  = self.get_argument('email', None)
        if not ctx:
            d = {'code': -1, 'msg': 'invalid'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        elif not mo and not wx and not qq and not em:
            d = {'code': -1, 'msg': 'failed'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/other_edit' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = self.request.body
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {'code': -1, 'msg': 'error'}
            try:
                d = json.loads(r)
            except:
                d = {'code': -1, 'msg': 'error'}
            if d.get('code', -1) == 0:
                data = d['data']
                u = data['user']
                key = 'user_%s_%s' % (u['nick_name'], u['password'])
                data = json.dumps(data)
                cache.set(key, data, conf.redis_timeout)
                del d['data']
            d = json.dumps(d)
            self.write(d)
            self.finish()

class PCDataPublishHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        ctx     = self.get_argument('ctx', None)
        kind    = self.get_argument('kind', None)
        action  = self.get_argument('action', None)
        if not ctx or  not kind or not action:
            d = {'code': -1, 'msg': 'invalid'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/publish' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = self.request.body
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {'code': -1, 'msg': 'error'}
            try:
                d = json.loads(r)
            except:
                d = {'code': -1, 'msg': 'error'}
            if d.get('code', -1) == 0:
                data = d['data']
                print(data['otherinfo']['public_m'])
                u = data['user']
                data = d['data']
                u = data['user']
                key = 'user_%s_%s' % (u['nick_name'], u['password'])
                data = json.dumps(data)
                cache.set(key, data, conf.redis_timeout)
                del d['data']
            d = json.dumps(d)
            self.write(d)
            self.finish()
            

if __name__ == "__main__":
    tornado.options.parse_command_line()
    settings = {
        "cookie_secret": "Tq2!c2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
        "xsrf_cookies": False,
        "debug":True}
    handler = [
               (r'/ctx', PCDataCtxHandler),
               (r'/login', PCDataLoginHandler),
               (r'/regist', PCDataRegistHandler),
               (r'/indexdata', PCIndexDataHandler),
               (r'/basic_edit', PCDataBasicEditHandler),
               (r'/statement_edit', PCDataStatementEditHandler),
               (r'/other_edit', PCDataOtherEditHandler),
               (r'/new', IndexNewHandler),
               (r'/find', FindHandler),
              #(r'/publish', PCDataPublishHandler),
              ]
    application = tornado.web.Application(handler, **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()