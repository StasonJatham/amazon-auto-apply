import time
from argparse import ArgumentParser
from os.path import exists

import discord
import undetected_chromedriver as uc
from decouple import config
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


JOB_URL = "https://www.amazon.jobs/de/jobs/1926701/security-engineer-robot-detection"
AMAZON_EM = config('AMAZON_EM')
AMAZON_PW = config('AMAZON_PW')
DISC_KEY = config('DISC_KEY')
DISC_CHANNEL = int(config('DISC_CHANNEL'))
OTP_CODE = "+"


def main():
    driver = browser_options(True)
    amazon_otp(driver)


def amazon_otp(driver):
    path_to_file = "amazon/new.png"
    driver.get("https://account.amazon.jobs/de-DE/login?relay=%2Fde-DE")
    wait_until(driver, page_loaded=True)
    driver.find_element(By.ID, "btn-lwa-init").click()
    wait_until(driver, page_loaded=True)

    driver.find_element(By.ID, "ap_email").send_keys(AMAZON_EM)
    driver.find_element(By.ID, "ap_password").send_keys(AMAZON_PW)

    wait_until(
        driver=driver,
        js=f'document.querySelector("#ap_email").value == "{AMAZON_EM}" && document.querySelector("#ap_password").value == "{AMAZON_PW}"'
    )

    driver.find_element(By.ID, "signInSubmit").click()
    wait_until(driver, page_loaded=True)

    # amazon OTP
    element = driver.find_element(By.ID, "auth-mfa-form")
    element.screenshot(path_to_file)

    file_exists = exists(path_to_file)
    if file_exists:
        send_image_disc(path_to_file)
    else:
        time.sleep(3)
        send_image_disc(path_to_file)

    otp = OTP_CODE.replace("+", "").replace(" ", "")
    driver.find_element(By.ID, "auth-mfa-otpcode").send_keys(otp)
    wait_until(
        driver=driver,
        js=f'document.querySelector("#auth-mfa-otpcode").value == "{otp}"'
    )
    driver.find_element(By.ID, "auth-signin-button").click()
    wait_until(driver, page_loaded=True)
    driver.get(JOB_URL)
    wait_until(driver, page_loaded=True)
    driver.find_element(By.ID, "apply-button").click()
    wait_until(driver, page_loaded=True)
    wait_until(driver, url="apply")
    wait_until(driver, page_loaded=True)
    driver.find_element(
        By.CSS_SELECTOR, ".submit-application-button > button").click()
    wait_until(driver, page_loaded=True)


def send_image_disc(path):
    bot = discord.Bot()

    @bot.event
    async def on_ready():
        channel = bot.get_channel(DISC_CHANNEL)
        with open(path, mode='rb') as f:
            await channel.send(content="A new Captcha or OTP to solve.", file=discord.File(f))
        await channel.send(f"Please enter your OTP with a leading + like +123456")

    @bot.event
    async def on_message(message):
        channel = bot.get_channel(DISC_CHANNEL)
        if message.content.startswith("+") and bot.user != message.author:
            global OTP_CODE
            OTP_CODE = message.content
            await channel.send(f"Got your OTP code {OTP_CODE}, thanks.")
            await bot.close()
        if not message.content.startswith("+") and bot.user != message.author:
            await channel.send(f"Nope, please enter it starting with a + sign. Like +{message.content}")

    bot.run(DISC_KEY)


def browser_options(undetected=False):
    headless = True
    if options['show']:
        headless = False

    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
    else:
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)

    if undetected:
        driver = uc.Chrome(suppress_welcome=False)
    else:
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=chrome_options)

    return driver


