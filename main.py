import os
import random
import sys
import time
from datetime import datetime
from random import choice
from dotenv import load_dotenv
from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from termcolor import colored, cprint
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from fake_useragent import UserAgent
from apscheduler.schedulers.blocking import BlockingScheduler
import undetected_chromedriver as uc
import geckodriver_autoinstaller
import chromedriver_autoinstaller
import requests
from lxml.html import fromstring
from itertools import cycle
# from random_proxies import random_proxy
# import traceback

################################
# TODO: Add dynamic loading of user configurations - ex. *.employee and there will be a separate scheduled events for each user.
################################

################################
# Settings
################################
load_dotenv()
M_USERNAME = os.getenv('M_USERNAME')
M_PASSWORD = os.getenv('M_PASSWORD')
DEBUG_MODE = os.getenv("DEBUG_MODE", 'False').lower() in ['true', '1']
M_URL_DASHBOARD = os.getenv('M_URL_DASHBOARD')
WORK_STARTS = os.getenv('WORK_STARTS')
WORK_STARTS_MINUTE = os.getenv('WORK_STARTS_MINUTE')
WORK_ENDS = os.getenv('WORK_ENDS')
WORK_ENDS_MINUTE = os.getenv('WORK_ENDS_MINUTE')
RUN_HEADLESS = os.getenv("RUN_HEADLESS", 'False').lower() in ['true', '1']
EMPLOYEE_TIMEZONE = os.getenv('EMPLOYEE_TIMEZONE')
uc.TARGET_VERSION = int(os.getenv('CHROME_TARGET_VERSION'))
current_employees = []

################################
# Fine Tunning
################################
# Pseudo-randomness
RANDOM_START_MAX = int(os.getenv('RANDOM_START_MAX'))
RANDOM_STOP_MAX = int(os.getenv('RANDOM_STOP_MAX'))
DELAY_WAIT_FOR = int(os.getenv('DELAY_WAIT_FOR'))
# Elements
M_XPATH_START = '//*[@id="checkin-button"]'
M_XPATH_START_2 = '//*[@id="organizer"]/div[2]/div/div[2]/label/input'
M_XPATH_STOP = '//*[@id="checkout-button"]'
M_XPATH_STOP_2 = '//*[@id="organizer"]/div[2]/div/div[2]/label/input'
M_XPATH_LOGOUT = '//*[@id="logout-link"]'
M_XPATH_LOGIN = '//*[@id="submitButtons"]/input[1]'
M_XPATH_WORK_COUNTER = '//*[@id="checkout-button"]/div[1]'
M_XPATH_LOGIN_2 = '//*[@id="submitButtons"]'
M_XPATH_USER = '//*[@id="email"]'
M_XPATH_PASSWORD = '//*[@id="password"]'
M_XPATH_DASHBOARD = '//*[@id="li-dashboard"]'
M_XPATH_RECAPTCHA = '/html/body/section/div/div/div[1]/form/div[9]/input[1]'
M_SELECTOR_LOGIN = '#submitButtons > input.send.sl.login'
M_SELECTOR_DASHBOARD = '#li-dashboard'
M_SELECTOR_LOGOUT = '#logout-link'
M_SELECTOR_START = '#checkin-button'
M_SELECTOR_START_2 = '#organizer > div.forTreeEmployees > div > div.lineSideView.wrapperSwitchButton.align-center > label'
M_SELECTOR_STOP = '#checkout-button'
M_SELECTOR_STOP_2 = '#organizer > div.forTreeEmployees > div > div.lineSideView.wrapperSwitchButton.align-center > label'
M_SELECTOR_RECAPTCHA = '.recaptchaCode'


################################
# Helpers
################################
def slow_type(element, text, delay=0.1):
    for character in text:
        element.send_keys(character)
        time.sleep(delay)


def random_sleep(min_sleep, max_sleep):
    time.sleep(random.uniform(min_sleep, max_sleep))


