from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from bs4 import BeautifulSoup
from .colors import *
from .async_sync import *
from typing import (
    Optional,
    Literal,
    Awaitable,
    Callable
)
import time
import os
import json
import logging
import pickle
import re
import base64
from .props import props
from .Update import Update
import inspect

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
        number_phone: Optional[str] = None,
        viewing_browser: Optional[bool] = False
    ):
        self.number_phone = number_phone
        name = name_session + ".pysplus"
        self.name_cookies = name_session + "_cookies.pkl"
        self.viewing_browser = viewing_browser
        self.splus_url = "https://web.splus.ir"
        self.me = {}
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
            self.messages_handlers = []
            self.running = False
            self.list_ = []
            self.message_handlers = []
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
        if not self.viewing_browser:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=fa")
        chrome_options.add_experimental_option("detach", True)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(self.driver, 30)
        try:
            self.driver.get(self.splus_url)
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
            self.driver.save_screenshot("error_screenshot.png")
            print("ERROR :")
            print(e)
            print("ERROR SAVED : error_screenshot.png")
            return False

    @async_to_sync
    async def get_url_opened(self) -> str:
        return self.driver.current_url

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
    async def get_chat_ids(self) -> props:
        """گرفتن چت آیدی ها / getting chat ids"""
        url_opened = await self.get_url_opened()
        if not url_opened == self.splus_url+"/":
            self.driver.get(self.splus_url)
        self.code_html = self.driver.page_source
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
        return props(chats)

    @async_to_sync
    async def get_chats(self) -> props:
        """گرفتن چت ها / getting chats"""
        try:
            url_opened = await self.get_url_opened()
            if not url_opened == self.splus_url+"/":
                self.driver.get(self.splus_url)
        except Exception:
            pass
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-list.custom-scroll"))
            )
        except Exception:
            pass
        items = self.driver.find_elements(By.CSS_SELECTOR, "div.ListItem.Chat")
        def js_avatar_src(el):
            js = r"""
            return (function(root){
                // تلاش از <img>
                var img = root.querySelector('img.Avatar__media, img.avatar-media, .Avatar img, .avatar img, picture img');
                var src = '';
                if (img){
                    src = img.getAttribute('src') || img.currentSrc || img.getAttribute('data-src') || '';
                    if (!src){
                        var ss = img.getAttribute('srcset') || '';
                        if (ss){
                            src = ss.split(',')[0].trim().split(' ')[0].trim();
                        }
                    }
                }
                // اگر نبود، از background-image روی .Avatar
                if (!src){
                    var av = root.querySelector('.Avatar, .avatar, .avatar-badge-wrapper');
                    if (av){
                        var st = getComputedStyle(av);
                        var bg = (st && st.backgroundImage) || '';
                        if (bg && bg.startsWith('url(')){
                            src = bg.slice(4, -1).replace(/^["']|["']$/g,'');
                        }
                    }
                }
                return src || '';
            })(arguments[0]);
            """
            try:
                return (self.driver.execute_script(js, el) or "").strip()
            except Exception:
                return ""
        results = []
        default_icon_hint = "/person_icon."
        for el in items:
            try:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'nearest'});", el)
                except Exception:
                    pass
                chat_id = ""
                try:
                    a = el.find_element(By.CSS_SELECTOR, "a.ListItem-button")
                    href = (a.get_attribute("href") or "")
                    m = re.search(r"#(\d+)", href)
                    if m: chat_id = m.group(1)
                except Exception:
                    pass
                if not chat_id:
                    try:
                        peer = el.find_element(By.CSS_SELECTOR, "[data-peer-id]")
                        chat_id = (peer.get_attribute("data-peer-id") or "").strip()
                    except Exception:
                        chat_id = ""
                try:
                    name = el.find_element(By.CSS_SELECTOR, "h3.fullName").text.strip()
                except Exception:
                    name = ""
                try:
                    time_txt = el.find_element(By.CSS_SELECTOR, "span.time").text.strip()
                except Exception:
                    time_txt = ""
                last_message = ""
                try:
                    sub_html = self.driver.execute_script(
                        "var x=arguments[0].querySelector('.subtitle, p.last-message'); return x? x.innerHTML: '';",
                        el
                    ) or ""
                    soup = BeautifulSoup(sub_html, "html.parser")
                    for sp in soup.select("span.Spoiler__content"):
                        sp_text = sp.get_text()
                        sp.replace_with(f"||{sp_text}||")
                    last_message = soup.get_text(" ", strip=True)
                except Exception:
                    try:
                        last_message = el.find_element(By.CSS_SELECTOR, ".subtitle, p.last-message").text.strip()
                    except Exception:
                        last_message = ""
                avatar_src = js_avatar_src(el)
                if avatar_src and default_icon_hint in avatar_src:
                    try:
                        WebDriverWait(self.driver, 0.7).until(
                            lambda d: (("blob:" in js_avatar_src(el)) or (default_icon_hint not in js_avatar_src(el)))
                        )
                        avatar_src = js_avatar_src(el)
                    except Exception:
                        if default_icon_hint in (avatar_src or ""):
                            avatar_src = None
                        if not str(avatar_src).startswith("blob:"):
                            avatar_src = None
                type_chat = await self.get_type_chat_id(chat_id)
                results.append({
                    "chat_id": chat_id,
                    "name": name,
                    "last_message": {
                        "text":last_message,
                        "time":time_txt
                    },
                    "avatar_src": avatar_src,
                    "type_chat":type_chat
                })
            except Exception as e:
                try:
                    print("get_chats avatar parse error : ", e)
                except:
                    pass
        return props(results)

    @async_to_sync
    async def download_blob_image(self, blob_url: str, dest_path: str) -> bool:
        """download avatar / دانلود آواتور"""
        try:
            js = """
            var url = arguments[0];
            var cb  = arguments[arguments.length - 1];
            try {
                var img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = function(){
                    try {
                        var canvas = document.createElement('canvas');
                        canvas.width  = this.naturalWidth  || this.width  || 0;
                        canvas.height = this.naturalHeight || this.height || 0;
                        var ctx = canvas.getContext('2d');
                        ctx.drawImage(this, 0, 0);
                        var data = canvas.toDataURL('image/png').split(',')[1];
                        cb(data);
                    } catch(e) { cb(null); }
                };
                img.onerror = function(){ cb(null); };
                img.src = url;
            } catch(e) { cb(null); }
            """
            b64 = self.driver.execute_async_script(js, blob_url)
            if not b64:
                return False
            data = base64.b64decode(b64)
            with open(dest_path, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            try:
                print("download_blob_image error : ", e)
            except:
                pass
            return False

    @async_to_sync
    async def open_chat(self, chat_id: str) -> bool:
        """opening chat / باز کردن چت"""
        try:
            current = await self.get_url_opened()
            if current == f"{self.splus_url}/#{chat_id}":
                print(f"✅ Chat {chat_id} opened.")
                return True
            if not current == self.splus_url+"/":
                self.driver.get(self.splus_url)
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
    async def send_text(self, chat_id: str, text: str,reply_message_id: Optional[str] = None) -> bool:
        """ارسال متن / sending text"""
        try:
            await self.open_chat(chat_id)
            if reply_message_id:
                await self.context_click_message(reply_message_id, menu_text="پاسخ")
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

    @async_to_sync
    async def get_chat(
        self,
        chat_id: str
    ):
        """getting messages chat / گرفتن پیام های چت"""
        opening = await self.open_chat(chat_id)
        type_chat = await self.get_type_chat_id(chat_id)
        peer_name = None
        peer_status = None
        peer_avatar = None
        peer_verified = False
        if not opening:
            return {
                    "messages":[],
                    "chat":{
                        "name": peer_name,
                        "avatar_src": peer_avatar,
                        "last_seen": peer_status,
                        "verified": peer_verified,
                        "type": type_chat
                    }
                }
        try:
            header_el = WebDriverWait(self.driver, 5).until(
                lambda d: d.find_element(By.CSS_SELECTOR, ".ChatInfo")
            )
            header_html = self.driver.execute_script("return arguments[0].outerHTML;", header_el)
            hsoup = BeautifulSoup(header_html, "html.parser")
            name_tag = hsoup.select_one(".fullName, .title h3, .info h3")
            if name_tag:
                peer_name = name_tag.get_text(strip=True)
            status_tag = hsoup.select_one(".user-status, .status, .info .status")
            if status_tag:
                peer_status = status_tag.get_text(" ", strip=True)
            if hsoup.select_one("svg.VerifiedIcon"):
                peer_verified = True
            try:
                avatar_src = self.driver.execute_script("""
                    var root = arguments[0];
                    var img = root.querySelector('.Avatar__media, .avatar-media, .Avatar img, .avatar img, picture img');
                    if (img) {
                        var s = img.getAttribute('src') || img.currentSrc || img.getAttribute('data-src') || '';
                        if (s) return s;
                    }
                    var av = root.querySelector('.Avatar, .avatar, .Avatar.size-medium, .Avatar.size-large');
                    if (av) {
                        var st = getComputedStyle(av);
                        var bg = st && st.backgroundImage || '';
                        if (bg && bg.indexOf('url(') === 0) {
                            return bg.slice(4, -1).replace(/^['"]|['"]$/g,'');
                        }
                    }
                    return '';
                """, header_el) or ""
                peer_avatar = avatar_src or None
            except Exception:
                peer_avatar = None
        except Exception:
            pass
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".messages-container"))
            )
        except Exception:
            pass
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Message, .message-list-item"))
            )
        except Exception:
            pass
        try:
            script_scroll = """
            (function(){
                var el = document.querySelector('.messages-container');
                if(!el) return false;
                el.scrollTop = el.scrollHeight;
                return true;
            })();
            """
            for _ in range(3):
                try:
                    self.driver.execute_script(script_scroll)
                    time.sleep(0.35)
                except Exception:
                    break
        except Exception:
            pass
        time.sleep(0.5)
        try:
            container_el = self.driver.find_element(By.CSS_SELECTOR, ".messages-container")
            html_fragment = self.driver.execute_script("return arguments[0].innerHTML;", container_el)
            html_string = f'<div class="messages-container">{html_fragment}</div>'
        except Exception:
            html_string = self.driver.page_source
        def normalize_lines(text):
            lines = [ln.strip() for ln in text.splitlines()]
            lines = [ln for ln in lines if ln]
            return "\n".join(lines)
        def extract_text_from_textcontent(text_div):
            if text_div is None:
                return ""
            for meta in text_div.select(".MessageMeta"):
                meta.extract()
            raw = text_div.get_text("\n", strip=True)
            return normalize_lines(raw)
        def _persian_digits_to_ascii(s: str) -> str:
            if not s:
                return s
            persian_offset = {ord(c): ord('0') + i for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}
            arabic_offset = {ord(c): ord('0') + i for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
            table = {}
            table.update(persian_offset)
            table.update(arabic_offset)
            return s.translate(table)
        def parse_message_tag(msg_tag, sticky_text=None):
            time_span = msg_tag.select_one(".message-time")
            time_sent = None
            full_date = None
            if time_span:
                title = time_span.get("title") or ""
                title = title.strip()
                if title:
                    title_ascii = _persian_digits_to_ascii(title)
                    if "،" in title_ascii:
                        parts = [p.strip() for p in title_ascii.split("،") if p.strip()]
                    else:
                        parts = [p.strip() for p in title_ascii.split(",") if p.strip()]
                    if len(parts) >= 2:
                        date_part = "، ".join(parts[:-1]) if len(parts) > 2 else parts[0]
                        time_part = parts[-1]
                        full_date = title_ascii
                        time_sent = time_part
                    else:
                        full_date = title_ascii
                        import re
                        m = re.search(r'(\d{1,2}[:\:\uFF1A]\d{2}(?::\d{2})?)', title_ascii)
                        if m:
                            time_sent = m.group(1).replace("\uFF1A", ":")
                else:
                    txt = time_span.get_text(strip=True)
                    txt_ascii = _persian_digits_to_ascii(txt)
                    if ":" in txt_ascii:
                        parts = txt_ascii.split(":")
                        if len(parts) == 2:
                            time_sent = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
                        else:
                            time_sent = txt_ascii
                    else:
                        time_sent = txt_ascii
            text_div = msg_tag.select_one(".text-content")
            if text_div is None:
                text_div = msg_tag.select_one(".content-inner")
            cleaned = extract_text_from_textcontent(text_div)
            classes = msg_tag.get("class", []) or []
            own_flag = False
            if "own" in classes:
                own_flag = True
            if msg_tag.select_one(".with-outgoing-icon") or msg_tag.select_one(".MessageOutgoingStatus") or msg_tag.select_one(".MessageOutgoingStatus .icon-message-succeeded"):
                own_flag = True
            summary = cleaned.replace("\n", " ")
            if len(summary) > 160:
                summary = summary[:157].rstrip() + "..."
            return {
                "message_id": msg_tag.get("id").replace("message", "") if msg_tag.get("id") else None,
                "day": sticky_text,
                "date": full_date,
                "time": time_sent,
                "is_me": bool(own_flag),
                "text": cleaned,
                "summary": summary,
                "classes": classes
            }

        soup = BeautifulSoup(html_string, "html.parser")
        container = soup.select_one(".messages-container") or soup
        sticky_current = None
        collected = []
        seen_ids = set()
        for d in container.find_all("div", recursive=True):
            d_classes = d.get("class") or []
            if "sticky-date" in d_classes:
                txt = d.get_text(" ", strip=True)
                sticky_current = txt if txt else sticky_current
                continue
            is_msg = False
            for token in ("Message", "message-list-item"):
                if token in d_classes:
                    is_msg = True
                    break
            if is_msg:
                mid = d.get("id")
                if mid and mid in seen_ids:
                    continue
                parsed = parse_message_tag(d, sticky_text=sticky_current)
                collected.append(parsed)
                if mid:
                    seen_ids.add(mid)
        collected.reverse()
        return {
                "messages":collected,
                "chat":{
                    "name": peer_name,
                    "avatar_src": peer_avatar,
                    "last_seen": peer_status,
                    "verified": peer_verified,
                    "type": type_chat
                }
            }

    @async_to_sync
    async def get_chat_id_by_username(self, username: str) -> Optional[str]:
        """get chat id by username / گرفتن چت آیدی با نام کاربری"""
        try:
            if username.startswith('@'):
                username = username[1:]
            print(f"🔍 جستجوی چت آیدی برای: {username}")
            current_url = await self.get_url_opened()
            if not current_url == self.splus_url + "/":
                self.driver.get(self.splus_url)
                time.sleep(3)
            try:
                script = f"""
                try {{
                    // تلاش برای تغییر مسیر به چت با نام کاربری
                    window.location.hash = 'im?p=@{username}';
                    return true;
                }} catch(e) {{
                    return false;
                }}
                """
                result = self.driver.execute_script(script)
                time.sleep(5)
                current_url = self.driver.current_url
                print(f"📎 URL پس از جاوااسکریپت: {current_url}")
                import re
                match = re.search(r'#(\d+)', current_url)
                if match:
                    chat_id = match.group(1)
                    if chat_id and chat_id != "777000":
                        print(f"✅ چت آیدی پیدا شد: {chat_id}")
                        return chat_id
            except Exception as e:
                print(f"⚠️ خطا در جاوااسکریپت: {e}")
            try:
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        ".icon-search, " +
                        "[aria-label*='جستجو'], " +
                        "button[title*='جستجو']"
                    ))
                )
                search_button.click()
                time.sleep(2)
                search_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "input[placeholder*='جستجو'], " +
                        "input[type='search']"
                    ))
                )
                search_input.clear()
                search_input.send_keys(f"@{username}")
                time.sleep(3)
                time.sleep(3)
                try:
                    user_result = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            f"//div[contains(@class, 'ListItem') and contains(., '@{username}')] | " +
                            f"//div[contains(@class, 'Chat') and contains(., '@{username}')]"
                        ))
                    )
                    user_result.click()
                    time.sleep(5)
                    current_url = self.driver.current_url
                    import re
                    match = re.search(r'#(\d+)', current_url)
                    if match:
                        chat_id = match.group(1)
                        if chat_id and chat_id != "777000":
                            print(f"✅ چت آیدی (از جستجو) پیدا شد: {chat_id}")
                            return chat_id
                except Exception as e:
                    print(f"⚠️ خطا در کلیک روی نتیجه جستجو: {e}")
            except Exception as e:
                print(f"⚠️ خطا در جستجو: {e}")
            try:
                url = f"{self.splus_url}/#im?p=@{username}"
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.current_url != self.splus_url + "/"
                )
                time.sleep(5)
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-peer-id]")
                    for element in elements:
                        peer_id = element.get_attribute("data-peer-id")
                        if peer_id and peer_id != "777000" and len(peer_id) >= 6:
                            print(f"✅ چت آیدی از data-peer-id: {peer_id}")
                            return peer_id
                except:
                    pass
            except Exception as e:
                print(f"⚠️ خطا در روش URL مستقیم: {e}")
            print("❌ چت آیدی پیدا نشد")
            return None
        except Exception as e:
            print(f"❌ خطا در get_chat_id_by_username: {e}")
            import traceback
            traceback.print_exc()
            return None

    @async_to_sync
    async def get_me(self) -> dict:
        """دریافت اطلاعات حساب کاربر / Get my account info"""
        try:
            current_url = await self.get_url_opened()
            if not current_url == self.splus_url + "/":
                self.driver.get(self.splus_url)
                time.sleep(3)
            try:
                account_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(., 'حساب من')]"))
                )
                account_tab.click()
                time.sleep(2)
                print("✅ 'حساب من' کلیک شد")
            except Exception as e:
                print(f"⚠️ خطا در کلیک روی 'حساب من': {e}")
                return {"error": "نمیتوان به حساب کاربری دسترسی پیدا کرد"}
            try:
                settings_xpath = "//div[contains(@class, 'ListItem-button') and .//i[contains(@class, 'icon-settings')] and contains(., 'تنظیمات')]"
                settings_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, settings_xpath))
                )
                settings_option.click()
                time.sleep(3)
                print("✅ 'تنظیمات' کلیک شد")
            except Exception as e:
                print(f"⚠️ خطا در کلیک روی 'تنظیمات': {e}")
                return {"error": "نمیتوان به تنظیمات دسترسی پیدا کرد"}
            result = {
                "phone_number": None,
                "username": None,
                "bio": None,
                "user_id": None,
                "full_name": None
            }
            try:
                name_elements = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.fullName, .fullName, .title, h1.title"))
                )
                for element in name_elements:
                    text = element.text.strip()
                    if text and len(text) > 0 and not text.startswith("+"):
                        result["full_name"] = text
                        print(f"✅ نام کامل: {text}")
                        break
            except Exception as e:
                print(f"⚠️ خطا در گرفتن نام: {e}")
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, "html.parser")
            try:
                phone_spans = soup.find_all("span", class_="subtitle", string=lambda t: t and "شماره تلفن" in str(t))
                for span in phone_spans:
                    title_span = span.find_previous_sibling("span", class_="title")
                    if title_span:
                        phone_text = title_span.get_text(strip=True)
                        import re
                        phone_digits = re.sub(r'\D', '', phone_text)
                        if phone_digits.startswith('98'):
                            phone_digits = '0' + phone_digits[2:]
                        result["phone_number"] = phone_digits
                        print(f"✅ شماره تلفن: {result['phone_number']}")
                        break
            except Exception as e:
                print(f"⚠️ خطا در گرفتن شماره تلفن: {e}")
            try:
                username_spans = soup.find_all("span", class_="subtitle", string=lambda t: t and "نام کاربری" in str(t))
                for span in username_spans:
                    title_span = span.find_previous_sibling("span", class_="title")
                    if title_span:
                        username = title_span.get_text(strip=True)
                        if username and not username.startswith("+"):
                            result["username"] = username
                            print(f"✅ نام کاربری: {result['username']}")
                            break
            except Exception as e:
                print(f"⚠️ خطا در گرفتن نام کاربری: {e}")
            try:
                bio_spans = soup.find_all("span", class_="subtitle", string=lambda t: t and "بیوگرافی" in str(t))
                for span in bio_spans:
                    title_span = span.find_previous_sibling("span", class_="title")
                    if title_span:
                        result["bio"] = title_span.get_text(strip=True)
                        print(f"✅ بیوگرافی: {result['bio'][:50]}..." if result['bio'] and len(result['bio']) > 50 else f"✅ بیوگرافی: {result['bio']}")
                        break
            except Exception as e:
                print(f"⚠️ خطا در گرفتن بیوگرافی: {e}")
            print("🔍 گرفتن user_id از طریق پیام‌های ذخیره شده...")
            self.driver.get(self.splus_url)
            time.sleep(3)
            try:
                account_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tab') and contains(., 'حساب من')]"))
                )
                account_tab.click()
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ خطا در کلیک روی 'حساب من': {e}")
            try:
                saved_messages = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//div[contains(@class, 'ListItem-button') and contains(., 'پیام‌های ذخیره شده')]"
                    ))
                )
                saved_messages.click()
                time.sleep(5)
                current_url = self.driver.current_url
                import re
                match = re.search(r'#(\d+)', current_url)
                if match:
                    chat_id = match.group(1)
                    if chat_id and chat_id != "777000":  # حذف چت سیستمی
                        result["user_id"] = chat_id
                        print(f"✅ چت آیدی (از پیام ذخیره شده): {result['user_id']}")
                    else:
                        print("⚠️ چت آیدی سیستمی است، نادیده گرفته می‌شود")
                else:
                    print("❌ چت آیدی در URL پیدا نشد")
            except Exception as e:
                print(f"⚠️ خطا در کلیک روی پیام‌های ذخیره شده: {e}")
            self.driver.get(self.splus_url)
            time.sleep(2)
            print("✅ اطلاعات حساب کاربر با موفقیت دریافت شد")
            self.me = result
            return result
        except Exception as e:
            print(f"❌ خطا در get_me: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.get(self.splus_url)
            except:
                pass
            return {
                "phone_number": None,
                "username": None,
                "bio": None,
                "user_id": None,
                "full_name": None,
                "error": str(e)
            }

    @async_to_sync
    async def validate_invite_link(self, link: str) -> dict:
        """بررسی اعتبار لینک دعوت"""
        result = {
            "valid": False,
            "type": None,
            "title": None,
            "members_count": None
        }
        try:
            import re
            if "splus.ir" not in link:
                return result
            original_window = self.driver.current_window_handle
            self.driver.execute_script(f"window.open('{link}', '_blank');")
            time.sleep(3)
            windows = self.driver.window_handles
            if len(windows) > 1:
                self.driver.switch_to.window(windows[-1])
                time.sleep(5)
                page_html = self.driver.page_source
                if "گروه" in page_html or "group" in page_html.lower():
                    result["type"] = "group"
                elif "کانال" in page_html or "channel" in page_html.lower():
                    result["type"] = "channel"
                try:
                    title_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "h1, h2, h3, .title, .dialog-title, .group-title, .channel-title"
                    )
                    for element in title_elements:
                        text = element.text.strip()
                        if text and len(text) > 0:
                            result["title"] = text
                            break
                except:
                    pass
                try:
                    members_texts = self.driver.find_elements(By.XPATH,
                        "//*[contains(text(), 'عض') or contains(text(), 'member') or contains(text(), 'subscriber')]"
                    )
                    for element in members_texts:
                        text = element.text.strip()
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            result["members_count"] = int(''.join(numbers))
                            break
                except:
                    pass
                result["valid"] = True
                self.driver.close()
                self.driver.switch_to.window(original_window)
            return result
        except Exception as e:
            print(f"⚠️ خطا در بررسی لینک: {e}")
            try:
                windows = self.driver.window_handles
                if len(windows) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
            except:
                pass
            return result

    @async_to_sync
    async def join(self, link: str) -> bool:
        """join to group/channel from link / پیوستن به گروه/کانال از طریق لینک دعوت"""
        try:
            if not self.me:
                print("📋 اطلاعات کاربر موجود نیست، در حال دریافت...")
                await self.get_me()
            if not self.me or not self.me.get("user_id"):
                print("❌ اطلاعات کاربر دریافت نشد")
                return False
            user_id = self.me["user_id"]
            print("📤 ارسال لینک به پیام‌های ذخیره شده...")
            success = await self.send_text(user_id, link)
            if not success:
                print("❌ ارسال لینک ناموفق بود")
                return False
            time.sleep(3)
            print("💬 باز کردن پیام‌های ذخیره شده...")
            await self.open_chat(user_id)
            time.sleep(3)
            print("🔍 پیدا کردن لینک در پیام‌ها...")
            chat_data = await self.get_chat(user_id)
            if not chat_data or not chat_data.get("messages"):
                print("❌ پیامی پیدا نشد")
                return False
            link_message_id = None
            for message in chat_data["messages"]:
                if link in message.get("text", ""):
                    link_message_id = message.get("message_id")
                    print(f"✅ پیام حاوی لینک پیدا شد: {link_message_id}")
                    break
            if not link_message_id:
                print("❌ پیام حاوی لینک پیدا نشد")
                return False
            print("🖱️ کلیک روی لینک...")
            try:
                message_selector = f"#message{link_message_id}"
                self.driver.execute_script(f"""
                    var msg = document.querySelector('{message_selector}');
                    if (msg) {{
                        msg.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    }}
                """)
                time.sleep(2)
                try:
                    link_in_message = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            f"//div[@id='message{link_message_id}']//a[contains(@href, 'http')]"
                        ))
                    )
                    link_in_message.click()
                    time.sleep(5)
                except:
                    message_element = self.driver.find_element(By.ID, f"message{link_message_id}")
                    message_element.click()
                    time.sleep(3)
                    self.driver.execute_script(f"""
                        var msg = document.querySelector('#message{link_message_id}');
                        if (msg) {{
                            var link = msg.querySelector('a');
                            if (link) {{
                                window.open(link.href, '_blank');
                            }}
                        }}
                    """)
                    time.sleep(5)
                print("✅ لینک باز شد")
            except Exception as e:
                print(f"⚠️ خطا در کلیک روی لینک: {e}")
                try:
                    message_element = self.driver.find_element(By.ID, f"message{link_message_id}")
                    message_element.click()
                    time.sleep(1)
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.ENTER).perform()
                    time.sleep(5)
                except:
                    pass
            print("🔍 در جستجوی دکمه پیوستن...")
            original_window = self.driver.current_window_handle
            windows = self.driver.window_handles
            if len(windows) > 1:
                for window in windows:
                    if window != original_window:
                        self.driver.switch_to.window(window)
                        break
                time.sleep(3)
            join_found = False
            join_button_selectors = [
                # برای گروه
                "button:contains('پیوستن به گروه')",
                "button:contains('Join Group')",
                "button:contains('عضویت در گروه')",
                "button:contains('پیوستن')",
                "button:contains('Join')",
                "button.Button--primary",
                "button.btn-primary",
                
                # برای کانال
                "button:contains('پیوستن به کانال')",
                "button:contains('Join Channel')",
                "button:contains('عضویت در کانال')",
                
                # انتخاب‌های عمومی
                "button[type='submit']",
                ".join-button",
                ".JoinButton",
            ]
            
            for selector in join_button_selectors:
                try:
                    if ":contains" in selector:
                        text = selector.split("'")[1]
                        join_buttons = self.driver.find_elements(By.XPATH, 
                            f"//button[contains(text(), '{text}')] | " +
                            f"//div[contains(text(), '{text}') and @role='button']"
                        )
                    else:
                        join_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in join_buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                print(f"✅ دکمه پیدا شد: {selector}")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(1)
                                try:
                                    button.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", button)
                                print("✅ روی دکمه پیوستن کلیک شد")
                                time.sleep(3)
                                join_found = True
                                break
                        except:
                            continue
                            
                    if join_found:
                        break
                except Exception as e:
                    continue
            if not join_found:
                print("⚠️ دکمه پیوستن پیدا نشد، بررسی مجدد...")
                join_texts = [
                    "پیوستن به گروه",
                    "پیوستن به کانال", 
                    "عضویت در گروه",
                    "عضویت در کانال",
                    "Join Group",
                    "Join Channel",
                    "Join",
                    "پیوستن",
                    "عضویت",
                    "ورود به گروه",
                    "ورود به کانال"
                ]
                
                for text in join_texts:
                    try:
                        elements = self.driver.find_elements(By.XPATH,
                            f"//*[contains(text(), '{text}') and " +
                            "(self::button or self::div or self::a or @role='button')]"
                        )
                        for element in elements:
                            if element.is_displayed():
                                print(f"✅ دکمه با متن '{text}' پیدا شد")
                                element.click()
                                time.sleep(3)
                                join_found = True
                                break
                        if join_found:
                            break
                    except:
                        continue
            if len(windows) > 1:
                self.driver.close()
                self.driver.switch_to.window(original_window)
            self.driver.get(self.splus_url)
            time.sleep(3)
            if join_found:
                print("✅ با موفقیت به گروه/کانال پیوستید!")
                return True
            else:
                print("⚠️ پیوستن انجام نشد (ممکن است قبلاً عضو باشید یا لینک معتبر نباشد)")
                return False
        except Exception as e:
            print(f"❌ خطا در متد join: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.get(self.splus_url)
            except:
                pass
            return False

    def _dispatch_js_contextmenu(self, el):
        js = """
        var el = arguments[0];
        try {
            var ev = document.createEvent('MouseEvent');
            ev.initMouseEvent('contextmenu', true, true, window, 1, 0,0,0,0, false, false, false, false, 2, null);
            el.dispatchEvent(ev);
            return true;
        } catch(e) {
            try {
                var ev2 = new MouseEvent('contextmenu', {bubbles:true, cancelable:true, view:window});
                el.dispatchEvent(ev2);
                return true;
            } catch(e2) {
                return false;
            }
        }
        """
        try:
            return self.driver.execute_script(js, el)
        except Exception:
            return False


    @async_to_sync
    async def context_click_message(
        self,
        message_id: str,
        menu_selector: Optional[str] = None,
        menu_text: Optional[str] = None,
        timeout: int = 8
    ) -> bool:
        """
        Context-click on message, then click a menu item.
        Improved: wait for menu container, search inside it, click via JS.
        """
        import time
        try:
            mid = str(message_id)
            if not mid.startswith("message"):
                mid = "message" + mid
            msg_el = WebDriverWait(self.driver, 5).until(lambda d: d.find_element(By.ID, mid))
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", msg_el)
            except Exception:
                pass
            time.sleep(0.08)
            opened = False
            try:
                ac = ActionChains(self.driver)
                ac.move_to_element(msg_el).context_click(msg_el).perform()
                opened = True
            except Exception:
                opened = bool(self._dispatch_js_contextmenu(msg_el))
            if not menu_selector and not menu_text:
                return opened
            menu_containers_selectors = [
                ".ContextMenu", ".context-menu", ".menu", ".dropdown-menu",
                "[role='menu']", ".popup-menu", ".menu-container"
            ]
            end = time.time() + float(timeout)
            menu_container = None
            while time.time() < end:
                for sel in menu_containers_selectors:
                    try:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        for e in els:
                            try:
                                if e.is_displayed():
                                    menu_container = e
                                    break
                            except Exception:
                                menu_container = e
                                break
                        if menu_container:
                            break
                    except Exception:
                        continue
                if menu_container:
                    break
                try:
                    els = self.driver.find_elements(By.XPATH, "//*[@role='menu' or @role='listbox']")
                    for e in els:
                        try:
                            if e.is_displayed():
                                menu_container = e
                                break
                        except Exception:
                            menu_container = e
                            break
                    if menu_container:
                        break
                except Exception:
                    pass
                time.sleep(0.12)
            def _safe_click(el):
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    try:
                        el.click()
                        return True
                    except Exception:
                        return False
            if menu_container:
                if menu_selector:
                    try:
                        found = menu_container.find_elements(By.CSS_SELECTOR, menu_selector)
                        for f in found:
                            if _safe_click(f):
                                return True
                    except Exception:
                        pass
                if menu_text:
                    try:
                        xpe = f".//*[normalize-space(text())={repr(menu_text)}]"
                        found = menu_container.find_elements(By.XPATH, xpe)
                        for f in found:
                            if _safe_click(f):
                                return True
                    except Exception:
                        pass
                    try:
                        found = menu_container.find_elements(By.XPATH, f".//*[contains(normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')), {repr(menu_text.strip().lower())})]")
                        for f in found:
                            if _safe_click(f):
                                return True
                    except Exception:
                        pass
            xpaths = []
            if menu_text:
                xpaths = [
                    f"//button[normalize-space()='{menu_text}']",
                    f"//div[normalize-space()='{menu_text}']",
                    f"//a[normalize-space()='{menu_text}']",
                    f"//*[normalize-space()='{menu_text}']"
                ]
            if menu_selector:
                try:
                    el = WebDriverWait(self.driver, 0.5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, menu_selector)))
                    if _safe_click(el):
                        return True
                except Exception:
                    pass
            for xp in xpaths:
                try:
                    el = WebDriverWait(self.driver, 0.5).until(EC.element_to_be_clickable((By.XPATH, xp)))
                    if _safe_click(el):
                        return True
                except Exception:
                    continue
            try:
                self.driver.save_screenshot("context_click_menu_notfound.png")
                if menu_container:
                    html = self.driver.execute_script("return arguments[0].outerHTML;", menu_container)
                    with open("menu_container.html", "w", encoding="utf-8") as f:
                        f.write(html)
            except Exception:
                pass
            return False
        except Exception:
            try:
                self.driver.save_screenshot("context_click_error.png")
            except:
                pass
            return False

    @async_to_sync
    async def click_confirm(
        self,
        confirm_selector: Optional[str] = None,
        confirm_text: Optional[str] = None,
        timeout: int = 6,
        take_screenshot_on_fail: bool = True
    ) -> bool:
        """
        Wait for confirmation dialog/modal then click confirm button inside it.
        """
        import time
        try:
            end = time.time() + float(timeout)
            modal_selectors = [
                ".Modal", ".modal", ".Dialog", ".dialog", ".confirm-dialog",
                ".confirmation", ".popup", "[role='dialog']", ".overlay", ".confirmModal"
            ]

            modal_el = None
            while time.time() < end:
                for sel in modal_selectors:
                    try:
                        cand = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        for c in cand:
                            try:
                                if c.is_displayed():
                                    modal_el = c
                                    break
                            except Exception:
                                modal_el = c
                                break
                        if modal_el:
                            break
                    except Exception:
                        continue
                if modal_el:
                    break
                try:
                    cands = self.driver.find_elements(By.XPATH, "//*[@role='dialog' or @role='alertdialog']")
                    for c in cands:
                        try:
                            if c.is_displayed():
                                modal_el = c
                                break
                        except Exception:
                            modal_el = c
                            break
                    if modal_el:
                        break
                except Exception:
                    pass
                time.sleep(0.12)
            def _safe_click(el):
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    try:
                        el.click()
                        return True
                    except Exception:
                        return False
            if modal_el and confirm_selector:
                try:
                    btns = modal_el.find_elements(By.CSS_SELECTOR, confirm_selector)
                    for b in btns:
                        if _safe_click(b):
                            return True
                except Exception:
                    pass
            candidate_texts = []
            if confirm_text:
                candidate_texts.append(confirm_text)
            candidate_texts += ["حذف", "حذف پیام", "حذف گفتگو", "بله", "تایید", "OK", "Yes", "Delete", "Confirm"]
            if modal_el:
                for t in candidate_texts:
                    try:
                        xp = f".//*[normalize-space(text())={repr(t)}]"
                        els = modal_el.find_elements(By.XPATH, xp)
                        for e in els:
                            if _safe_click(e):
                                return True
                    except Exception:
                        pass
                for t in candidate_texts:
                    try:
                        low = t.strip().lower()
                        els = modal_el.find_elements(By.XPATH, ".//button|.//a|.//div|.//span")
                        for e in els:
                            try:
                                txt = (e.text or "").strip().lower()
                                if low and low in txt:
                                    if _safe_click(e):
                                        return True
                            except Exception:
                                continue
                    except Exception:
                        pass
            for t in candidate_texts:
                try:
                    xp = f"//*[normalize-space(text())={repr(t)}]"
                    els = self.driver.find_elements(By.XPATH, xp)
                    for e in els:
                        try:
                            if _safe_click(e):
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                low_candidates = [t.lower() for t in candidate_texts]
                for b in buttons:
                    try:
                        txt = (b.text or "").strip().lower()
                        if not txt:
                            txt = (b.get_attribute("value") or "").strip().lower()
                        for cand in low_candidates:
                            if cand and cand in txt:
                                if _safe_click(b):
                                    return True
                    except Exception:
                        continue
            except Exception:
                pass
            if take_screenshot_on_fail:
                try:
                    self.driver.save_screenshot("confirm_click_failed.png")
                    if modal_el:
                        html = self.driver.execute_script("return arguments[0].outerHTML;", modal_el)
                        with open("confirm_modal.html", "w", encoding="utf-8") as f:
                            f.write(html)
                except Exception:
                    pass

            return False

        except Exception:
            try:
                if take_screenshot_on_fail:
                    self.driver.save_screenshot("confirm_click_error.png")
            except:
                pass
            return False

    def _schedule_handler(self, handler, update):
        async def _run():
            try:
                await handler(update)
            except Exception as e:
                print(f"❌ خطا: {e}")
        import threading
        thread = threading.Thread(
            target=lambda: asyncio.run(_run()),
            daemon=True
        )
        thread.start()

    @async_to_sync
    async def delete_message(self,message_id:str,chat_id:str) -> bool:
        """delete message / حذف پیام"""
        opening = await self.open_chat(chat_id)
        if opening:
            try:
                click_right = await self.context_click_message(message_id, menu_text="حذف")
                if click_right:
                    delete = await self.click_confirm(confirm_text="حذف")
                    if delete:
                        return True
                return False
            except:
                raise ValueError("Invalid Acsses")
        else:
            return False

    @async_to_sync
    async def pin_message(self,message_id:str,chat_id:str) -> bool:
        """pining message / سنجاق پیام"""
        type_chat = await self.get_type_chat_id(chat_id)
        if type_chat in ["Group","Channel"]:
            await self.open_chat(chat_id)
            try:
                click_right = await self.context_click_message(message_id, menu_text="سنجاق کردن")
                if click_right:
                    pining = await self.click_confirm(confirm_text="سنجاق کردن")
                    if pining:
                        return True
                return False
            except:
                raise ValueError("Invalid Acsses")
        raise ValueError("group and channel can pining message")

    @async_to_sync
    async def unpin_message(self,message_id:str,chat_id:str) -> bool:
        """unpining message / برداشتن سنجاق پیام"""
        type_chat = await self.get_type_chat_id(chat_id)
        if type_chat in ["Group","Channel"]:
            await self.open_chat(chat_id)
            try:
                click_right = await self.context_click_message(message_id, menu_text="برداشتن سنجاق")
                if click_right:
                    return True
                return False
            except:
                raise ValueError("Invalid Acsses")
        raise ValueError("group and channel can pining message")

    def on_message(self,chat_id:str,is_me: Literal[True,False,None] = None):
        """برای دریافت پیام ها"""
        self._fetch_messages = True
        def decorator(handler: Callable[[Update], Awaitable[None]]):
            self.messages_handlers.append({"handler":handler,"chat_id":chat_id,"is_me":is_me})
            return handler
        return decorator

    @async_to_sync
    async def fetch_messages_updates(self,chat_id: str,is_me: Literal[True,False,None] = False):
        while self.running:
            chat = await self.get_chat(chat_id)
            messages = chat["messages"]
            if not self.list_:
                for msg in messages:
                    self.list_.append(msg["message_id"])
            for msg in messages:
                if not msg["message_id"] in self.list_:
                    self.list_.append(msg["message_id"])
                    if len(self.list_) >= 200:
                        self.list_.pop(-1)
                    if msg["day"] == "امروز":
                        if not is_me:
                            if not msg["is_me"]:
                                update_obj = Update(msg,self,chat_id)
                                for handler in self.messages_handlers:
                                    self._schedule_handler(handler["handler"], update_obj)
                        else:
                            if msg["is_me"]:
                                update_obj = Update(msg,self,chat_id)
                                for handler in self.messages_handlers:
                                    self._schedule_handler(handler["handler"], update_obj)

    @async_to_sync
    async def _run_all(self):
        tasks = []
        if self._fetch_messages and self.messages_handlers:
            for msg_hnd in self.messages_handlers:
                tasks.append(self.fetch_messages_updates(msg_hnd["chat_id"],msg_hnd["is_me"]))
        if not tasks:
            raise ValueError("No handlers registered. Use on_message('chat id') first.")
        await asyncio.gather(*tasks)

    def run(self):
        """اجرای اصلی بات - فقط اگر هندلرهای مربوطه ثبت شده باشند"""
        if not (self._fetch_messages):
            raise ValueError("No update types selected. Use on_message() first.")
        
        if (self._fetch_messages and not self.messages_handlers) or (self._fetch_messages and not self.messages_handlers):
            raise ValueError("Message handlers registered but no message callbacks defined.")

        self.running = True
        asyncio.run(self._run_all())
