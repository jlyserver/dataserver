#-*- coding: utf8 -*-

import time

from sqlalchemy import Column, String, Integer, Date, TIMESTAMP, create_engine
from sqlalchemy import Enum
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import sys
reload(sys)

from conf import conf

# 初始化数据库连接:
mysql_url = 'mysql+mysqlconnector://' + str(conf.mysql_user) + ':%s@%s:'%(conf.mysql_password, conf.mysql_host) + str(conf.mysql_port) + '/' + conf.mysql_db
engine = create_engine(mysql_url, encoding=conf.mysql_encode)
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = conf.table_user
    def __init__(self, id_=0, name='', password='', age=18, shuxiang='0',\
            xingzuo='0', height=158, weight=49, blood='0', location='',\
           jiguan='', gender='2', education='3', nation='1', marriage='0',\
           job='0', salary='0', wx='', wx_v='0', qq='', qq_v='0', mobile='',\
           mobile_v='0', email='', email_v='0',  aim='0',\
           hobby0=0, hobby1=0, hobby2=0, hobby3=0, hobby4=0, statement=''):
        self.id            = id_
        self.nick_name     = name
        self.password      = password
        self.age           = age
        self.shuxiang      = shuxiang
        self.xingzuo       = xingzuo
        self.height        = height
        self.weight        = weight
        self.blood         = blood
        self.location      = location
        self.jiguan        = jiguan
        self.gender        = gender
        self.education     = education
        self.nation        = nation
        self.marriage      = marriage
        self.job           = job
        self.salary        = salary
        self.wx            = wx
        self.wx_v          = wx_v
        self.qq            = qq
        self.qq_v          = qq_v
        self.mobile        = mobile
        self.mobile_v      = mobile_v
        self.email         = email
        self.email_v       = email_v
        self.aim           = aim
        self.hobby0        = hobby0
        self.hobby1        = hobby1
        self.hobby2        = hobby2
        self.hobby3        = hobby3
        self.hobby4        = hobby4
        self.statement     = statement

    id                = Column(Integer, primary_key=True)
    nick_name         = Column(String(16))
    password          = Column(String(16))
    age               = Column(Integer)
    shuxiang          = Column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'))
    xingzuo           = Column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'))
    height            = Column(Integer)
    weight            = Column(Integer)
    blood             = Column(Enum('0', '1', '2', '3', '4'))
    location          = Column(String(32))
    jiguan            = Column(String(64))
    gender            = Column(Enum('0', '1', '2'))
    education         = Column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8'))
    nation            = Column(Integer)
    marriage          = Column(Enum('0', '1', '2', '3'))
    job               = Column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'))
    salary            = Column(Enum('0', '1', '2', '3', '4', '5', '6', '7', '8'))
    wx                = Column(String(32))
    wx_v              = Column(Enum('0', '1'))
    qq                = Column(String(16))
    qq_v              = Column(Enum('0', '1'))
    mobile            = Column(String(16))
    mobile_v          = Column(Enum('0', '1'))
    email             = Column(String(128))
    email_v           = Column(Enum('0', '1'))
    aim               = Column(Enum('0', '1'))
    hobby0            = Column(Integer)
    hobby1            = Column(Integer)
    hobby2            = Column(Integer)
    hobby3            = Column(Integer)
    hobby4            = Column(Integer)
    statement         = Column(String(160))
    def dic_return(self):
        return {'id':   self.id,            'nick_name':     self.nick_name,
                'password': self.password,  'age':           self.age,
                'shuxiang': self.shuxiang,  'xingzuo':       self.xingzuo,
                'height':   self.height,    'weight':        self.weight,
                'blood':    self.blood,     'location':      self.location,
                'jiguan':   self.jiguan,    'gender':        self.gender,
                'education':self.education, 'natioin':       self.nation,
                'marriage': self.marriage,  'job':           self.job,
                'salary':   self.salary,    'wx':            self.wx,
                'qq':       self.qq,        'mobile':        self.mobile,
                'email':    self.email,     'aim':           self.aim,
                'hobby0':   self.hobby0,    'hobby1':        self.hobby1,
                'hobby2':   self.hobby2,    'hobby3':        self.hobby3,
                'hobby4':   self.hobby4,    'statement':     self.statement
        }

class Hobby(Base):
    __tablename__ = conf.table_hobby
    def __init__(self, id_, kind, seq, name):
        self.id       = id
        self.kind     = kind
        self.seq      = seq
        self.name     = name

    id                = Column(Integer, primary_key=True)
    kind              = Column(Integer)
    seq               = Column(Integer)
    name              = Column(String(32))

    def dic_return(self):
        return { 'id':   self.id,     'kind': self.kind,
                 'seq':  self.seq,    'name': self.name}

