"""
Telegram Bot — โต้ตอบ 2 ทาง (send + receive) ผ่าน Telegram Bot API

รองรับ: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6
- ส่ง: ข้อความ / รูป / ไฟล์ / แก้ไขข้อความ / inline keyboard
- รับ: getUpdates long-polling / short-polling + commands + callback query
- 2 โหมด polling:
  * "sync"  = long-poll (timeout=25s) เหมาะกับสคริปต์ตัวเดียว
  * "async" = short-poll (timeout=0) ทุก 1.5s ไม่บล็อก asyncio loop
- HTTPS:
  * default: TLS เข้ารหัส (urequests, CERT_NONE)
  * verify_cert=True: ตรวจใบรับรองจริง (raw socket + SSLContext CERT_REQUIRED)
"""

import time

try:
    import gc
except ImportError:
    gc = None

try:
    import asyncio
except ImportError:
    asyncio = None

try:
    import urequests as _requests
except ImportError:
    try:
        import requests as _requests
    except ImportError:
        _requests = None

try:
    import ujson as json
except ImportError:
    import json

try:
    import socket
except ImportError:
    socket = None

try:
    import ssl
except ImportError:
    ssl = None

try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None

_API_BASE = "https://api.telegram.org"
_API_HOST = "api.telegram.org"
_DEFAULT_POLL_TIMEOUT = 25
_DEFAULT_POLL_INTERVAL_MS = 1500
_DEFAULT_HTTP_TIMEOUT = 40
_MAX_TEXT_LEN = 4096
_MAX_UPLOAD_BYTES = 100 * 1024


def _safe_str(data, limit=200):
    if isinstance(data, (dict, list)):
        try:
            s = json.dumps(data)
        except Exception:
            s = str(data)
    else:
        s = str(data)
    if len(s) > limit:
        s = s[:limit] + "..."
    return s


def _now_ms():
    f = getattr(time, "ticks_ms", None)
    if f:
        return f()
    return int(time.time() * 1000)


def _sleep_ms(ms):
    if ms <= 0:
        return
    f = getattr(time, "sleep_ms", None)
    if f:
        f(ms)
    else:
        time.sleep(ms / 1000.0)


def _make_ssl_context(ca_cert):
    """สร้าง SSLContext ที่ตรวจสอบใบรับรอง (CERT_REQUIRED) — ป้องกัน MITM"""
    if not ssl or not hasattr(ssl, "SSLContext"):
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(ca_cert)
    return ctx


class MessageContext:
    """
    ข้อมูลข้อความ / callback ที่ส่งไปยัง handler
    """

    def __init__(self, bot, chat_id, text="", message_id=None, user_id=None,
                 username="", command="", args=None, data=None, callback_query_id=None):
        self.bot = bot
        self.chat_id = chat_id
        self.text = text
        self.message_id = message_id
        self.user_id = user_id
        self.username = username
        self.command = command
        self.args = args or []
        self.data = data
        self.callback_query_id = callback_query_id

    def reply(self, text, parse_mode=None, keyboard=None):
        """
        ตอบกลับไปยัง chat ต้นทาง

        :param text: ข้อความที่ต้องการตอบ
        :param parse_mode: "HTML" หรือ "Markdown"
        :param keyboard: reply_markup dict (จาก TelegramBot.inline_keyboard)
        :return: message_id หรือ None
        """
        return self.bot.send_message(self.chat_id, text, parse_mode=parse_mode, keyboard=keyboard)

    def answer_callback(self, text=None):
        """
        ตอบรับ callback query (ต้องเรียกถ้าใช้ inline keyboard)

        :param text: ข้อความแจ้งเตือนสั้น ๆ (แสดง popup)
        :return: bool
        """
        if self.callback_query_id:
            return self.bot.answer_callback_query(self.callback_query_id, text=text)
        return False

    def __repr__(self):
        return "MessageContext(chat_id=%s, command=%s)" % (self.chat_id, self.command)


