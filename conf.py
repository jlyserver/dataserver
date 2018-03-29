#-*- coding: utf-8 -*-
import ConfigParser

class Loginconf():
    def __init__(self, name):
        p = ConfigParser.ConfigParser()
        p.read(name)
       
        self.sys_port                    = p.getint('sys', 'sys_port')
        self.sys_ip                      = p.get('sys', 'sys_ip')

        self.dbserver_ip                 = p.get('db', 'dbserver_ip')
        self.dbserver_port               = p.getint('db', 'dbserver_port')

        self.redis_ip                    = p.get('redis', 'redis_ip')
        self.redis_port                  = p.getint('redis', 'redis_port')
        self.redis_db                    = p.getint('redis', 'redis_db')
        self.redis_password              = p.get('redis', 'redis_password')
        self.redis_timeout               = p.getint('redis', 'redis_timeout')

        self.mysql_host                 = p.get('mysql', 'mysql_host')
        self.mysql_port                 = p.getint('mysql', 'mysql_port')
        self.mysql_user                 = p.get('mysql', 'mysql_user')
        self.mysql_password             = p.get('mysql', 'mysql_password')
        self.mysql_db                   = p.get('mysql', 'mysql_db')
        self.mysql_encode               = p.get('mysql', 'mysql_encode')

        self.table_user                 = p.get('table', 'table_user')
        self.table_hobby                = p.get('table', 'table_hobby')
        self.table_neixindubai          = p.get('table', 'table_neixindubai')
        self.table_picture              = p.get('table', 'table_picture')
        self.table_account              = p.get('table', 'table_account')
        self.table_account_record       = p.get('table', 'table_account_record')
        self.table_kanguo               = p.get('table', 'table_kanguo')
        self.table_guanzhu              = p.get('table', 'table_guanzhu')
        self.table_email                = p.get('table', 'table_email')
        self.table_email_content        = p.get('table', 'table_email_content')
        self.pic_ip                     = p.get('pic', 'pic_ip')
        self.postfix                    = p.get('pic', 'postfix')

    def dis(self):
        print(self.sys_ip)
        print(self.sys_port)
        print(self.redis_ip)
        print(self.redis_port)
        print(self.redis_db)
        print(self.table_user)
        print(self.table_hobby)
        print(self.table_neixindubai)
        print(self.table_picture)
        print(self.table_account)

conf    = Loginconf('./conf.txt')
if __name__ == "__main__":
    conf.dis()