def log(message, level):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    message = f"[{current_time}]: {message}"
    if level == 'ERR' or level == 'ERROR':
        cprint(colored(message, 'red', 'on_grey'))
        driver.quit()
        sys.exit(message)
    if level == 'DBG' or level == 'DEBUG':
        cprint(colored(f"[DEBUG]: {message}", 'grey', 'on_white', attrs=['dark']))
        return
    if level == 'INFO':
        cprint(colored(message, 'white', 'on_grey', attrs=['dark']))
        return
    if level == 'OK' or level == 'OKAY':
        cprint(colored(message, 'green', 'on_grey'))
        return
    if level == 'MAIN':
        cprint(colored(message, 'blue', 'on_grey', attrs=['bold']))
        return
    cprint(colored(f"[UNKNOWN]: {message}", 'magenta', 'on_grey'))


def wait_for(browser, element, delay):
    try:
        placeholder = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, element)))
    except Exception as ex:
        log(f"Waiting for {element} (not found)", "INFO")
    if DEBUG_MODE is True: log(f"Found {element}", "DEBUG")


def get_page_hash(browser):
    dom = browser.find_element_by_tag_name('html').get_attribute('innerHTML')
    # dom = driver.find_element_by_id('root').get_attribute('innerHTML')
    dom_hash = hash(dom.encode('utf-8'))
    return dom_hash


def logout(browser):
    if random.choice([True, False]) is True:
        if DEBUG_MODE is True: log("We will log out this time", "DEBUG")
        click_on(browser, M_XPATH_LOGOUT, 'xpath')
    log("Exiting browser", "INFO")
    browser.quit()
    sys.exit()


def has_page_loaded(browser, sleep_time=1):
    page_hash = 'empty'
    page_hash_new = ''
    while page_hash != page_hash_new:
        page_hash = get_page_hash(browser)
        time.sleep(sleep_time)
        page_hash_new = get_page_hash(browser)
        if DEBUG_MODE is True: log(f"Page not yet changed ({browser.current_url})", "DEBUG")
    if DEBUG_MODE is True: log(f"Page changed ({browser.current_url})", "DEBUG")


def click_on(browser, element, method):
    if method == 'selector':
        browser.find_element(By.CSS_SELECTOR, element).click()
    if method == 'xpath':
        browser.find_element(By.XPATH, element).click()


def check_exists(browser, element, method, delay=3):
    try:
        if method == 'selector':
            buffer = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, element)))
        if method == 'xpath':
            buffer = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, element)))
    except Exception as ex:
        if DEBUG_MODE is True: log(f"Element does not exist ({element})", "DEBUG")
        return False
    if DEBUG_MODE is True: log(f"Element exists ({element})", "DEBUG")
    return True


def random_scroll(browser):
    browser.execute_script(f"window.scrollTo(0, window.scrollY + {random.uniform(100, 200)})")


def is_working(browser):
    # TODO: Add a check for JS variable instead of html element.
    wait_for(browser, M_XPATH_DASHBOARD, DELAY_WAIT_FOR)
    counter = browser.find_element(By.XPATH, M_XPATH_WORK_COUNTER).text
    random_sleep(1.0, 1.5)
    counter_new = browser.find_element(By.XPATH, M_XPATH_WORK_COUNTER).text
    if counter_new != counter:
        log(f"Working ({counter_new})", "INFO")
        return
    else:
        log(f"Not working ({counter_new})", "INFO")
        return


