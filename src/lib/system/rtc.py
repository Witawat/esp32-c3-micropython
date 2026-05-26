"""
RTC Utility: DS3231 + NTP sync + RTC Factory
รองรับ: machine.RTC (built-in), DS3231 (external I2C)
"""

import machine
import time


class DS3231:
    """DS3231 External RTC via I2C"""
    
    def __init__(self, sda: int = 21, scl: int = 22, address: int = 0x68,
                 i2c: machine.I2C = None):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (default 0x68)
        :param i2c: existing I2C instance (optional)
        """
        if i2c:
            self.i2c = i2c
        else:
            self.i2c = machine.I2C(0, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=100000)
        self.address = address
        print(f"🕐 DS3231 RTC เริ่มต้น — I2C 0x{address:02X}")

    @staticmethod
    def _bcd2dec(v):
        return ((v >> 4) * 10) + (v & 0x0F)

    @staticmethod
    def _dec2bcd(v):
        return ((v // 10) << 4) | (v % 10)

    def datetime(self):
        data = self.i2c.readfrom_mem(self.address, 0x00, 7)
        sec = self._bcd2dec(data[0] & 0x7F)
        minute = self._bcd2dec(data[1])
        hour = self._bcd2dec(data[2] & 0x3F)
        wday = self._bcd2dec(data[3])
        mday = self._bcd2dec(data[4])
        month = self._bcd2dec(data[5] & 0x1F)
        year = 2000 + self._bcd2dec(data[6])
        return (year, month, mday, wday, hour, minute, sec, 0)

    def set_datetime(self, dt):
        year, month, mday, wday, hour, minute, sec, _ = dt
        yy = year - 2000
        buf = bytes([
            self._dec2bcd(sec),
            self._dec2bcd(minute),
            self._dec2bcd(hour),
            self._dec2bcd(wday),
            self._dec2bcd(mday),
            self._dec2bcd(month),
            self._dec2bcd(yy),
        ])
        self.i2c.writeto_mem(self.address, 0x00, buf)


class RTCManager:
    """Manage built-in RTC + optional external DS3231"""
    
    def __init__(self):
        self.rtc = machine.RTC()
        self._external_rtc = None  # DS3231 instance (optional)
    
    def set_external_rtc(self, ds: DS3231):
        """Attach external DS3231 RTC"""
        self._external_rtc = ds
        # Restore time from external RTC to built-in
        self.sync_from_ds3231(ds)

    def get_datetime(self):
        return self.rtc.datetime()

    def set_datetime(self, dt):
        self.rtc.datetime(dt)

    def sync_ntp(self, timezone_offset_hours: int = 7):
        import ntptime
        ntptime.settime()
        dt = self.rtc.datetime()
        ts = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))
        ts += timezone_offset_hours * 3600
        lt = time.localtime(ts)
        self.rtc.datetime((lt[0], lt[1], lt[2], lt[6] + 1, lt[3], lt[4], lt[5], 0))
        return self.rtc.datetime()

    def sync_to_ds3231(self, ds: DS3231):
        ds.set_datetime(self.rtc.datetime())

    def sync_from_ds3231(self, ds: DS3231):
        self.rtc.datetime(ds.datetime())
        return self.rtc.datetime()


class RTCFactory:
    """
    RTC Factory — auto-select RTC source
    
    ลำดับการเลือก:
    1. DS3231 (external, battery-backed) — ถ้ามี
    2. machine.RTC (built-in, volatile) — fallback
    
    ตัวอย่าง:
        rtc = RTCFactory.create(sda=21, scl=22)
        dt = rtc.datetime()
        rtc.sync_ntp()
    """
    
    @staticmethod
    def create(sda: int = 21, scl: int = 22,
               ds3231_addr: int = 0x68,
               i2c: machine.I2C = None) -> 'RTCManager':
        """
        Create RTC with auto-detection
        
        :param sda: GPIO SDA (for DS3231)
        :param scl: GPIO SCL (for DS3231)
        :param ds3231_addr: DS3231 I2C address
        :param i2c: existing I2C instance (optional)
        :return: RTCManager instance with best available RTC
        """
        rtc_mgr = RTCManager()
        
        # Try DS3231 first
        if i2c:
            try:
                ds = DS3231(i2c=i2c)
                # Verify by reading
                dt = ds.datetime()
                if dt and dt[0] >= 2020:  # sanity check
                    rtc_mgr.set_external_rtc(ds)
                    print("🕐 RTCFactory → DS3231 (external, battery-backed)")
                    return rtc_mgr
            except Exception:
                pass
        
        # Try with GPIO pins
        try:
            ds = DS3231(sda=sda, scl=scl, address=ds3231_addr)
            dt = ds.datetime()
            if dt and dt[0] >= 2020:
                rtc_mgr.set_external_rtc(ds)
                print("🕐 RTCFactory → DS3231 (external)")
                return rtc_mgr
        except Exception:
            pass
        
        # Fallback to built-in RTC
        print("🕐 RTCFactory → machine.RTC (internal, volatile)")
        return rtc_mgr
    
    @staticmethod
    def create_default() -> 'RTCManager':
        """Create RTC with built-in only (no I2C scan)"""
        return RTCManager()


class NTPTimeSync:
    """
    NTP Time Synchronization helper
    
    Sync both machine.RTC and DS3231 from NTP
    
    ตัวอย่าง:
        rtc = RTCFactory.create(sda=21, scl=22)
        ntp = NTPTimeSync(rtc, timezone_offset=7)
        ntp.sync()
        print(rtc.get_datetime())
    """
    
    def __init__(self, rtc_manager: 'RTCManager', timezone_offset: int = 7):
        """
        :param rtc_manager: RTCManager instance
        :param timezone_offset: UTC offset in hours (e.g. 7 = ICT/Bangkok)
        """
        self._rtc = rtc_manager
        self._tz_offset = timezone_offset
    
    def sync(self, retries: int = 3) -> bool:
        """
        Sync time from NTP server
        
        :param retries: number of retry attempts
        :return: True if successful
        """
        try:
            import ntptime
        except ImportError:
            print("❌ NTP: ntptime module ไม่พบ — ใช้ WiFi manager sync แทน")
            return False
        
        for attempt in range(retries):
            try:
                # Sync built-in RTC from NTP
                ntptime.settime()
                
                # Apply timezone offset
                dt = self._rtc.rtc.datetime()
                ts = time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0))
                ts += self._tz_offset * 3600
                lt = time.localtime(ts)
                local_dt = (lt[0], lt[1], lt[2], lt[6] + 1, lt[3], lt[4], lt[5], 0)
                self._rtc.rtc.datetime(local_dt)
                
                # Sync external RTC if available
                if self._rtc._external_rtc:
                    self._rtc.sync_to_ds3231(self._rtc._external_rtc)
                    print(f"🕐 NTP synced → DS3231 + machine.RTC (UTC+{self._tz_offset})")
                else:
                    print(f"🕐 NTP synced → machine.RTC (UTC+{self._tz_offset})")
                
                return True
                
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️ NTP attempt {attempt + 1} failed: {e} — retrying...")
                    time.sleep_ms(1000)
                else:
                    print(f"❌ NTP sync failed after {retries} attempts: {e}")
        
        return False
    
    def get_last_sync_time(self, rtc_manager: 'RTCManager' = None) -> tuple:
        """
        Get last sync timestamp (from external RTC if available)
        
        :return: datetime tuple or None
        """
        if rtc_manager is None:
            rtc_manager = self._rtc
        return rtc_manager.get_datetime()
