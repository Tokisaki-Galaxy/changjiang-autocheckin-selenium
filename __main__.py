import math
from time import sleep
import requests
import os
import json
import base64
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

changjiang = {
    "changjiang_user": os.getenv("CHANGJIANG_USER"),
    "changjiang_password": os.getenv("CHANGJIANG_PASSWORD"),
    "csrftoken": os.getenv("CSRFTOKEN"),
    "sessionid": os.getenv("SESSIONID"),
}

# 模拟鼠标移动
# TODO: 没做完，但是似乎没必要
def simulate_random_mouse(driver):
    # 创建一个ActionChains实例
    actions = ActionChains(driver)

    # 获取浏览器窗口的大小
    window_size = driver.get_window_size()

    # 计算中心点的位置
    center_x = window_size['width'] // 2
    center_y = window_size['height'] // 2

    # 在中心点画圈
    for i in range(360):
        # 计算圆上的点的坐标
        x = center_x + 100 * math.cos(i * math.pi / 180)
        y = center_y + 100 * math.sin(i * math.pi / 180)
    
        # 移动到计算出的坐标
        actions.move_to_element_with_offset(driver.find_element_by_tag_name('body'), x, y)
    
    # 每秒移动20像素
    sleep(0.05)

    # 执行鼠标移动
    actions.perform()

# 账户密码登陆
# TODO: 还没做完，有个滑块验证码没有处理
def userpwdlogin(driver):
    driver.find_element_by_xpath('//img[@class="changeImg"]').click()
    driver.find_element_by_xpath('//div[@data-type="phone"]').click()
    # 在输入时解码
    driver.find_element_by_name('loginname').send_keys(base64.b64decode(changjiang.changjiang_user).decode())
    driver.find_element_by_name('password').send_keys(base64.b64decode(changjiang.changjiang_password).decode())
    driver.find_element_by_xpath('//div[@class="submit-btn login-btn customMargin"]').click()

# 钉钉机器人
def DingMsg(Msg):
    # please set charset= utf-8
    HEADERS = {
        "Content-Type": "application/json ;charset=utf-8 "
    }
    # 这里的message是你想要推送的文字消息
    message = "猫猫：\n" + Msg
    stringBody = {
        "msgtype": "text",
        "text": {"content": message},
        "at": {
            "atMobiles": [""],
            "isAtAll": "true"  # @所有人 时为true，上面的atMobiles就失效了
        }
    }
    MessageBody = json.dumps(stringBody)
    result = requests.post(url=os.getenv("DING_WEBHOOK"), data=MessageBody, headers=HEADERS)
    print(result.text)

def main():
    # 创建一个浏览器实例
    if os.getenv("RUNNING_IN_DOCKER"):
        try:
            sleep(10)
            driver = webdriver.Remote(os.getenv("REMOTE_FIREFOX"), DesiredCapabilities.FIREFOX)
        except:
            print("连接远程selenium出错:", Exception)
    else:
        driver = webdriver.Edge()
        
    # 打开网页
    try:
        driver.get(r'https://changjiang.yuketang.cn/web/?next=/v2/web/index')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//img[@class="changeImg"]')))
    except:
        print("=====网络连接错误，无法连接到雨课堂=====",Exception)

    print("========Try Login=========")
    # 首先尝试cookie登陆
    try:
        # 构造新的cookie
        driver.delete_all_cookies()
        for i in range(2):
            last_item = list(changjiang.items())[-1-i]
            new_dict = {'name': last_item[0], 'value': last_item[1]}
            print(new_dict)
            driver.add_cookie(new_dict)
        driver.get(r'https://changjiang.yuketang.cn/v2/web/index')
        # 登陆失败的话到登录界面，通过是否有切换按钮可以判断登陆成功
        if driver.find_elements_by_xpath('//img[@class="changeImg"]'):
            raise(AssertionError)
        print("登陆成功")
    except:
        # 若cookie登陆失败采用用户密码登陆
        userpwdlogin(driver)

    try:
        driver.get(r'https://changjiang.yuketang.cn/v2/web/index')
        while(1):
            if driver.find_elements_by_xpath('//div[@class="name-box"]/span[@class="name"]'):
                DingMsg("雨课堂开始上课了,10秒后自动签到")
                print("雨课堂开始上课")
                sleep(10)
                driver.find_element_by_xpath('//div[@class="name-box"]/span[@class="name"]').click()
            sleep(10)
            driver.refresh()
    except:
        sleep(5)
        driver.close()

if '__main__' == __name__:
    # 用于直接运行py调试的时候环境变量设置
    if not os.getenv("RUNNING_IN_DOCKER"):
        import dotenv
        dotenv.load_dotenv('.env')
    main()
