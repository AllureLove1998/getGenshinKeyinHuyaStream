# getGenshinKeyinHuyaStream
每次做原神直播任务以后激活码复制很麻烦，所以写了个脚本方便提取激活码，同时有每天是否全部领取激活码的提示

项目基于selenium开发，需要自己安装对应的chrome浏览器和驱动，同时数据放在mysql里，同样也需要自己安装

配置文件位setting.json，分别对应的是虎牙信息，数据库信息，邮件发送信息，微信发布信息，定时信息

setting.json的结构介绍如下
{"huya": {"username": "xxxxxx",           #虎牙用户名
          "id": "xxxxx",                  #虎牙登录id
          "password": "xxxx"，            #虎牙登录密码
          "login_method": "scan"},        #扫码或者密码登录
  "database": {"localhost": "localhost",  #数据库
                "user": "root",           #数据库用户名
                "password": xxxx},        #数据库密码
  "email": {"sender": "xxxx@xxx.com",     #邮件发送人
            "receiver": "xxx@xxx.com",    #邮件接收人
            "mail_host": "smtp.qq.com",   #邮件发送途径
            "mail_pass": "xxxx",          #邮件识别码
            "trigger": "false"},          #邮件是否开启
  "weixin": {"url": "xxx",                #微信提示链接
              "trigger": "true"},         #微信是否开启
  "timer": {"trigger": "false",           #定时器是否开启
            "time": "23:45"}}             #定时器每天定时时间