def wait_until(driver, seconds=0, jquery="", js="", url="", title="", text="", button="", page_loaded=False, max_wait=30):

    def sleeper(timer):
        time.sleep(timer)
        return timer

    if page_loaded:
        timer = 0
        is_page_loaded = False
        while not is_page_loaded and timer < max_wait:
            is_page_loaded = driver.execute_script(
                'return document.readyState;')
            if is_page_loaded == "complete":
                return True
            timer += sleeper(1)
        raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if seconds:
        # wait for 'seconds' till continue
        time.sleep(seconds)
        return True

    if jquery:
        # wait till 'jquery' was executed succesfully
        is_on_page = False
        timer = 0
        while not is_on_page and timer < max_wait:
            is_on_page = driver.execute_script("""return """ + jquery)
            if is_on_page:
                return True
            timer += sleeper(1)

        raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if js:
        # wait till 'js' was executed succesfully
        is_on_page = False
        timer = 0
        while not is_on_page and timer < max_wait:
            is_on_page = driver.execute_script('return ' + js)
            if is_on_page:
                return True
            timer += sleeper(1)

        raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if url:
        # wait till certain 'url' is the current url or if part of the url is 'url'
        # - for example you can pass "login", if "login" is in url then continue
        is_new_page = False
        is_current_page = False
        timer = 0
        if url.startswith("not_"):
            url = url.split("not_")[1]
            while not is_new_page and timer < max_wait:
                if url not in driver.current_url:
                    is_new_page = True
                timer += sleeper(1)
        else:
            while not is_current_page and timer < max_wait:
                if url in driver.current_url:
                    is_current_page = True
                timer += sleeper(1)

        if is_new_page or is_current_page:
            return True
        else:
            raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if title:
        # if the title of the website is "title" or includes "title"
        is_new_title = False
        is_current_title = False
        timer = 0
        if title.startswith("not_"):
            title = title.split("not_")[1]
            while not is_new_title and timer < max_wait:
                if title not in driver.title:
                    is_new_title = True
                timer += sleeper(1)
        else:
            while not is_current_title and timer < max_wait:
                if title in driver.title:
                    is_current_title = True
                timer += sleeper(1)

        if is_new_title or is_current_title:
            return True
        else:
            raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if text:
        # is visible on page, this has to be an exact match
        is_text_on_page = False
        timer = 0
        while not is_text_on_page and timer < max_wait:
            try:
                try:
                    is_text_on_page = driver.execute_script(
                        f"return (document.documentElement.textContent || document.documentElement.innerText).indexOf('{text}') > -1")
                except Exception as e:
                    is_text_on_page = driver.execute_script(
                        f"return document.body.innerHTML.search('{text}') > -1")
            except Exception as e:
                if text in driver.page_source:
                    is_text_on_page = True
            timer += sleeper(1)

        if is_text_on_page:
            return True
        else:
            raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')

    if button:
        # check if button is visible on page
        is_on_page = False
        timer = 0
        while not is_on_page and timer < max_wait:
            if button.startswith("css_"):
                button_css_selector = button.split("css_")[1]
                try:
                    is_on_page = driver.find_element(
                        By.CSS_SELECTOR, button_css_selector)
                except Exception as e:
                    is_on_page = driver.find_element_by_css_selector(
                        button_css_selector)

            elif button.startswith("xpath_"):
                button_xpath_selector = button.split("xpath_")[1]
                try:
                    #driver.find_element(By.XPATH, "//*[contains(text(), 'My Button')]")
                    is_on_page = driver.find_element(
                        By.XPATH, button_xpath_selector)
                except Exception as e:
                    is_on_page = driver.find_element_by_xpath(
                        button_xpath_selector)
            else:
                is_on_page = driver.execute_script(button)

            timer += sleeper(1)

        if is_on_page:
            return True
        else:
            raise TimeoutError(f'Max wait of {max_wait} seconds, exceeded.')


if __name__ == '__main__':
    my_parser = ArgumentParser()
    my_parser.add_argument('-s', '--show',
                           action='store_true',
                           help='Show browser. Default is headless.')

    options = my_parser.parse_args()
    options = vars(options)

    main()
