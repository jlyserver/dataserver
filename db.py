#-*- coding: utf8 -*-

from table import *

class User_():
#返回  值: 引用
    def query_by_id(self, id_):
        S = DBSession()
        r = S.query(User).filter(User.id == id_).first()
        S.close()
        return {}, None if not r else r.dic_return(), r

    def query_name(self, name):
        S = DBSession()
        r = S.query(User).filter(User.nick_name == name).first()
        S.close()
        return {}, None if not r else r.dic_return(), r

    def query_name_password(self, name, passwd):
        S = DBSession()
        r = S.query(User).filter(and_(User.nick_name == name, User.password == passwd)).first()
        S.close()
        return None if not r else r
    
    def add(self, name, passwd):
        S = None
        try:
            S = DBSession()
            r = True
            u = User(name=name, password=passwd, id_=0)
            S.add(u)
            S.commit()
        except:
            r = False
        finally:
            S.close()
        return r
'''
    def update(self, id_=0, uname='', passwd='', age=0, shuxiang=None,\
            xingzuo=None, height=None, weight=None, blood=None, location=None,\
            jiguan='', gender=None, edu=None, nation=None, marriage=None,\
            job=None, salary=None, wx=None, qq=None, mobile=None, email=None,\
            aim, h0, h1, h2,\
                h3, h4, stat):
        if not id_:
            return None
        S = DBSession()
        r = S.query(User).filter(User.id == id_).first()
        if not r:
            return None

        D = {}
        if uname:
            D[User.name] = name
        if passwd:
            D[User.password] = passwd
        if age:
            D[User.age] = age
        if shuxiang:
            D[User.shuxiang] = shuxiang
        if xingzuo:
            D[User.xingzuo]  = xingzuo
        if height:
            D[User.height]   = height
        if weight:
            D[User.weight]   = weight
        if blood:
            D[User.blood]    = blood

        if location:
            D[User.location] = location
        if jiguan:
            D[User.jiguan]   = jiguan
        if gender:
            D[User.gender]   = gender
        if edu:
            D[User.education]= edu
        if nation:
            D[User.nation]   = nation
        if marriage:
            D[User.marriage] = marriage
        if job:
            D[User.job]      = job
        if salary:
            D[User.salary]   = salary
        if wx and r.wx_v == '0':
            D[User.wx]       = wx
        if qq and r.qq_v == '0':
            D[User.qq]       = qq
        if mobile and r.mobile_v == '0':
            D[User.mobile]   = mobile
        if email and email_v == '0':
            D[User.email]    = email
        if aim:
            D[User.aim]      = aim
        if h0:
            D[User.hobby0]   = h0
        if h1:
            D[User.hobby1]   = h1
        if h2:
            D[User.hobby2]   = h2
        if h3:
            D[User.hobby3]   = h3
        if h4:
            D[User.hobby4]   = h4
        if stat:
            D[User.stat]     = stat

        r = S.query(User).filter(User.id == id_).update(D, synchronize_session=False)
        S.commit()
        S.close()
        return True
'''

user_ = User_()

if __name__ == '__main__':
    pass

