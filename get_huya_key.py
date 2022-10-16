from multiprocessing import managers
from multiprocessing.dummy import Manager
import time
import pickle
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
import sys
import requests
from selenium import webdriver
import json
import pymysql
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from selenium.webdriver.edge.service import Service
from toollib import autodriver


class getHuyaKey(object):
    def __init__(self,json_setting):
        self.json_setting=json_setting
        self.username = ''
        self.db = pymysql.connect(host=self.json_setting['database']['localhost'], user=self.json_setting['database']['user'], password=self.json_setting['database']['password'], port=3306)
        self.cursor = self.db.cursor()
        self.driver = self.getDriver()
        self.driver.get(self.json_setting['weburl'])

    def main(self):
        strLog = "开始运行脚本"
        print(strLog)
        self.writelog(strLog)
        self.is_login()     #进行登录
        self.driver.get(self.json_setting['weburl'])  #刷新网页
        time.sleep(3)
        self.get_info()     #读取网页激活码
        self.check_huya_database() #检查每天激活码是否领取
        self.driver.quit()  #退出浏览器
        self.close_db()     #关闭数据库连接

    # 检测数据库是否存在，若不存在，则创建
    def createDatabse(self):
        cursor = self.db.cursor()
        cursor.execute('show databases')
        exist = False
        for i in cursor:
            if i[0] == "yuanshen":
                exist = True
                strLog = "存在yuanshen数据库"
                print(strLog)
                self.writelog(strLog)
        if exist == False:
            cursor.execute('create database yuanshen')
            strLog = "不存在yuanshen数据库，已建立"
            print(strLog)
            self.writelog(strLog)
        self.db = pymysql.connect(host=self.json_setting['database']['localhost'], user=self.json_setting['database']['user'], password=self.json_setting['database']['password'], port=3306,db="yuanshen")

        try:
            sql = "select * from information_schema.TABLES where TABLE_NAME = 'huya'"
            cursor.execute(sql)
            results = cursor.fetchall()
            if results == ():
                strLog = "数据库内huya不存在"
                print(strLog)
                self.writelog(strLog)
                try:
                    sql = "CREATE TABLE IF NOT EXISTS huya(ID INT(10) NOT NULL, Name VARCHAR(255), Gamekey VARCHAR(255) NOT NULL, Time Date)"
                    cursor.execute(sql)
                    strLog = "数据库内huya创建成功"
                    print(strLog)
                    self.writelog(strLog)
                except:
                    s = sys.exc_info()
                    strErrlog = "Error '%s' happened on line %d" % (
                        s[1], s[2].tb_lineno)
                    print(strErrlog)
                    self.writeerrlog(strErrlog)
                    strLog = "数据库内huya创建失败"
                    print(strLog)
                    self.writelog(strLog)
            else:
                strLog = "数据库内huya存在"
                print(strLog)
                self.writelog(strLog)
                return None
        except Exception as e:
            s = sys.exc_info()
            strErrlog = "Error '%s' happened on line %d" % (
                s[1], s[2].tb_lineno)
            print(strErrlog)
            self.writeerrlog(strErrlog)
            strLog = "数据库huya表查询失败"
            print(strLog)
            self.writelog(strLog)

    #每天检测激活码是否领取
    def check_huya_database(self):
        todaydate = datetime.date.today()
        try:
            cursor = self.db.cursor()
            sql = 'select count(Time = "{0}" or null) from huya'.format(
                todaydate)
            cursor.execute(sql)
            results = cursor.fetchone()[0]
            # print(results)
            if (results >= 6):
                strLog = "虎牙原神直播任务当天奖励已全部领取完毕"
                print(strLog)
                self.writelog(strLog)
            else:
                strLog = "虎牙原神直播任务当天奖励未领取，请赶快领取！！"
                print(strLog)
                self.writelog(strLog)
            self.send_WXMessage(strLog, strLog)
            self.send_email(strLog)
        except Exception as e:
            s = sys.exc_info()
            strErrlog = "Error '%s' happened on line %d" % (
                s[1], s[2].tb_lineno)
            print(strErrlog)
            self.writeerrlog(strErrlog)
            strLog = "数据库huya表查询失败"
            print(strLog)
            self.writelog(strLog)

    #判断是否登录
    def is_login(self):
        while self.username != self.json_setting['huya']['username']:
            self.set_cookie() #设置cookie
            self.driver.refresh()
            time.sleep(3)
            html = self.driver.page_source  # 获取网页信息
            if html.find(self.json_setting['huya']['username']) == -1:  # 利用用户名判断是否登陆
                strLog = "请手动登录"
                print(strLog)
                self.writelog(strLog)
                self.login()
            else:
                self.username = self.json_setting['huya']['username']
        strLog = "登录成功"
        print(strLog)
        self.writelog(strLog)

    #进行登录
    def login(self):
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                         "[class='item-btn J_drawAward']"))).click()  #随便点击按钮，弹出登录页面
        time.sleep(3)
        firstelement = self.driver.find_element_by_css_selector("[id='UDBSdkLgn_iframe']") #切换iframe
        self.driver.switch_to.frame(firstelement)

        if self.json_setting['huya']['login_method'] == 'scan': #根据配置文件选择是扫描二维码登录还是密码登录
            self.Login_by_scan()
        else:
            self.Login_by_password()

        self.driver.refresh()
        time.sleep(2)
        html = self.driver.page_source  # 获取网页信息
        if html.find(self.json_setting['huya']['username']) != -1:  # 利用用户名判断是否登陆
            self.username = self.json_setting['huya']['username']
            self.save_cookie()  #保存cookies

    #获取登录二维码
    def Login_by_scan(self):
        qrurl = self.driver.find_element_by_id("qr-image").get_attribute('src') 
        # print(qrurl)
        self.save_image(url=qrurl)
        strLog = "虎牙登录使用二维码验证，请于60s内完成验证"
        print(strLog)
        self.writelog(strLog)
        self.send_WXMessage(strLog, strLog)
        self.send_email(strLog)
        time.sleep(70)


    #根据密码登录
    def Login_by_password(self):
        secondelement = self.driver.find_element_by_class_name("udb-wrap")
        thirdelement = secondelement.find_element_by_class_name('input-login')
        thirdelement.click()
        time.sleep(3)
        input_email = self.driver.find_element_by_css_selector("[class='udb-input udb-input-account udbstatInput']") # 输入虎牙id
        input_email.click()
        input_email.send_keys(self.json_setting['huya']['id'])
        time.sleep(1)
        input_password = self.driver.find_element_by_css_selector(
            "[class='udb-input udb-input-pw udbstatInput']")  # 输入密码
        input_password.click()
        input_password.send_keys(self.json_setting['huya']['password'])
        time.sleep(1)
        self.driver.find_element_by_css_selector("[class='udb-button clickstat']").click()  # 点击登录按钮
        time.sleep(5)
        try:
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                                   "[class='layui-layer layui-layer-iframe udb-auth-64']")))  # 验证框出现
            strLog = "虎牙登录使用密码验证，弹出验证框"
            print(strLog)
            self.writelog(strLog)
            strLog = "虎牙登录使用密码验证，请于60s内完成验证"
            print(strLog)
            self.writelog(strLog)
            self.send_WXMessage(strLog, strLog)
            self.send_email(strLog)
            time.sleep(30)
        except:
            strLog = "虎牙登录使用密码验证，未弹出验证框"
            print(strLog)
            self.writelog(strLog)
        time.sleep(5)

    #保存cookie
    def save_cookie(self):
        cookies = self.driver.get_cookies()
        # print(cookies)
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))# 将cookie序列化保存下来

    #往浏览器添加cookie
    def set_cookie(self):
        self.driver.delete_all_cookies()
        #利用pickle序列化后的cookie
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
               #以下信息使用开发者工具或Chrome插件EditThisCookie可查看
                cookie_dict = {
                    "domain": '.huya.com',  # 火狐浏览器不用填写，谷歌要需要
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'path': '/',
                    # "expires": "",
                    'httpOnly': cookie.get('httpOnly'),
                    'secure': cookie.get('secure')

                }
                self.driver.add_cookie(cookie_dict)
                # print(cookie_dict)
            strLog = "cookie添加成功"
            print(strLog)
            self.writelog(strLog)
        except Exception as e:
            s = sys.exc_info()
            strErrlog = "Error '%s' happened on line %d" % (
                s[1], s[2].tb_lineno)
            print(strErrlog)
            self.writeerrlog(strErrlog)
            strLog = "cookie添加失败"
            print(strLog)
            self.writelog(strLog)

    #通过网页获取激活码，并写入数据库
    def get_info(self):
        self.createDatabse()
        try:
            firstelement = self.driver.find_element(By.XPATH,'//*[@id="matchComponent4"]/div/div[1]/div/div[2]')#切换到开播页面
            # print(firstelement.get_attribute('outerHTML'))
            firstelement.click()
            time.sleep(3)
            secondelement = self.driver.find_element(By.XPATH,'//*[@id="matchComponent14"]/div/div[1]/div[1]/div/div[2]/div[1]/div') #点击查询历史
            secondelement.click()
            time.sleep(3)
            key_list = self.driver.find_elements(By.XPATH,'//*[@id="matchComponent14"]/div[2]/div/div/div/ol/li') #获得所有激活码信息
            strLog = "获得激活码信息，共{0}个".format(len(key_list))
            print(strLog)
            self.writelog(strLog)
            for singalKey in key_list:
                result = re.search('恭喜你获得(.*?)\n卡号：(.*?) 密码：(.*?)\n(.*)', singalKey.text, re.S)
                if result:
                    # print(result.group(1), result.group(2),result.group(3),result.group(4))
                    self.add_huya_database(ID=time.mktime(time.strptime(result.group(4), '%Y.%m.%d %H:%M')),Key=result.group(2),Name=result.group(1))

        except Exception as e:
            s = sys.exc_info()
            strErrlog = "Error '%s' happened on line %d" % (
                s[1], s[2].tb_lineno)
            print(strErrlog)
            self.writeerrlog(strErrlog)
            strLog = "激活码信息获取失败"
            print(strLog)
            self.writelog(strLog)


    #将激活码加入数据库
    def add_huya_database(self, ID, Key, Name):
        cursor = self.db.cursor()
        keytime = time.strftime("%Y-%m-%d", time.localtime(ID))
        try:
            sql = 'SELECT * FROM huya WHERE Gamekey ="{0}"'.format(Key) #根据激活码判断是否写入到数据库
            cursor.execute(sql)
        except Exception as e:
            s = sys.exc_info()
            strErrlog = "Error '%s' happened on line %d" % (
                s[1], s[2].tb_lineno)
            print(strErrlog)
            self.writeerrlog(strErrlog)
            strLog = "数据库内huya表查询失败"
            print(strLog)
            self.writelog(strLog)

        database_results = cursor.fetchall()
        if database_results != (): #存在则不添加
            strLog = "数据库内huya存在{0}的{1}，查询成功\n".format(keytime, Name)
            print(strLog)
        else:
            sql = 'INSERT INTO huya(ID, Name, Gamekey, Time) VALUES({0},"{1}","{2}","{3}")'.format(ID,Name,Key,keytime) #不存在，写入数据库
            try:
                cursor.execute(sql) # 执行sql语句
                self.db.commit()    # 提交到数据库执行
                strLog = "数据库huya无{0}的{1}信息，已添加\n".format(keytime, Name)
                print(strLog)
            except Exception as e:
                self.db.rollback() #出错回滚
                s = sys.exc_info()
                strErrlog = "Error '%s' happened on line %d" % (
                    s[1], s[2].tb_lineno)
                print(strErrlog)
                self.writeerrlog(strErrlog)
                strLog = "数据库huya添加sql语句失败"
                print(strLog)
                self.writelog(strLog)

    #保存二维码为图片
    def save_image(self,url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                file_path = '{0}.{1}'.format("login_image", 'png')
                if  os.path.exists(file_path):
                    os.remove(file_path)
                    strLog = '本地存在二维码，已移除'
                    print(strLog)
                    self.writelog(strLog)
                with open(file_path, 'wb') as f:
                        strLog = '生成二维码，已保存到本地'
                        print(strLog)
                        self.writelog(strLog)
                        f.write(response.content)
                f.close()
        except Exception as e:
                s = sys.exc_info()
                strErrlog = "Error '%s' happened on line %d" % (
                    s[1], s[2].tb_lineno)
                print(strErrlog)
                self.writeerrlog(strErrlog)
                strLog = "保存二维码失败"
                print(strLog)
                self.writelog(strLog)

    #发送邮件
    def send_email(self, content):
        if self.json_setting['email']['trigger'] == 'true':
            message = MIMEText(content, "plain", "utf-8")
            message["From"] = Header(self.json_setting['email']['sender'], "utf-8")
            message["To"] = Header(self.json_setting['email']['receiver'], "utf-8")
            subject = "虎牙原神脚本执行结果"  # 发送的主题，可自由填写
            message["Subject"] = Header(subject, "utf-8")
            try:
                smtpObj = smtplib.SMTP_SSL(self.json_setting['email']['mail_host'], 465)
                smtpObj.login(self.json_setting['email']['sender'], self.json_setting['email']['mail_pass'])
                smtpObj.sendmail(self.json_setting['email']['sender'], self.json_setting['email']['receiver'], message.as_string())
                smtpObj.quit()
                strLog = '邮件发送成功，内容为"{0}"'.format(content)
                print(strLog)
                self.writelog(strLog)
            except Exception as e:
                s = sys.exc_info()
                strErrlog = "Error '%s' happened on line %d" % (
                    s[1], s[2].tb_lineno)
                print(strErrlog)
                self.writeerrlog(strErrlog)
                strLog = '邮件发送失败，内容为"{0}"'.format(content)
                self.writelog(strLog)

    #发送微信信息
    def send_WXMessage(self, title, content):
        if self.json_setting['weixin']['trigger'] == 'true':
            headers = {
                "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Content-Type': 'application/json',
            }
            data = {}
            data['title'] = title
            data['desp'] = content
            try:
                r = requests.post(self.json_setting['weixin']['url'],
                                  headers=headers, data=json.dumps(data))
                strLog = '微信信息发送成功，内容为"{0}"'.format(content)
                print(strLog)
                self.writelog(strLog)
            except:
                strLog = '微信信息发送失败，内容为"{0}"'.format(content)
                print(strLog)
                self.writelog(strLog)

    #写日志
    def writelog(self, content, encoding='utf-8'):
        with open("huyalog.txt", "a", encoding='utf-8') as f:
            strLog = "[{0}]   {1}\n".format(time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime()),content)
            print(strLog)
            f.write(strLog)
            f.close()

    #写错误日志
    def writeerrlog(self, content, encoding='utf-8'):
        with open("huyaerrlog.txt", "a") as f:
            strLog = "[{0}]   {1}\n".format(time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime()), content)
            print(strLog)
            f.write(strLog)
            f.close()

    #关闭数据库连接
    def close_db(self):
        self.cursor.close()
        self.db.close()
        strLog = "脚本执行完毕\n\n"
        print(strLog)
        self.writelog(strLog)

    #设置webdriver驱动
    def getDriver(self):
        ch_options = webdriver.ChromeOptions()#为Chrome配置无头模式
        ch_options.add_argument("--headless")
        ch_options.add_argument('--no-sandbox')
        ch_options.add_argument('--disable-gpu')
        ch_options.add_argument('--disable-dev-shm-usage')
        if self.json_setting['platform'] == "linux64":
            chrome_driver_name = "chromedriver"
        else:
            chrome_driver_name = "chromedriver.exe"
        try:    #打包的时候加入library读取
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            driver = webdriver.Chrome(chromedriver_path,options=ch_options)
        except:  #直接用本文档的chromedriver
            if os.path.exists(chrome_driver_name): #如果存在本地文件
                try:
                    chromedriver_path = os.path.abspath(chrome_driver_name)
                    strLog = '本地存在{0}，路径为{1}'.format(chrome_driver_name,chromedriver_path)
                    print(strLog)
                    self.writelog(strLog)
                    print(chromedriver_path)
                    driver = webdriver.Chrome(executable_path=chromedriver_path,options=ch_options) 
                except:
                    os.remove(chrome_driver_name)
                    strLog = '已移除本地{0}'.format(chrome_driver_name)
                    print(strLog)
                    self.writelog(strLog)
                    driver_path = autodriver.chromedriver(platform = self.json_setting['platform'])
                    print(driver_path)
                    if self.json_setting['platform'] == "linux64":
                        os.system("chmod +x chromedriver")
                    driver = webdriver.Chrome(executable_path=driver_path,options=ch_options)
            else:   #如果不存在本地文件，则下载
                driver_path = autodriver.chromedriver(platform = self.json_setting['platform'])
                strLog = "已下载驱动{0},路径为{1}".format(chrome_driver_name,driver_path)
                if self.json_setting['platform'] == "linux64":
                    os.system("chmod +x chromedriver")
                    # os.system("/bin/cp -rf chromedriver /usr/bin/")
                print(strLog)
                self.writelog(strLog)
                driver = webdriver.Chrome(executable_path=driver_path,options=ch_options)
        return driver

if __name__ == '__main__':
    json_setting = json.load(open('setting.json', 'r', encoding='utf-8')) #读取setting.json的信息
    if json_setting['timer']['trigger'] == 'true': #如果设置了定时
        while True:
            time_now = time.strftime("%H:%M", time.localtime())  # 刷新
            # print(time_now)
            if time_now == json_setting['timer']['time']:  # 设置要执行的时间
                getHuyaKey(json_setting = json_setting).main()
                time.sleep(61)
    else: #如果未设置定时，直接执行
        getHuyaKey(json_setting=json_setting).main()
    