#-*- coding: utf-8 -*-

import redis
import json
from conf import conf

class Cache():
    def __init__(self):
        self.rds = redis.Redis(host=conf.redis_ip, port=conf.redis_port, db=conf.redis_db, password=conf.redis_password)
    def get(self, key):
        r   = self.rds.get(key)
        return r
    def set(self, key, val, t=conf.redis_timeout):
        r   = self.rds.set(key, val, t)
    def del_(self, key):
        r   = self.rds.delete(key)
    def hget(self, name, key):
        r   = self.rds.hget(name, key)
        return r
    def hset(self, name, key, val):
        r   = self.rds.hset(name, key, val)
        return r
    def flushall(self):
        r = self.rds.flushall()

cache = Cache()

if __name__ == '__main__':
    r = cache.flushall()