class TelegramBot:
    """
    Telegram Bot — โต้ตอบ 2 ทางผ่าน long-polling / short-polling

    ตัวอย่าง:
        from telegram.telegram_bot import TelegramBot

        bot = TelegramBot(token="123456:ABC...", allowed_chat_ids=[123456789])
        bot.on_command("/status", lambda ctx: ctx.reply("ONLINE"))
        bot.loop()

    HTTPS:
        - เริ่มต้น: ข้อมูลเข้ารหัสด้วย TLS แต่ไม่ตรวจสอบใบรับรอง (เหมือน urequests ทั่วไป)
        - เพื่อกัน MITM: เปิด verify_cert=True + วาง CA cert ไว้ที่ ca_cert
          (ต้องดาวน์โหลด Root CA ของ api.telegram.org มาไว้ใน flash)
    """

    def __init__(self, token=None, config_file="telegram_config.json", poll_mode="async",
                 poll_timeout=_DEFAULT_POLL_TIMEOUT, poll_interval_ms=_DEFAULT_POLL_INTERVAL_MS,
                 max_updates=10, allowed_chat_ids=None, http_timeout=_DEFAULT_HTTP_TIMEOUT,
                 verify_cert=False, ca_cert="/cert/ca.pem"):
        self._config_mgr = JsonConfigManager(config_file) if JsonConfigManager else None

        self.config = {
            "token": token,
            "poll_mode": poll_mode,
            "poll_timeout": poll_timeout,
            "poll_interval_ms": poll_interval_ms,
            "max_updates": max_updates,
            "allowed_chat_ids": allowed_chat_ids or [],
            "verify_cert": verify_cert,
            "ca_cert": ca_cert,
        }
        self._load_config()

        self.token = self.config.get("token") or ""
        self.poll_mode = self.config.get("poll_mode", "async")
        self.poll_timeout = self.config.get("poll_timeout", _DEFAULT_POLL_TIMEOUT)
        self.poll_interval_ms = self.config.get("poll_interval_ms", _DEFAULT_POLL_INTERVAL_MS)
        self.max_updates = self.config.get("max_updates", 10)
        self.allowed_chat_ids = self.config.get("allowed_chat_ids") or []
        self.http_timeout = http_timeout
        self.verify_cert = self.config.get("verify_cert", False)
        self.ca_cert = self.config.get("ca_cert", "/cert/ca.pem")

        self._last_update_id = 0
        self._handlers = {}
        self._message_handler = None
        self._callback_handler = None
        self._update_handler = None
        self._last_call_ms = 0
        self._min_call_interval_ms = 1000

        if _requests is None:
            print("⚠️ ไม่พบ urequests/requests module — ต้องติดตั้งก่อนใช้งาน")

    # ---------- Config ----------

    def _load_config(self):
        if self._config_mgr:
            data = self._config_mgr.load(default={})
            if data:
                self.config.update(data)

    def save_config(self):
        """บันทึก config (token, whitelist, settings) ลงไฟล์ JSON"""
        if self._config_mgr:
            return self._config_mgr.save(self.config)
        return False

    @property
    def ready(self):
        """พร้อมใช้งานหรือไม่ (มี token + มี HTTP library)"""
        return bool(self.token) and _requests is not None

    # ---------- Handler Registration ----------

    def on_command(self, command, handler):
        """ลงทะเบียน handler สำหรับ /command (เช่น "/status", "status")"""
        cmd = command.lower()
        if not cmd.startswith("/"):
            cmd = "/" + cmd
        self._handlers[cmd] = handler

    def on_message(self, handler):
        """ลงทะเบียน handler สำหรับข้อความทั่วไป (ที่ไม่มี /command ตรง)"""
        self._message_handler = handler

    def on_callback_query(self, handler):
        """ลงทะเบียน handler สำหรับการกดปุ่ม inline keyboard"""
        self._callback_handler = handler

    def on_update(self, handler):
        """ลงทะเบียน handler สำหรับ raw update ทุกตัว (callback(update))"""
        self._update_handler = handler

    # ---------- Helpers ----------

    def _base_url(self):
        return "%s/bot%s" % (_API_BASE, self.token)

    def _throttle(self):
        """จำกัดอัตรา API call — ป้องกันเกิน limit ของ Telegram (~30 msg/s)"""
        if self._min_call_interval_ms <= 0:
            return
        now = _now_ms()
        if self._last_call_ms:
            elapsed = now - self._last_call_ms
            if 0 <= elapsed < self._min_call_interval_ms:
                time.sleep((self._min_call_interval_ms - elapsed) / 1000.0)
        self._last_call_ms = _now_ms()

    def _api_call(self, method, params=None):
        """
        เรียก Bot API (POST JSON) — คืน result dict หรือ None

        - ปกติ: ใช้ urequests (TLS แต่ไม่ตรวจสอบ cert)
        - ถ้า verify_cert=True: ใช้ raw socket + SSLContext CERT_REQUIRED

        :param method: ชื่อ method เช่น "sendMessage", "getUpdates"
        :param params: dict ของ parameters
        :return: result (dict/list) หรือ None
        """
        if not self.ready:
            return None
        self._throttle()
        if params is None:
            params = {}
        path = "bot%s/%s" % (self.token, method)
        try:
            if gc:
                gc.collect()
            if self.verify_cert:
                body_bytes = json.dumps(params).encode()
                code, body = self._raw_https_request(
                    path, {"Content-Type": "application/json"}, body_bytes)
            else:
                req = _requests
                if req is None:
                    return None
                url = "%s/%s" % (self._base_url(), method)
                resp = req.post(url, json=params, timeout=self.http_timeout)
                try:
                    code = resp.status_code
                    body = resp.json()
                finally:
                    resp.close()
            if code == 200 and body and body.get("ok"):
                return body.get("result")
            print("❌ %s error (%s): %s" % (method, code, _safe_str(body)))
            return None
        except Exception as e:
            print("❌ %s exception: %s" % (method, e))
            return None
        finally:
            if gc:
                gc.collect()

    def _raw_https_request(self, path, headers, body_bytes):
        """
        ส่ง HTTPS request ด้วย raw socket + SSLContext CERT_REQUIRED
        (ตรวจสอบใบรับรองจริง — ป้องกัน MITM)

        :param path: path เช่น "botTOKEN/sendMessage"
        :param headers: dict ของ HTTP headers
        :param body_bytes: body (bytes)
        :return: (status_code, parsed_json_or_None)
        :raises: Exception ถ้า cert ตรวจไม่ผ่านหรือเชื่อมต่อไม่ได้
        """
        if not socket or not ssl:
            raise RuntimeError("ไม่พบ socket/ssl module")
        host = _API_HOST
        ctx = _make_ssl_context(self.ca_cert)
        if ctx is None:
            raise RuntimeError("ssl.SSLContext ไม่รองรับใน firmware นี้")

        sock = None
        tls = None
        try:
            try:
                addr = socket.getaddrinfo(host, 443, 0, socket.SOCK_STREAM)[0][4]
            except Exception:
                addr = (host, 443)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.http_timeout)
            sock.connect(addr)
            tls = ctx.wrap_socket(sock, server_hostname=host)

            req = b"POST /%s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n" % (
                path.encode(), host.encode())
            for k, v in headers.items():
                req += b"%s: %s\r\n" % (str(k).encode(), str(v).encode())
            req += b"Content-Length: %d\r\n\r\n" % len(body_bytes)
            req += body_bytes
            tls.write(req)
            del req
            if gc:
                gc.collect()

            data = b""
            while b"\r\n\r\n" not in data:
                chunk = tls.read(512)
                if not chunk:
                    break
                data += chunk
            head, _, rest = data.partition(b"\r\n\r\n")

            status_line = head.split(b"\r\n", 1)[0]
            try:
                code = int(status_line.split(b" ", 2)[1])
            except Exception:
                raise RuntimeError("HTTP response ผิดปกติ: %s" % status_line)

            content_length = 0
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    try:
                        content_length = int(line.split(b":", 1)[1].strip())
                    except Exception:
                        content_length = 0

            body_data = rest
            while len(body_data) < content_length:
                chunk = tls.read(512)
                if not chunk:
                    break
                body_data += chunk

            try:
                return code, json.loads(body_data.decode("utf-8"))
            except Exception:
                return code, None
        finally:
            try:
                if tls:
                    tls.close()
                elif sock:
                    sock.close()
            except Exception:
                pass

    def _multipart_call(self, method, fields, file_field, file_path, mime="application/octet-stream"):
        """เรียก API แบบ multipart/form-data สำหรับอัปโหลดไฟล์"""
        if not self.ready:
            return False
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            print("❌ เปิดไฟล์ %s ไม่ได้: %s" % (file_path, e))
            return False

        if len(file_bytes) > _MAX_UPLOAD_BYTES:
            print("⚠️ ไฟล์ใหญ่เกิน %dKB — ESP32 อาจ RAM ไม่พอ" % (_MAX_UPLOAD_BYTES // 1024))

        self._throttle()
        boundary = "----ESP32TelegramBoundary"
        body = b""
        for k, v in fields.items():
            body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                     % (boundary, k, v)).encode()
        fname = file_path.replace("\\", "/").split("/")[-1]
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                 "Content-Type: %s\r\n\r\n" % (boundary, file_field, fname, mime)).encode()
        body += file_bytes
        body += ("\r\n--%s--\r\n" % boundary).encode()
        del file_bytes

        url = "%s/%s" % (self._base_url(), method)
        headers = {"Content-Type": "multipart/form-data; boundary=%s" % boundary}
        try:
            if gc:
                gc.collect()
            if self.verify_cert:
                path = "bot%s/%s" % (self.token, method)
                code, result = self._raw_https_request(path, headers, body)
            else:
                req = _requests
                if req is None:
                    return False
                resp = req.post(url, data=body, headers=headers, timeout=self.http_timeout)
                try:
                    code = resp.status_code
                    result = resp.json()
                finally:
                    resp.close()
            ok = code == 200 and result and result.get("ok")
            if not ok:
                print("❌ %s upload error (%s): %s" % (method, code, _safe_str(result)))
            return ok
        except Exception as e:
            print("❌ %s upload exception: %s" % (method, e))
            return False
        finally:
            del body
            if gc:
                gc.collect()

    # ---------- UI Helpers (static) ----------

    @staticmethod
    def inline_keyboard(rows):
        """
        สร้าง inline keyboard (ปุ่มกดในข้อความ)

        :param rows: list ของแถว — แต่ละแถวเป็น list[(text, callback_data)]
                     หรือ dict {text: callback_data} หรือ dict ของปุ่มเต็มรูปแบบ
        :return: reply_markup dict
        """
        kb = []
        for row in rows:
            btns = []
            if isinstance(row, dict):
                items = list(row.items())
            else:
                items = list(row)
            for item in items:
                if isinstance(item, (tuple, list)) and len(item) == 2:
                    btns.append({"text": item[0], "callback_data": item[1]})
                elif isinstance(item, dict):
                    btns.append(item)
            kb.append(btns)
        return {"inline_keyboard": kb}

    @staticmethod
    def reply_keyboard(rows, one_time=False, resize=True):
        """
        สร้าง reply keyboard (ปุ่มใต้ช่องพิมพ์)

        :param rows: list ของแถว — แต่ละแถวเป็น list[str]
        :return: reply_markup dict
        """
        kb = []
        for row in rows:
            kb.append([{"text": t} for t in row])
        return {"keyboard": kb, "one_time_keyboard": one_time, "resize_keyboard": resize}

    @staticmethod
    def remove_keyboard():
        """ลบ reply keyboard ออกจากหน้าจอ"""
        return {"remove_keyboard": True}

    # ---------- ส่ง (ESP32 → Telegram) ----------

    def get_me(self):
        """ตรวจสอบ token — คืน bot username หรือ None"""
        result = self._api_call("getMe")
        if result and "username" in result:
            return result["username"]
        return None

    def send_message(self, chat_id, text, parse_mode=None, keyboard=None, disable_notification=False):
        """
        ส่งข้อความ

        :param chat_id: id ของ chat/group/channel
        :param text: ข้อความ (ตัดอัตโนมัติถ้าเกิน 4096 ตัว)
        :param parse_mode: "HTML" หรือ "Markdown"
        :param keyboard: reply_markup dict
        :return: message_id หรือ None
        """
        if text is None:
            return None
        text = str(text)
        if len(text) > _MAX_TEXT_LEN:
            text = text[:_MAX_TEXT_LEN - 3] + "..."
        params = {"chat_id": chat_id, "text": text}
        if parse_mode:
            params["parse_mode"] = parse_mode
        if keyboard is not None:
            params["reply_markup"] = keyboard
        if disable_notification:
            params["disable_notification"] = True
        result = self._api_call("sendMessage", params)
        if result and "message_id" in result:
            return result["message_id"]
        return None

    def send_photo(self, chat_id, path, caption=None):
        """
        ส่งรูปจาก filesystem

        :param chat_id: id ของ chat
        :param path: path ไฟล์รูปบน ESP32
        :param caption: คำอธิบายใต้รูป
        :return: bool
        """
        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = caption
        return self._multipart_call("sendPhoto", fields, "photo", path, "image/jpeg")

    def send_document(self, chat_id, path, caption=None):
        """
        ส่งไฟล์จาก filesystem

        :param chat_id: id ของ chat
        :param path: path ไฟล์บน ESP32
        :param caption: คำอธิบาย
        :return: bool
        """
        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = caption
        return self._multipart_call("sendDocument", fields, "document", path, "application/octet-stream")

    def edit_message(self, chat_id, message_id, text, parse_mode=None):
        """
        แก้ไขข้อความของข้อความเดิม (ใช้ update สเตตัส)

        :param chat_id: id ของ chat
        :param message_id: id ของข้อความเดิม
        :param text: ข้อความใหม่
        :return: bool
        """
        params = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if parse_mode:
            params["parse_mode"] = parse_mode
        return self._api_call("editMessageText", params) is not None

    def send_keyboard(self, chat_id, text, buttons, parse_mode=None):
        """
        ส่งข้อความพร้อม inline keyboard

        :param buttons: list ของแถวปุ่ม (ดู inline_keyboard)
        :return: message_id หรือ None
        """
        return self.send_message(chat_id, text, parse_mode=parse_mode,
                                 keyboard=self.inline_keyboard(buttons))

    def answer_callback_query(self, callback_query_id, text=None):
        """
        ตอบรับ callback query — แสดง popup หรือปิดสปินเนอร์ปุ่ม

        :param callback_query_id: id ของ callback query
        :param text: ข้อความ popup (optional)
        :return: bool
        """
        params = {"callback_query_id": callback_query_id}
        if text:
            params["text"] = text
        return self._api_call("answerCallbackQuery", params) is not None

    # ---------- รับ (Telegram → ESP32) ----------

    def get_updates(self):
        """
        ดึง updates จาก Telegram

        - async mode: timeout=0 → ตอบกลับทันที
        - sync mode: timeout=poll_timeout (long-poll)
        - จำ offset อัตโนมัติ → ไม่รับข้อความซ้ำ

        :return: list ของ update dict
        """
        params = {
            "timeout": 0 if self.poll_mode == "async" else self.poll_timeout,
            "offset": self._last_update_id + 1 if self._last_update_id else 0,
        }
        if self.max_updates:
            params["limit"] = self.max_updates
        result = self._api_call("getUpdates", params)
        return result if isinstance(result, list) else []

    @staticmethod
    def _parse_command(text):
        """แยก /command และ arguments จากข้อความ"""
        if text and text.startswith("/"):
            parts = text.split()
            cmd = parts[0].lower()
            if "@" in cmd:
                cmd = cmd.split("@", 1)[0]
            return cmd, parts[1:]
        return "", []

    def _authorized(self, chat_id):
        """ตรวจ whitelist — ถ้าไม่ได้ตั้ง allowed_chat_ids ให้ผ่านทุก chat"""
        if not self.allowed_chat_ids:
            return True
        if chat_id in self.allowed_chat_ids:
            return True
        return any(str(c) == str(chat_id) for c in self.allowed_chat_ids)

    def _handle_message(self, update, msg):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        text = msg.get("text") or msg.get("caption") or ""
        message_id = msg.get("message_id")
        user = msg.get("from") or {}
        user_id = user.get("id")
        username = user.get("username") or ""

        if not self._authorized(chat_id):
            print("⛔ บล็อกข้อความจาก chat ที่ไม่อนุญาต: %s" % chat_id)
            return

        command, args = self._parse_command(text)
        ctx = MessageContext(self, chat_id, text=text, message_id=message_id,
                             user_id=user_id, username=username,
                             command=command, args=args)

        if command and command in self._handlers:
            self._handlers[command](ctx)
            return
        if self._message_handler:
            self._message_handler(ctx)

    def _handle_callback(self, update, cq):
        cq_id = cq.get("id")
        data = cq.get("data") or ""
        message = cq.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        user = cq.get("from") or {}
        user_id = user.get("id")
        username = user.get("username") or ""

        if not self._authorized(chat_id):
            print("⛔ บล็อก callback จาก chat ที่ไม่อนุญาต: %s" % chat_id)
            return

        ctx = MessageContext(self, chat_id, text=data, user_id=user_id, username=username,
                             data=data, callback_query_id=cq_id)
        if self._callback_handler:
            self._callback_handler(ctx)

    def process_updates(self, updates=None):
        """
        ประมวลผล updates ทั้งหมด — จัดการทีละตัวแล้ว del (ประหยัด RAM)

        :param updates: list ของ update dict (ถ้าไม่ส่งจะดึงเอง)
        :return: จำนวน update ที่ประมวลผล
        """
        if updates is None:
            updates = self.get_updates()
        count = 0
        for upd in updates:
            update_id = upd.get("update_id")
            if update_id:
                self._last_update_id = max(self._last_update_id, update_id)

            msg = upd.get("message") or upd.get("edited_message")
            if msg:
                self._handle_message(upd, msg)
                count += 1

            cq = upd.get("callback_query")
            if cq:
                self._handle_callback(upd, cq)
                count += 1

            if self._update_handler:
                self._update_handler(upd)

            del upd
        if gc:
            gc.collect()
        return count

    def poll(self):
        """รับ 1 รอบ: getUpdates → process — คืนจำนวน update ที่ประมวลผล"""
        if not self.ready:
            return 0
        updates = self.get_updates()
        return self.process_updates(updates)

    def loop(self, sleep_ms=100):
        """
        sync loop (long-poll) — บล็อกตลอด ไม่เหมาะกับงาน async พร้อมกัน

        ใช้เมื่อต้องการสคริปต์ bot ตัวเดียว
        """
        if self.poll_mode != "sync":
            self.poll_mode = "sync"
            print("🔄 สลับเป็น sync polling (long-poll timeout=%ds)" % self.poll_timeout)
        print("🤖 TelegramBot polling (sync)...")
        while True:
            try:
                self.poll()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("❌ poll error: %s — retry..." % e)
                time.sleep(2)
            _sleep_ms(sleep_ms)

    async def poll_once(self):
        """async: ยอมให้ task อื่นรัน แล้ว poll 1 รอบ"""
        if asyncio:
            await asyncio.sleep(0)
        return self.poll()

    async def run(self, stop_event=None):
        """
        async loop (short-poll) — ไม่บล็อก task อื่น เหมาะกับหลาย bot / งานพร้อมกัน

        ตัวอย่าง:
            asyncio.create_task(bot.run())
        """
        if self.poll_mode != "async":
            self.poll_mode = "async"
            print("🔄 สลับเป็น async polling (short-poll ทุก %dms)" % self.poll_interval_ms)
        print("🤖 TelegramBot polling (async)...")
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            try:
                self.poll()
            except Exception as e:
                print("❌ poll error: %s — retry..." % e)
            if gc:
                gc.collect()
            if asyncio:
                await asyncio.sleep(self.poll_interval_ms / 1000.0)
            else:
                _sleep_ms(self.poll_interval_ms)

    # ---------- Lifecycle ----------

    def deinit(self):
        """คืนทรัพยากร ล้าง handlers"""
        self._handlers.clear()
        self._message_handler = None
        self._callback_handler = None
        self._update_handler = None
        self._last_update_id = 0
