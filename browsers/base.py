from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from amazoncaptcha import AmazonCaptcha
from selenium.webdriver.common.keys import Keys
from uuid import uuid4
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from config import PROFILES_FOLDER
import random
import logging
import time
import requests
import traceback
import json
import os

from seleniumwire import webdriver as wire_webdriver
from selenium import webdriver

logger = logging.getLogger('seleniumwire.handler:Capturing')
logger.setLevel(logging.ERROR)


class Base():
    def __init__(self, email=None, keyword=None, start_url='https://www.walmart.com/', headless=True, profile=None, proxy=False, host="", port="", user="", password="", wait_time=30):
        self.driver = None
        self.wait_time = wait_time
        self.user = user
        self.password = password
        self.Keys = Keys
        self.email = email
        self.setup_driver(proxy=proxy, headless=headless, profile=profile, host=host, port=port, user=user, password=password)
    
    def valid_otp(self):
        if self._has_captcha():
            self._amazon_captcha()
        # try:
        count = 1
        while count > 0:
            try:
                cf_otp = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, "auth-send-code")))
                cf_otp.click()
            except TimeoutException:
                time.sleep(1)
                count -= 1
        try:
            otp = self.wait.until(EC.presence_of_element_located((By.ID, "auth-mfa-otpcode")))
            otp.send_keys(self.gen_otp())
            remember = self.wait.until(EC.presence_of_element_located((By.ID, "auth-mfa-remember-device")))
            remember.click()
            submit = self.wait.until(EC.presence_of_element_located((By.ID, "auth-signin-button")))
            submit.click()
        except:
            self.driver.save_screenshot('/tmp/otpcode.png')
            traceback.print_exc()
    
    
    def login(self):
        try:
            #self.driver.save_screenshot(f"/tmp/{s.name}-loggingcheck1.png")
            submit = self.wait.until(EC.presence_of_element_located((By.ID, "signInSubmit")))
            if submit:
                pw = self.wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
                self.ac.move_to_element(pw).click().perform()
                for k in self.password:
                    time.sleep(random.choice([0.1, 0.2]))
                    pw.send_keys(k)
                # pw.send_keys(self.password)
                time.sleep(1)
                try:
                    user = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.ID, "ap_email")))
                    self.ac.move_to_element(user).click().perform()
                    for k in self.user:
                        user.send_keys(k)
                        time.sleep(random.choice([0.1, 0.2]))
                    # user.send_keys(self.user)
                except TimeoutException:
                    logging.error(traceback.print_exc())
                    print("passed email")
                    pass
                rememberme = self.wait.until(EC.presence_of_element_located((By.NAME, "rememberMe")))
                self.ac.move_to_element(rememberme).click().perform()
                # rememberme.click()
                time.sleep(random.choice([0.1, 0.3]))
                # submit.click()
                self.ac.move_to_element(submit).click().perform()
                time.sleep(1)
                self.valid_otp()

                count = 3
                while count > 0:
                    try:
                        skip_phone = WebDriverWait(self.driver, 1).until(
                            EC.presence_of_element_located(
                                (By.ID, 'ap-account-fixup-phone-skip-link')))
                        skip_phone.click()
                    except TimeoutException:
                        count -= 1
                        time.sleep(1)
                        pass
                return True

        except Exception as e:
            #traceback.print_exc()
            logging.error(traceback.print_exc())
            #self.noti.sendMessage(f"ERROR.GET_OPTIONS.LOGINERROR_DETAIL! - User: {email} - ERRROR: {e}", chat_id=noti.amz_fsg)
            return False

    def _has_captcha(self):
        self.driver.save_screenshot('/tmp/check_captcha.png')
        try:
            for div in self.wait.until(self.EC.presence_of_all_elements_located((self.By.CSS_SELECTOR, "div.a-box"))):
                if 'Type the characters you see in this image' in div.text:
                    return True
        except:
            return False
        return False

    def _amazon_captcha(self):
        self.driver.save_screenshot('/tmp/check_captcha.png')
        try:
            img = self.wait.until(self.EC.presence_of_element_located((self.By.TAG_NAME, "img")))
        except Exception:
            return False
        url = img.get_attribute('src')
        if '/captcha/' not in url:
            return False
        logging.error(url)
        try:
            captcha = AmazonCaptcha.fromlink(url)
            solution = captcha.solve()
            logging.error(f"CAPTCHA: {solution}")
            _input = self.wait.until(self.EC.presence_of_element_located((self.By.ID, "captchacharacters")))
            _input.send_keys(solution)
            _input.send_keys(Keys.ENTER)
        except Exception:
            logging.error(traceback.print_exc())
            return False
        try:
            button = self.wait.until(self.EC.presence_of_element_located((self.By.TAG_NAME, "button")))
            button.click()
        except Exception:
            logging.error(traceback.print_exc())
            return False
        return True

    def _verify_proxy(self, host, port, user, password, region="US"):
        PROXY = f"{user}:{password}@{host}:{port}"
        logging.error(PROXY)
        _proxy = {'http': 'http://' + PROXY,
                  'https': 'https://' + PROXY,
                  'ftp': 'ftp://' + PROXY}
        logging.error(_proxy)
        r = requests.get("http://api.myip.com", proxies=_proxy)
        if r.status_code != 200:
            print(r.json())
            return False
        if r.json().get("cc") == region:
            return True
        return False


    @property
    def headers(self):
        return {
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
            'content-type': 'text/plain;charset=UTF-8',
            'accept': '*/*',
            'origin': 'https://www.etsy.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7,de;q=0.6,ca;q=0.5,ig;q=0.4,mt;q=0.3,hmn;q=0.2,es;q=0.1',
        }

    def setup_driver(self, host="185.193.157.60", port="12323", user="fsggroup", password="D0ntkn0w_country-us_session-ry2wwsq2_lifetime-24h", proxy=False, headless=False):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36")
        self.chrome_options.add_argument("--start-maximized")

        self.chrome_options.add_argument("--disable-crash-reporter")
        self.chrome_options.add_argument("--disable-logging")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # self.chrome_options.add_argument("--kiosk")
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument("--disable-notifications")

        #self.chrome_options.add_extension('anti_cookie.crx')
        
        if headless:
            self.chrome_options.add_argument("--disable-gpu")
            self.chrome_options.add_argument("--kiosk")
            self.chrome_options.add_argument('--disable-infobars')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument("--headless=new")
            self.chrome_options.add_argument("--disable-notifications")
            self.chrome_options.add_argument("--disable-extensions")
            # self.chrome_options.add_argument("--inprivate")
        if proxy:
            PROXY = f"{user}:{password}@{host}:{port}"
            proxies = {
                'proxy': {
                    'http': 'socks5://' + PROXY,
                    'https': 'socks5://' + PROXY,
                    'no_proxy': 'localhost,127.0.0.1'
                },
                'exclude_hosts': ['google-analytics.com'],
            }
            self.driver = wire_webdriver.Chrome(seleniumwire_options=proxies, options=self.chrome_options)
        else:
            self.driver = webdriver.Chrome(options=self.chrome_options)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"})
        # self.driver.delete_all_cookies()
        self.wait = WebDriverWait(self.driver, self.wait_time)
        self.ac = ActionChains(self.driver)
        self.EC = EC
        self.By = By
        self.WebDriverWait = WebDriverWait

    def _scroll(self):

        """scroll to lazy loadingpage"""

        count = 0

        while count < self.driver.execute_script("return document.documentElement.scrollHeight"):
            count += 250
            self.driver.execute_script(f"window.scrollBy(0,{count})", "")
            time.sleep(0.3)

    def teadown(self):
        self.driver.quit()