class Neixindubai(Base):
    __tablename__ = conf.table_neixindubai
    def __init__(self, id_, uid, seq, cnt):
        self.id       = id_
        self.userid   = uid
        self.seq      = seq
        self.content  = cnt

    id                = Column(Integer, primary_key=True)
    userid            = Column(Integer)
    seq               = Column(Integer)
    content           = Column(String(512))

    def dic_return(self):
        return {'id':     self.id,  'userid': self.userid,
                'seq':    self.seq, 'content': self.content}

class Picture(Base):
    __tablename__ = conf.table_picture
    def __init__(self, id_, uid, url):
        self.id       = id_
        self.userid   = uid
        self.url      = url

    id                = Column(Integer, primary_key=True)
    userid            = Column(Integer)
    url               = Column(String(96))

    def dic_return(self):
        return {'id': self.id, 'userid': self.userid, 'url': self.url}
#账户表
class Account(Base):
    __tablename__ = conf.table_account
    def __init__(self, id_, uid, b1, b2, b3, b4):
        self.id       = id_
        self.userid   = uid
        self.bean1    = s1
        self.bean2    = s2
        self.bean3    = s3
        self.bean4    = s4

    id                = Column(Integer, primary_key=True)
    userid            = Column(Integer) 
    bean1             = Column(Integer) #充值
    bean2             = Column(Integer) #每日赠送 不累加
    bean3             = Column(Integer) 
    bean4             = Column(Integer) 

    def dic_return(self):
        return {'id':   self.id,       'userid':   self.userid,
                'bean1':self.bean1,    'bean2':    self.bean2,
                'bean3':self.bean3,    'bean4':    self.bean4 }


#充值记录表
class AccountRecord(Base):
    __tablename__ = conf.table_account_record
    def __init__(self, id_, uid, way, t, n, n1):
        self.id       = id_
        self.userid   = uid
        self.way      = way
        self.time     = t
        self.num      = n
        self.num1     = n1

    id                = Column(Integer, primary_key=True)
    userid            = Column(Integer)
    way               = Column(Integer) #充值方式1=wx 2=alipay
    time              = Column(TIMESTAMP)
    num               = Column(Integer)#实际的人民币 分
    num1              = Column(Integer)#转换后的示爱豆 个

    def dic_return(self):
        return {'id':   self.id,     'userid':  self.userid,
                'way':  self.way,    'time':    self.time,
                'num':  self.num,    'num1':    self.num1}

class Kangguo(Base):
    __tablename__ = conf.table_kanguo
    def __init__(self, id_, id_f, id_t, t):
        self.id       = id_
        self.id_from  = id_f
        self.id_to    = id_t
        self.time     = t

    id            = Column(Integer, primary_key=True)
    id_from       = Column(Integer)
    id_to         = Column(Integer)
    time          = Column(TIMESTAMP)
    
    def dic_return(self):
        return {'id':  self.id,      'id_from': self.id_from,
                'id_to': self.id_to, 'time':    self.time}

class email(Base):
    __tablename__ = conf.table_email
    def __init__(self, id_, id_f, id_t, t):
        self.id       = id_
        self.id_from  = id_f
        self.id_to    = id_t
        self.time     = t

    id            = Column(Integer, primary_key=True)
    id_from       = Column(Integer)
    id_to         = Column(Integer)
    time          = Column(TIMESTAMP)
    
    def dic_return(self):
        return {'id':  self.id,      'id_from': self.id_from,
                'id_to': self.id_to, 'time':    self.time}

class Emailcontent(Base):
    __tablename__ = conf.table_email_content
    def __init__(self, id_, eid, seq, cnt):
        self.id       = id_
        self.email_id = eid
        self.seq      = seq
        self.content  = cnt
        
    id            = Column(Integer, primary_key=True)
    email_id      = Column(Integer)
    seq           = Column(Integer)
    content       = Column(String(128))

    def dic_return(self):
        return {'id': self.id,  'email_id': self.email_id,
                'seq': self.seq, 'content': self.content}

'''
'''
if __name__ == '__main__':
    S = DBSession()
    u = User(0, 'qiang', '123', '1', '2', 170, 75, '1', 'beijing', 'jiguan', '1', '1', 1, '1', '1', '1', '1234wx', '1234qq','123mobile', 'email', '1', 2048, 127, 127, 127, 63, 'hello')
    S.add(u)
    S.commit()
    S.close()

