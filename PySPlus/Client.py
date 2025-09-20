from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from .colors import *
from typing import Optional
import time,os,json,asyncio,logging,pickle

logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)

os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

class Client:
    def __init__(self,
        name_session: str,
        display_welcome=True,
        user_agent: Optional[str] = None,
        time_out: Optional[int] = 60,
        number_phone: Optional[str] = None
    ):
        self.number_phone = number_phone
        name = name_session + ".pysplus"
        self.name_cookies = name_session + "_cookies.pkl"
        if os.path.isfile(name):
            with open(name, "r", encoding="utf-8") as file:
                text_json_py_slpus_session = json.load(file)
                self.number_phone = text_json_py_slpus_session["number_phone"]
                self.time_out = text_json_py_slpus_session["time_out"]
                self.user_agent = text_json_py_slpus_session["user_agent"]
                self.display_welcome = text_json_py_slpus_session["display_welcome"]
                asyncio.run(self.login())
        else:
            if not number_phone:
                number_phone = input("Enter your phone number : ")
                if number_phone.startswith("0"):
                    number_phone = number_phone[1:]
                while number_phone in ["", " ", None] or self.check_phone_number(number_phone)==False:
                    cprint("Enter the phone valid !",Colors.RED)
                    number_phone = input("Enter your phone number : ")
                    if number_phone.startswith("0"):
                        number_phone = number_phone[1:]
                is_login = asyncio.run(self.login())
                if not is_login:
                    print("Error Login !")
                    exit()
            text_json_py_slpus_session = {
                "name_session": name_session,
                "number_phone":number_phone,
                "user_agent": user_agent,
                "time_out": time_out,
                "display_welcome": display_welcome,
            }
            with open(name, "w", encoding="utf-8") as file:
                json.dump(
                    text_json_py_slpus_session, file, ensure_ascii=False, indent=4
                )
            self.time_out = time_out
            self.user_agent = user_agent
            self.number_phone = number_phone
            if display_welcome:
                k = ""
                for text in "Welcome to PySPlus":
                    k += text
                    print(f"{Colors.GREEN}{k}{Colors.RESET}", end="\r")
                    time.sleep(0.07)
                cprint("",Colors.WHITE)
    def check_phone_number(self,number:str) -> bool:
        if len(number)!=10:
            return False
        if not number.startswith("9"):
            return False
        return True
    async def login(self) -> bool:
        """لاگین / login"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=fa")
        chrome_options.add_experimental_option("detach", True)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        try:
            driver.get("https://web.splus.ir")
            time.sleep(1)
            is_open_cookies = False
            if os.path.exists(self.name_cookies):
                with open(self.name_cookies, 'rb') as file:
                    cookies = pickle.load(file)
                    for cookie in cookies:
                        driver.add_cookie(cookie)
                        is_open_cookies = True
            if is_open_cookies:
                driver.refresh()
            try:
                understand_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'متوجه شدم')]"))
                )
                understand_button.click()
                time.sleep(1)
            except:
                pass
            phone_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#sign-in-phone-number"))
            )
            phone_input.clear()
            phone_number = f"98 98{self.number_phone}"
            phone_input.send_keys(phone_number)
            next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'Button') and contains(text(), 'بعدی')]"))
            )
            next_button.click()
            time.sleep(5)
            verification_code = input("Enter the Code » ")
            code_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#sign-in-code"))
            )
            self.code_html = driver.page_source
            code_input.clear()
            code_input.send_keys(verification_code)
            time.sleep(5)
            self.code_html = driver.page_source
            messages = await self.get_chat_ids()
            while not messages:
                time.sleep(1)
                self.code_html = driver.page_source
                messages = await self.get_chat_ids()
            with open(self.name_cookies, 'wb') as file:
                pickle.dump(driver.get_cookies(), file)
            return True
        except Exception as e:
            driver.save_screenshot("error_screenshot.png")
            print("ERROR :")
            print(e)
            print("ERROR SAVED : error_screenshot.png")
            return False
    async def get_chat_ids(self) -> list:
        """گرفتن چت آیدی ها / getting chat ids"""
        soup = BeautifulSoup(self.code_html, "html.parser")
        root = soup.select_one(
            "body > #UiLoader > div.Transition.full-height > "
            "#Main.left-column-shown.left-column-open > "
            "#LeftColumn > #LeftColumn-main > div.Transition > "
            "div.ChatFolders.not-open.not-shown > div.Transition > "
            "div.chat-list.custom-scroll > div[style*='position: relative']"
        )
        chats = []
        if root:
            divs = root.find_all("div", recursive=True)
            for div in divs:
                anchors = div.find_all("a", href=True)
                for a in anchors:
                    if a!=None:
                        chat = str(a["href"]).replace("#","")
                        chats.append(chat)
        else:
            print("❌ تگ ریشه پیدا نشد!")
        return chats
    async def send_text(self,chat_id:str,text:str) -> bool:
        """ارسال متن / sending text"""
        try:
            self.driver.get(f"https://web.splus.ir/#{chat_id}")
            time.sleep(3)
            input_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-message-input"))
            )
            input_box.click()
            input_box.send_keys(text)
            send_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.Button.send"))
            )
            send_button.click()
            return True
        except Exception as e:
            print("Error in send_text:", e)
            return False