def login(browser):
    browser.get(M_URL_DASHBOARD)
    # move_mouse_to_random_position(browser)
    random_sleep(1.1, 1.5)
    wait_for(browser, M_XPATH_USER, 5)
    randomize_window_size(browser)
    browser.find_element(By.XPATH, M_XPATH_USER).click()
    username = browser.find_element(By.XPATH, M_XPATH_USER)
    password = browser.find_element(By.XPATH, M_XPATH_PASSWORD)
    slow_type(username, M_USERNAME, random.uniform(0.01, 0.05))
    random_sleep(0.5, 0.8)
    slow_type(password, M_PASSWORD, random.uniform(0.02, 0.07))
    random_sleep(0.9, 1.1)
    click_on(browser, M_SELECTOR_LOGIN, 'selector')
    random_sleep(2, 3)
    # Stupid broken MFA - probably reCaptcha v3 detects us
    if check_exists(browser, M_XPATH_RECAPTCHA, 'xpath') is True or check_exists(browser, M_SELECTOR_RECAPTCHA, 'selector') is True:
        if DEBUG_MODE is True: log("Recaptcha detected", "DEBUG")
        # move_mouse_to_random_position(browser)
        random_scroll(browser)
        random_sleep(2, 3)
        click_on(browser, M_SELECTOR_RECAPTCHA, 'selector')
        click_on(browser, M_XPATH_LOGIN_2, 'xpath')
    # Sometimes it must be clicked twice
    if check_exists(browser, M_XPATH_DASHBOARD, 'xpath') is False:
        if DEBUG_MODE is True: log("Double login detected", "DEBUG")
        click_on(browser, M_SELECTOR_LOGIN, 'selector')

def randomize_window_size(browser):
    browser.set_window_size(random.uniform(900, 1400), random.uniform(600, 900))


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def prepare_browser():
    # TODO: Test if the agents are properly applied.
    if random.choice([True, False]) is True:
        if DEBUG_MODE is True: log("Firefox won", "DEBUG")
        options = FirefoxOptions()
        agent = get_random_agent('firefox')
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", agent)
        # options.add_argument(f'user-agent={agent}')
        geckodriver_autoinstaller.install()
        if RUN_HEADLESS is True:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')  
        return webdriver.Firefox(options=options)
    else:
        if DEBUG_MODE is True: log("Chromium won", "DEBUG")
        options = ChromeOptions()
        agent = get_random_agent('chrome')
        options.add_argument(f'user-agent={agent}')
        if RUN_HEADLESS is True:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')  
        return uc.Chrome(options=options)


def get_random_agent(browser):
    ua = UserAgent()
    if browser == 'firefox':
        return ua.firefox
    if browser == 'chrome':
        return ua.chrome


def move_mouse_to_random_position(browser):
    max_x, max_y = browser.execute_script("return [window.innerWidth, window.innerHeight];")
    body = browser.find_element_by_tag_name("body")
    actions = ActionChains(browser)
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)
    actions.move_to_element_with_offset(body, x, y)
    actions.perform()


def start_work(browser):
    login(browser)
    click_on(browser, M_XPATH_START, 'xpath')
    return True


def stop_work(browser):
    login(browser)
    click_on(browser, M_XPATH_STOP, 'xpath')
    return True


def test_start(test):
    log("start work", "INFO")


def test_stop(test):
    log("stop work", "INFO")


def load_employees(folder):
    return os.listdir(folder)


def refresh_employees():
    new_employees = load_employees('./employees')
    log("Refreshing employees", "INFO")
    for employee in new_employees:
        if employee not in current_employees:
            # Add new employee
            log(f"Adding {employee} to current employees.", "INFO")
            current_employees.append(employee)
    for old_employee in current_employees:
        if old_employee not in new_employees:
            # Remove deleted employee
            log(f"Removing {old_employee} from current employees.", "INFO")
            current_employees.remove(old_employee)
    log(f"Current employees: {current_employees}", "INFO")


################################
# Main
################################
log("Starting worker", "MAIN")
driver = prepare_browser()
scheduler = BlockingScheduler()
scheduler.add_job(start_work, trigger='cron', hour=WORK_STARTS, minute=WORK_STARTS_MINUTE, timezone=EMPLOYEE_TIMEZONE, jitter=RANDOM_START_MAX, args=[driver])
scheduler.add_job(stop_work, trigger='cron', hour=WORK_ENDS, minute=WORK_ENDS_MINUTE, timezone=EMPLOYEE_TIMEZONE, jitter=RANDOM_STOP_MAX,  args=[driver])
scheduler.add_job(refresh_employees, trigger='interval', seconds=10)
scheduler.start()
