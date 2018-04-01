#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import hashlib
import random
import os.path
import json
import time
import datetime
import re
from tornado.options import define, options

from conf import conf
from cache import cache
from alimsg import sndmsg

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
                if len(carr) != 2:
                    r = {'code': -2, 'data': {}, 'msg': 'cookie is invalid'}
                    r = json.dumps(r)
                    self.write(r)
                else:
                    [user, uid] = carr
                    url = 'http://%s:%s/ctx' % (conf.dbserver_ip, conf.dbserver_port)
                    headers = self.request.headers
                    http_client = tornado.httpclient.AsyncHTTPClient()
                    body = 'uid=%s' % uid
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
        mobile = self.get_argument('mobile', None)
        password = self.get_argument('password', None)
        if not mobile or not password:
            r = {'code': -1}
            r = json.dumps(r)
            self.write(r)
            self.finish()
        else:
            r = self.__query_cache(mobile, password)
            if r:
                d = {'code':0, 'msg':'ok', 'data': r}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/login' % (conf.dbserver_ip, conf.dbserver_port)
                headers = self.request.headers
                http_client = tornado.httpclient.AsyncHTTPClient()
                resp = yield tornado.gen.Task(
                        http_client.fetch,
                        url,
                        method="POST",
                        headers=headers,
                        body=self.request.body,
                        validate_cert=False)
                r = resp.body
                d = None
                try:
                    d = json.loads(r)
                except:
                    d = None
                self.__store_cache(d, mobile, password)
                if not d:
                    d = {'code': -1, 'msg':'dbserver returns None'}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                elif d.get('code', 0) != 0:
                    d = {'code': -1, 'msg':'dbserver returns code=-1'}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    data = d['data']
                    d = {'code':0, 'msg':'ok', 'data':data}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
    #store data in cache
    def __store_cache(self, r, mobile, password):
        if not r:
            return False
        code = r.get('code', -1)
        data = r.get('data')
        if code == 0 and data:
            key = 'user_tel_%s_%s' % (mobile, password)
            data = json.dumps(data)
            cache.set(key, data, conf.redis_timeout)
    #return dic
    def __query_cache(self, mobile, password):
        key = 'user_tel_%s_%s' % (mobile, password)
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
        if sex not in [1, 2] or limit < 1 or page < 1:
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
            if next_ == 0 and  val:
                cache.set(key, val, conf.redis_timeout)
                data = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data':data}
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

class PCDataImgHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        f   = self.get_argument('f',   None)
        s   = self.get_argument('s',   None)
        t   = self.get_argument('t',   None)
        k   = self.get_argument('k',   None)
        if not uid or not f or not s or not t or not k:
            d = {'code': -1, 'msg': '参数不正确'}
        else:
            url = 'http://%s:%s/img' % (conf.dbserver_ip, conf.dbserver_port)
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
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d:
                d = {'code': -1, 'msg': '服务器错误'}
            if d['code'] == 0:
                key = 'userid_%s' % uid
                cache.del_(key)
            d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataDelImgHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        src = self.get_argument('src', None)
        d = {'code': -2, 'msg': '参数不正确'}
        if not uid or not src:
            d = {'code': -2, 'msg': '参数不正确'}
        else:
            url = 'http://%s:%s/delimg' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'uid=%s&src=%s' % (uid, src)
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {'code': -3, 'msg': '服务器错误'}
            try:
                d = json.loads(r)
            except:
                d = {'code': -3, 'msg': '服务器错误'}
            if d['code'] == 0:
                key = 'userid_%s' % uid
                val = cache.get(key)
                if val:
                    v = json.loads(val)
                    t_src = '%s/%s/%s' % (conf.pic_ip, src, conf.postfix)
                    for i in xrange(len(v['pic']['arr'])):
                        if v['pic']['arr'][i] == t_src:
                            j = i
                            while j+1 < len(v['pic']['arr']):
                                v['pic']['arr'][j] = v['pic']['arr'][j+1]
                                j = j+1
                            break
                    v['pic']['count'] = v['pic']['count'] + 1
                    v = json.dumps(v)
                    cache.set(key, v, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()
                
            

class PCDataVerifyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        p = '^(1[356789])[0-9]{9}$'
        mobile = self.get_argument('mobile', None)
        ip     = self.get_argument('ip', None)
        if not mobile or not re.match(p, mobile) or not ip:
            d = {'code': -1, 'msg': '电话号码不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/verify' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'mobile=%s' % mobile
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d:
                d = {'code': -1, 'msg': '服务器错误'}
            elif d['code'] < 0:
                r = {'code': -2,'msg':d['msg']}
                r = json.dumps(r)
                self.write(r)
                self.finish()
            else:
                t = int(time.time())
                print(mobile, ip)
                mkey_n = 'verify_%s'%mobile
                mv_n   = cache.get(mkey_n)
                mkey_i = 'verify_%s'%ip
                mv_i   = cache.get(mkey_i)
                if mv_n or mv_i:
                    d = {'code': -1, 'msg': '不要频繁发送验证码'}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    cache.set(mkey_n, mv_n, 60)
                    cache.set(mkey_i, mv_i, 60)
                    a = random.randrange(0,10)
                    b = random.randrange(0,10)
                    c = random.randrange(0,10)
                    d = random.randrange(0,10)
                    code = '%d%d%d%d' % (a,b,c,d)
                    r = sndmsg(mobile, code)
                    print(r)
                    if not r:
                        d = {'code':-1, 'msg':'获取验证码失败,可能手机号不正确'}
                        d = json.dumps(d)
                        self.write(d)
                        self.finish()
                    else:
                        sec = 'jly'
                        m = '%s%d%s'%(code, t, sec)
                        m2 = hashlib.md5()
                        m2.update(m)
                        token = m2.hexdigest()
                        d = {'code':0, 'msg':'验证码已发送', 'time':t, 'token':token}
                        d = json.dumps(d)
                        self.write(d)
                        self.finish()

class PCDataVerifyMobileHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        mobile  = self.get_argument('mobile', None)
        uid     = self.get_argument('uid',    None)
        d = {}
        p = '^(1[356789])[0-9]{9}$'
        if not uid or not mobile or not re.match(p, mobile):
            d = {'code': -1, 'msg': 'parameter invalid'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/verify_mobile' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'mobile=%s&uid=%s' % (mobile, uid)
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d or d.get('code', -1) != 0:
                d = {'code': -1, 'msg': d.get('msg', 'parameter invalid')}
                d = json.dumps(d)
            else:
                d = {'code': 0, 'msg':'ok', 'data':d['data']}
                d = json.dumps(d)
            self.write(d)
            self.finish()

class PCDataFindVerifyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        p = '^(1[356789])[0-9]{9}$'
        mobile = self.get_argument('mobile', None)
        ip     = self.get_argument('ip', None)
        if not mobile or not re.match(p, mobile) or not ip:
            d = {'code': -1, 'msg': '电话号码不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/find_verify' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'mobile=%s' % mobile
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d:
                d = {'code': -1, 'msg': '服务器错误'}
            elif d['code'] < 0:
                r = {'code': -2,'msg':d['msg']}
                r = json.dumps(r)
                self.write(r)
                self.finish()
            else:
                t = int(time.time())
                print(mobile, ip)
                mkey_n = 'verify_%s'%mobile
                mv_n   = cache.get(mkey_n)
                mkey_i = 'verify_%s'%ip
                mv_i   = cache.get(mkey_i)
                if mv_n or mv_i:
                    d = {'code': -1, 'msg': '不要频繁发送验证码'}
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    cache.set(mkey_n, mv_n, 60)
                    cache.set(mkey_i, mv_i, 60)
                    a = random.randrange(0,10)
                    b = random.randrange(0,10)
                    c = random.randrange(0,10)
                    d = random.randrange(0,10)
                    code = '%d%d%d%d' % (a,b,c,d)
                    r = sndmsg(mobile, code)
                    print(r)
                    if not r:
                        d = {'code':-1, 'msg':'获取验证码失败,可能手机号不正确'}
                        d = json.dumps(d)
                        self.write(d)
                        self.finish()
                    else:
                        sec = 'jly'
                        m = '%s%d%s'%(code, t, sec)
                        m2 = hashlib.md5()
                        m2.update(m)
                        token = m2.hexdigest()
                        d = {'code':0, 'msg':'ok', 'time':t, 'token':token}
                        d = json.dumps(d)
                        self.write(d)
                        self.finish()

class PCDataFindPasswordHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        mobile = self.get_argument('mobile', None)
        passwd = self.get_argument('password', None)
        d = {}
        if not mobile or not passwd:
            d = {'code': -6, 'msg': '手机号码和密码不能为空'}
        else:
            url = 'http://%s:%s/find_password' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'mobile=%s&password=%s' % (mobile, passwd)
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            D = {}
            try:
                D = json.loads(r)
            except:
                D = {}
            if not D:
                d = {'code': -5, 'msg': '系统错误'}
            else:
                d = D
                if D['code'] == 0:
                    c = D['data']
                    k = 'userid_%s' % str(c['user']['id'])
                    v = json.dumps(c)
                    cache.set(k, v, conf.redis_timeout)
                    del D['data']
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataRegistHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        mobile   = self.get_argument('mobile', None)
        passwd   = self.get_argument('password', None)
        sex      = int(self.get_argument('sex', 0))
        p = '^(1[356789])[0-9]{9}$'
        if not mobile or not re.match(p, mobile) or not passwd or sex not in [1,2]:
            d = {'code':-1, 'msg':'parameters error'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/regist' % (conf.dbserver_ip, conf.dbserver_port)
            headers = self.request.headers
            body = 'mobile=%s&password=%s&sex=%d' % (mobile, passwd, sex)
            http_client = tornado.httpclient.AsyncHTTPClient()
            resp = yield tornado.gen.Task(
                    http_client.fetch,
                    url,
                    method="POST",
                    headers=headers,
                    body=body,
                    validate_cert=False)
            r = resp.body
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d:
                d = {'code':-1, 'msg':'服务器错误'}
            if d['code'] == 0:#新注册用户写入cache
                c = d['data']
                k = 'userid_%s' % str(c['user']['id'])
                v = json.dumps(c)
                cache.set(k, v, conf.redis_timeout)
                k = 'user_new_male' if sex == 1 else 'user_new_female'
                v = cache.get(k)
                if v:
                    v = json.loads(v)
                    v.insert(0, c)
                    v = json.dumps(v)
                    cache.set(k, v, conf.redis_timeout)
                k = 'user_index_find'
                v = cache.get(k)
                if v:
                    v = json.loads(v)
                    v.insert(0, c)
                    v = json.dumps(v)
                    cache.set(k, v, conf.redis_timeout)
            r = json.dumps(d)
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
            key = 'userid_%d' % u['id']
            data = json.dumps(data)
            cache.set(key, data, conf.redis_timeout)
            
            key = 'user_new_male' if u['sex'] == 1 else 'user_new_female'
            val = cache.get(key)
            if val:
                tmp = json.loads(val)
                f = 0
                for i in xrange(len(tmp)):
                    if tmp[i]['user']['id'] == u['id']:
                        tmp[i]['user'] = u
                        f = 1
                        break
                if f:
                    v = json.dumps(tmp)
                    cache.set(key, v, conf.redis_timeout)
            key = 'user_index_find'
            val = cache.get(key)
            if val:
                tmp = json.loads(val)
                f = 0
                for i in xrange(len(tmp)):
                    if tmp[i]['user']['id'] == u['id']:
                        tmp[i]['user'] = u
                        f = 1
                        break
                if f:
                    v = json.dumps(tmp)
                    cache.set(key, v, conf.redis_timeout)
            del d['data']
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
            key = 'userid_%d' % u['id']
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
        salary = self.get_argument('salary', None)
        work   = self.get_argument('work', None)
        car    = self.get_argument('car', None)
        house  = self.get_argument('hourse', None)
        if not ctx:
            d = {'code': -1, 'msg': 'invalid'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        elif not salary and not work and not car and not house:
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
                key = 'userid_%d' % u['id']
                data = json.dumps(data)
                cache.set(key, data, conf.redis_timeout)
                del d['data']
            d = json.dumps(d)
            self.write(d)
            self.finish()
class PCDataSeeOtherHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        kind = int(self.get_argument('kind', 0))
        uid  = self.get_argument('uid', None)
        cuid = self.get_argument('cuid', None)
        d = {'code': -1, 'msg': '参数错误'}
        if kind not in [1,2,3,4] or not uid or not cuid:
            d = {'code': -1, 'msg': '参数错误'}
        else:
            key = 'seeother_%s_%s_%s' % (cuid, uid, kind)
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                d = {'code': 0, 'msg': 'ok', 'data':val}
            else:
                url = 'http://%s:%s/seeother' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {}
                try:
                    d = json.loads(r)
                except:
                    d = {}
                if not d:
                    d = {'code': -2, 'msg': '服务器错误'}
                if d['code'] == 0:
                    data = d['data']
                    ac = data['account']
                    cookie = 'userid_%s' % cuid
                    cv = cache.get(cookie)
                    if cv:
                        cvd = json.loads(cv)
                        cvd['account'] = ac
                        cvd = json.dumps(cvd)
                        cache.set(cookie, cvd, conf.redis_timeout)
                    data = json.dumps(data)
                    conn = data['conn']
                    cache.set(key, conn, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataVerifyOtherHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        kind  = self.get_argument('kind', None)
        ctx   = self.get_argument('ctx', None)
        num   = self.get_argument('num', None)
        d = {}
        if not ctx or not kind or not num:
            d = {'code': -1, 'msg': '参数错误'}
        else:
            key = 'kind_%s_%s' % (kind, num)
            val = cache.get(key)
            if val:
                d = {'code': -1, 'msg': '30秒之后再发'}
                d = json.dumps(d)
            else:
                cache.set(key, 1, 30)
                url = 'http://%s:%s/verify_other' % (conf.dbserver_ip, conf.dbserver_port)
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
                    key = 'userid_%d' % u['id']
                    data = json.dumps(data)
                    cache.set(key, data, conf.redis_timeout)
                    del d['data']
                d = json.dumps(d)
        self.write(d)
        self.finish()
class PCDataPublicHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        ctx     = self.get_argument('ctx', None)
        kind    = self.get_argument('kind', None)
        action  = self.get_argument('action', None)
        if not ctx or  not kind or not action:
            d = {'code': -1, 'msg': '参数不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/public' % (conf.dbserver_ip, conf.dbserver_port)
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
            d = {'code': -1, 'msg': '参数不正确'}
            try:
                d = json.loads(r)
            except:
                d = {'code': -3, 'msg': '服务器错误'}
            if d.get('code', -1) == 0:
                data = d['data']
                print(data['otherinfo']['public_m'])
                u = data['user']
                key = 'userid_%d' % u['id']
                data = json.dumps(data)
                cache.set(key, data, conf.redis_timeout)
                del d['data']
            d = json.dumps(d)
            self.write(d)
            self.finish()
            
class PCDataISeeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        d = {'code': -1, 'msg':'参数不正确'}
        if uid:
            key = 'isee_%s' % uid
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data':v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/isee' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {'code': -1, 'msg': '参数不正确'}
                try:
                    d = json.loads(r)
                except:
                    d = {'code': -3, 'msg': '服务器错误'}
                if d.get('code', -1) == 0:
                    data = d['data']
                    val = json.dumps(data)
                    key = 'isee_%s' % uid
                    cache.set(key, val, conf.redis_timeout)
                    d = json.dumps(d)
                else:
                    d = json.dumps(d)
                self.write(d)
                self.finish()
        else:
            d = json.dumps(d)
            self.write(d)
            self.finish()

class PCDataSeeMeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        d = {'code': -1, 'msg':'参数不正确'}
        if uid:
            key = 'seeme_%s' % uid
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data': v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/seeme' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {'code': -1, 'msg': '参数不正确'}
                try:
                    d = json.loads(r)
                except:
                    d = {'code': -3, 'msg': '服务器错误'}
                if d.get('code', -1) == 0:
                    data = d['data']
                    val = json.dumps(data)
                    key = 'seeme_%s' % uid
                    cache.set(key, val, conf.redis_timeout)
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
        else:
            d = json.dumps(d)
            self.write(d)

class PCDataICareHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        d = {'code': -1, 'msg':'参数不正确'}
        if uid:
            key = 'icare_%s' % uid
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data': v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/icare' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {'code': -1, 'msg': '参数不正确'}
                try:
                    d = json.loads(r)
                except:
                    d = {'code': -3, 'msg': '服务器错误'}
                if d.get('code', -1) == 0:
                    data = d['data']
                    val = json.dumps(data)
                    key = 'icare_%s' % uid
                    cache.set(key, val, conf.redis_timeout)
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
                else:
                    d = json.dumps(d)
                    self.write(d)
                    self.finish()
        else:
            d = json.dumps(d)
            self.write(d)

class PCDataEmailHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        page = self.get_argument('page', None)
        next_ = self.get_argument('next', None)
        d = {}
        if not uid or not page or not next_:
            d = {'code': 0, 'msg': '参数不正确'}
        else:
            key = 'email_list_%s_%s_%s' % (uid, page, next_)
            val = cache.get(key)
            if val:
                v = json.loads(val)
                d = {'code': 0, 'msg': 'ok', 'data': v}
                cache.set(key, val, conf.redis_timeout)
            else:
                url = 'http://%s:%s/mail' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {}
                try:
                    d = json.loads(r)
                except:
                    d = {}
                if not d:
                    d = {'code': -1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    data = d['data']
                    v = json.dumps(data)
                    cache.set(key, v, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataLatestConnHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(sefl):
        uid = self.get_argument('uid', None)
        d = {}
        if not uid:
            d = {'code': -1, 'msg': '参数不正确'}
        else:
            key = 'latest_conn_%s' % uid
            val = cache.get(key)
            if val:
                v = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data': v}
                cache.set(key, val, conf.redis_timeout)
            else:
                url = 'http://%s:%s/latest_conn' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {}
                try:
                    d = json.loads(r)
                except:
                    d = {}
                if not d:
                    d = {'code': -1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    v = d['data']
                    v = json.dumps(v)
                    cache.set(key, v, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataSendEmailHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        cuid= self.get_argument('cuid', None)
        cnt = self.get_argument('content', None)
        d = {}
        if not uid or not cuid or not cnt:
            d = {'code': -1, 'msg': '参数不正确'}
        elif uid == cuid:
            d = {'code': -1, 'msg': '自己不用给自己发信'}
        else:
            url = 'http://%s:%s/sendemail' % (conf.dbserver_ip, conf.dbserver_port)
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
            d = {}
            try:
                d = json.loads(r)
            except:
                d = {}
            if not d:
                d = {'code': -1, 'msg': '服务器错误'}
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataYanyuanHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        cuid= self.get_argument('cuid', None)
        d = {}
        if not uid or not cuid:
            d = {'code': -1, 'msg': '参数不正确'}
        elif uid == cuid:
            d = {'code': -1, 'msg': '自己不用给自己发眼缘'}
        else:
            key = 'yanyuan_%s_%s' % (cuid, uid)
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                d = {'code': 0, 'msg': 'ok'}
            else:
                url = 'http://%s:%s/yanyuan' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {}
                try:
                    d = json.loads(r)
                except:
                    d = {}
                if not d:
                    d = {'code': -1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    cache.set(key, 1, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataYanyuanCheckHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid = self.get_argument('uid', None)
        cuid= self.get_argument('cuid', None)
        d = {}
        if not uid or not cuid:
            d = {'code': -1, 'msg': '参数不正确'}
        elif uid == cuid:
            d = {'code': -1, 'msg': '自己不用看自己的眼缘'}
        else:
            key = 'yanyuan_%s_%s' % (cuid, uid)
            val = cache.get(key)
            if val:
                d = {'code': 0, 'msg': 'ok', 'data':{'yanyuan': val}}
                cache.set(key, val, conf.redis_timeout)
            else:
                url = 'http://%s:%s/yanyuan_check' % (conf.dbserver_ip, conf.dbserver_port)
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
                d = {}
                try:
                    d = json.loads(r)
                except:
                    d = {}
                if not d:
                    d = {'code': -1, 'msg': '服务器错误'}
                if d['code'] == 0:
                   v = d['data']['yanyuan']
                   cache.set(key, v, conf.redis_timeout)
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataListDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        next_ = int(self.get_argument('next', 0))
        loc1  = self.get_argument('loc1', 'loc1')
        loc2  = self.get_argument('loc2', 'loc2')
        age1  = int(self.get_argument('age1', 18))
        age2  = int(self.get_argument('age2', 18))
        sex   = int(self.get_argument('sex', 3))
        key = 'date_%d_%s_%s_%d_%d_%d' % (next_, loc1, loc2, age1, age2, sex)
        val = cache.get(key)
        if val:
            cache.set(key, val, conf.redis_timeout)
            val = json.loads(val)
            d = {'code':0, 'msg':'ok', 'data': val}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/list_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
            d = {'code': -1, 'msg': '参数不正确'}
            try:
                d = json.loads(r)
            except:
                d = {'code': -1, 'msg': '服务器错误'}
            if d.get('code', -1) == 0:
                data = d['data']
                val = json.dumps(data)
                cache.set(key, val, conf.redis_timeout)
            self.write(r)
            self.finish()

class PCDataCreateDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        name       = self.get_argument('nick_name', None)
        uid        = self.get_argument('uid', None)
        age        = int(self.get_argument('age', 18))
        sex        = self.get_argument('sex', None)
        sjt        = self.get_argument('subject', None)
        dt         = int(self.get_argument('dtime', 1)) 
        loc1       = self.get_argument('loc1', '') 
        loc2       = self.get_argument('loc2', '') 
        locd       = self.get_argument('locd', None)
        obj        = self.get_argument('object', None)
        num        = self.get_argument('num', 1)
        fee        = self.get_argument('fee', 0)
        bc         = self.get_argument('bc', '') 
        vt         = self.get_argument('valid_time', 1)
        d = {'code': 0, 'msg': 'ok'}
        if not name or not uid or not sex or not sjt:
            d = {'code':-1, 'msg':'参数不正确'}
        if not loc1 and not loc2:
            d = {'code':-1, 'msg':'参数不正确'}
        if d['code'] == 0:
            url = 'http://%s:%s/create_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
            try:
                d = json.loads(r)
            except:
                d = {'code': -1, 'msg': '服务器错误'}
            if d['code'] == 0:
                cache.delpat('date_*')
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataRemoveDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid   = self.get_argument('uid', None)
        did   = self.get_argument('did', None)
        d = {'code': 0, 'msg': 'ok'}
        if not did or not uid:
            d = {'code':-1, 'msg':'参数不正确'}
        if d['code'] == 0:
            url = 'http://%s:%s/remove_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
            try:
                d = json.loads(r)
            except:
                d = {'code': -1, 'msg': '服务器错误'}
            if d['code'] == 0:
                cache.delpat('date_*')
        d = json.dumps(d)
        self.write(d)
        self.finish()

class PCDataParticipateDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid   = self.get_argument('uid', None)
        limit = int(self.get_argument('limit', 0))
        page  = int(self.get_argument('page', 0))
        next_ = int(self.get_argument('next', 0))
        if not uid:
            d = {'code': -1, 'msg': '参数不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            key = 'date_part_%s_%d_%d_%d' % (uid, limit, page, next_)
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg': 'ok', 'data': v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/participate_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
                try:
                    d = json.loads(r)
                except:
                    d = {'code':-1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    data = d['data']
                    v = json.dumps(data)
                    cache.set(key, v, conf.redis_timeout)
                d = json.dumps(d)
                self.write(d)
                self.finish()

class PCDataSponsorDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        uid   = self.get_argument('uid', None)
        limit = int(self.get_argument('limit', 0))
        page  = int(self.get_argument('page', 0))
        next_ = int(self.get_argument('next', 0))
        if not uid:
            d = {'code': -1, 'msg': '参数不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            key = 'date_sponsor_%s_%d_%d_%d' % (uid, limit, page, next_)
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg': 'ok', 'data': v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/sponsor_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
                try:
                    d = json.loads(r)
                except:
                    d = {'code':-1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    data = d['data']
                    v = json.dumps(data)
                    cache.set(key, v, conf.redis_timeout)
                d = json.dumps(d)
                self.write(d)
                self.finish()

class PCDataDetailDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        did   = self.get_argument('did', None)
        d = {}
        if not did:
            d = {'code': -1, 'msg': '参数不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            key = 'date_detail_%s'% did
            val = cache.get(key)
            if val:
                cache.set(key, val, conf.redis_timeout)
                v = json.loads(val)
                d = {'code': 0, 'msg':'ok', 'data': v}
                d = json.dumps(d)
                self.write(d)
                self.finish()
            else:
                url = 'http://%s:%s/detail_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
                try:
                    d = json.loads(r)
                except:
                    d = {'code':-1, 'msg': '服务器错误'}
                if d['code'] == 0:
                    data = d['data']
                    v = json.dumps(data)
                    cache.set(key, v, conf.redis_timeout)
                d = json.dumps(d)
                self.write(d)
                self.finish()

class PCDataBaomingDatingHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        did   = self.get_argument('did', None)
        uid   = self.get_argument('uid', None)
        d = {}
        if not did:
            d = {'code': -1, 'msg': '参数不正确'}
            d = json.dumps(d)
            self.write(d)
            self.finish()
        else:
            url = 'http://%s:%s/baoming_dating' % (conf.dbserver_ip, conf.dbserver_port)
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
            try:
                d = json.loads(r)
            except:
                d = {'code':-1, 'msg': '服务器错误'}
            if d['code'] == 0:
                key = 'date_detail_%s' % did
                val = cache.get(key)
                if val:
                    v = json.loads(val)
                    v['baoming'].append(uid)
                    v = json.dumps(v)
                    cache.set(key, v, conf.redis_timeout)
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
               (r'/verify', PCDataVerifyHandler),
               (r'/verify_mobile', PCDataVerifyMobileHandler),
               (r'/find_verify', PCDataFindVerifyHandler),
               (r'/find_password', PCDataFindPasswordHandler),
               (r'/indexdata', PCIndexDataHandler),
               (r'/basic_edit', PCDataBasicEditHandler),
               (r'/statement_edit', PCDataStatementEditHandler),
               (r'/other_edit', PCDataOtherEditHandler),
               (r'/seeother', PCDataSeeOtherHandler),
               (r'/verify_other', PCDataVerifyOtherHandler),
               (r'/new', IndexNewHandler),
               (r'/find', FindHandler),
               (r'/img', PCDataImgHandler),
               (r'/delimg', PCDataDelImgHandler),
               (r'/public', PCDataPublicHandler),
               (r'/isee', PCDataISeeHandler),
               (r'/seeme', PCDataSeeMeHandler),
               (r'/icare', PCDataICareHandler),
               (r'/email', PCDataEmailHandler),
               (r'/latest_conn', PCDataLatestConnHandler),
               (r'/latest_conn', PCDataLatestConnHandler),
               (r'/sendemail', PCDataSendEmailHandler),
               (r'/yanyuan', PCDataYanyuanHandler),
               (r'/yanyuan_check', PCDataYanyuanCheckHandler),
               (r'/list_dating', PCDataListDatingHandler),
               (r'/create_dating', PCDataCreateDatingHandler),
               (r'/remove_dating', PCDataRemoveDatingHandler),
               (r'/participate_dating', PCDataParticipateDatingHandler),
               (r'/sponsor_dating', PCDataSponsorDatingHandler),
               (r'/detail_dating', PCDataDetailDatingHandler),
               (r'/baoming_dating',PCDataBaomingDatingHandler),
              ]
    application = tornado.web.Application(handler, **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
