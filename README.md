# getGenshinKeyinHuyaStream

## 项目原由

每次做原神直播任务以后激活码复制很麻烦，所以写了个脚本方便提取激活码，同时有每天是否全部领取激活码的提示

## 项目说明

项目基于 selenium 开发，需要自己安装对应的 chrome 浏览器和驱动，同时数据放在 mysql 里，同样也需要自己安装。同时配置了两种消息发送的模式，分别为邮件和微信（某公众号），可通过 setting.json 进行配置

项目执行流程为:

- 1、查询数据库、表信息,若不存在则创建
- 2、根据用户名进行登录验证，若不存在则登录，可根据配置文件选择根据二维码或者密码登录，每次登录判断间隔为 60s
- 3、查询网页奖励信息，并写入数据库
- 4、查询当天奖励是否领取，发送信息

配置文件位 setting.json，分别对应的是虎牙信息，数据库信息，邮件发送信息，微信发布信息，定时信息

## setting.json 结构说明

```
{
        "weburl": "xxxxxx",                     #虎牙登录连接
        "huya": {"username": "xxxxxx",          #虎牙用户名
                "id": "xxxxx",                  #虎牙登录 id
                "password": "xxxx"，            #虎牙登录密码
                "login_method": "scan"},        #扫码或者密码登录
        "database": {"localhost": "localhost",  #数据库
                "user": "root",                 #数据库用户名
                "password": "xxxx"},            #数据库密码
        "email": {"sender": "xxxx@xxx.com",     #邮件发送人
                "receiver": "xxx@xxx.com",      #邮件接收人
                "mail_host": "smtp.qq.com",     #邮件发送途径
                "mail_pass": "xxxx",            #邮件识别码
                "trigger": "false"},            #邮件提示是否开启
        "weixin": {"url": "xxx",                #微信提示链接
                "trigger": "true"},             #微信提示是否开启
        "timer": {"trigger": "false",           #定时器是否开启
                "time": "23:45"}}               #定时器每天定时时间
```
