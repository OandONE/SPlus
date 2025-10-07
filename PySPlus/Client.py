from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from .colors import *
from .async_sync import *
from typing import Optional,Literal
from traceback import format_exc
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
                is_login = self.login()
                if not is_login:
                    print("Error Login !")
                    exit()
            # text_json_py_slpus_session = {
            #     "name_session": name_session,
            #     "number_phone":number_phone,
            #     "user_agent": user_agent,
            #     "time_out": time_out,
            #     "display_welcome": display_welcome,
            # }
            # with open(name, "w", encoding="utf-8") as file:
            #     json.dump(
            #         text_json_py_slpus_session, file, ensure_ascii=False, indent=4
            #     )
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
    @async_to_sync
    async def login(self) -> bool:
        """لاگین / login"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=fa")
        chrome_options.add_experimental_option("detach", True)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(self.driver, 30)
        try:
            self.driver.get("https://web.splus.ir")
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(1)
            is_open_cookies = False
            if os.path.exists(self.name_cookies):
                with open(self.name_cookies, 'rb') as file:
                    cookies = pickle.load(file)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                        is_open_cookies = True
            if is_open_cookies:
                self.driver.refresh()
            try:
                understand_button = WebDriverWait(self.driver, 3).until(
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
            self.code_html = self.driver.page_source
            code_input.clear()
            code_input.send_keys(verification_code)
            time.sleep(5)
            self.code_html = self.driver.page_source
            messages = await self.get_chat_ids()
            while not messages:
                time.sleep(1)
                self.code_html = self.driver.page_source
                messages = await self.get_chat_ids()
            with open(self.name_cookies, 'wb') as file:
                pickle.dump(self.driver.get_cookies(), file)
            return True
        except Exception as e:
            print("/*-+123456789*-+")
            print(format_exc())
            print("123456789*-+")
            self.driver.save_screenshot("error_screenshot.png")
            print("ERROR :")
            print(e)
            print("ERROR SAVED : error_screenshot.png")
            return False

    @async_to_sync
    async def get_type_chat_id(
        self,
        chat_id:str
    ) -> Literal["Channel","Group","Bot","User",None]:
        """getting chat id type / گرفتن نوع چت آیدی"""
        if chat_id.startswith("-"):
            if len(chat_id) == 11:
                return "Channel"
            elif len(chat_id) == 12:
                return "Group"
        if len(chat_id) == 6:
            return "User"
        elif len(chat_id) == 8:
            return "Bot"
        return None

    @async_to_sync
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
        return chats

    @async_to_sync
    async def get_chats(self) -> list:
        """گرفتن چت ها / getting chats"""
        soup = BeautifulSoup(self.code_html, "html.parser")
        root = soup.select_one(
            "body > #UiLoader > div.Transition.full-height > "
            "#Main.left-column-shown.left-column-open > "
            "#LeftColumn > #LeftColumn-main > div.Transition > "
            "div.ChatFolders.not-open.not-shown > div.Transition > "
            "div.chat-list.custom-scroll > div[style*='position: relative']"
        )
        chats_ = []
        chats = []
        if root:
            divs = root.find_all("div", recursive=True)
            for div in divs:
                anchors = div.find_all("a", href=True)
                for a in anchors:
                    if a!=None:
                        chat = str(a["href"]).replace("#","")
                        chats_.append(chat)
        for chat in chats_:
            type_chat = await self.get_type_chat_id(chat)
            chats.append({
                "chat_id":chat,
                "type_chat":type_chat
            })
        return chats

    @async_to_sync
    async def open_chat(self, chat_id: str) -> bool:
        """opening chat / باز کردن چت"""
        try:
            self.driver.get("https://web.splus.ir")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-list, div[role='main']"))
            )
            chat_link = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[href="#{chat_id}"]'))
            )
            chat_link.click()
            print(f"✅ Chat {chat_id} opened.")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            return True
        except Exception as e:
            print("❌ Error in open_chat : ", e)
            self.driver.save_screenshot("open_chat_error.png")
            return False

    @async_to_sync
    async def send_text(self, chat_id: str, text: str) -> bool:
        """ارسال متن / sending text"""
        try:
            await self.open_chat(chat_id)
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            input_box = self.driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            self.driver.execute_script("""
                arguments[0].innerText = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """, input_box, text)
            send_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "button.Button.send.main-button.default.secondary.round.click-allowed"
                ))
            )
            send_button.click()
            print("✅ Message sent successfully.")
            return True
        except Exception as e:
            print(f"❌ Error in send_text : {e}")
            self.driver.save_screenshot("send_text_error.png")
            return False
