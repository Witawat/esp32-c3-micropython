"""
I2S Audio Driver สำหรับ ESP32-C3
Interface: machine.I2S
รองรับ: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6

Modes:
- TX: เล่นเสียงผ่านลำโพง (I2S DAC เช่น MAX98357)
- RX: รับเสียงจากไมโครโฟน (I2S MEMS mic เช่น INMP441)
- TXRX: Full duplex

หมายเหตุ:
- ESP32-C3 มี I2S0 เพียง bus เดียว
- DMA buffer ใช้ RAM ~10-50KB ขึ้นอยู่กับ ibuf size
"""

import machine

try:
    from machine import I2S as _I2S, Pin
    HAS_I2S = True
except ImportError:
    HAS_I2S = False


class I2SAudio:
    """
    I2S Audio Driver — เล่น/บันทึกเสียงผ่าน I2S

    การเชื่อมต่อ (MAX98357 I2S DAC):
        ESP32-C3          MAX98357
        ─────────         ────────
        SCK (BCLK)  ──→   BCLK
        WS (LRC)    ──→   LRC
        SD (DIN)    ──→   DIN
        3.3V        ──→   VIN
        GND         ───   GND
        GAIN        ───   (ปรับ gain: GND=3dB, NC=6dB, VDD=9dB, 12dB, 15dB)
        SD_MODE     ──→   3.3V (normal) / GND (shutdown)

    การเชื่อมต่อ (INMP441 I2S Mic):
        ESP32-C3          INMP441
        ─────────         ───────
        SCK (BCLK)  ──→   SCK
        WS (LRC)    ──→   WS
        SD (DOUT)   ←──   SD
        L/R         ──→   GND (left) / 3.3V (right)
        3.3V        ──→   VDD
        GND         ───   GND

    ตัวอย่าง:
        # เล่น WAV (16-bit mono 16kHz)
        audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx')
        audio.write(wav_data)
        audio.deinit()

        # บันทึกเสียง
        mic = I2SAudio(sck=10, ws=9, sd=8, mode='rx')
        samples = mic.read(1600)  # 100ms @ 16kHz
    """

    # Mode constants
    MODE_TX = 0    # Playback (DAC → speaker)
    MODE_RX = 1    # Recording (ADC ← microphone)
    MODE_TXRX = 2  # Full duplex

    _MODE_MAP = {
        'tx': MODE_TX,
        'rx': MODE_RX,
        'txrx': MODE_TXRX,
    }

    # I2S mode mapping
    _I2S_MODE_MAP = {
        MODE_TX: _I2S.TX,
        MODE_RX: _I2S.RX,
        MODE_TXRX: _I2S.TXRX,
    } if HAS_I2S else {}

    def __init__(self, sck: int, ws: int, sd: int,
                 mode: str = 'tx',
                 sample_rate: int = 16000,
                 bits: int = 16,
                 channels: int = 1,
                 dma_buf_len: int = 256,
                 i2s_id: int = 0):
        """
        :param sck: GPIO pin สำหรับ Serial Clock (BCLK)
        :param ws: GPIO pin สำหรับ Word Select (LRC)
        :param sd: GPIO pin สำหรับ Serial Data (DIN/DOUT)
        :param mode: 'tx' (speaker), 'rx' (mic), 'txrx' (duplex)
        :param sample_rate: sample rate (Hz): 8000, 11025, 16000, 22050, 44100, 48000
        :param bits: bit depth (16 หรือ 32)
        :param channels: จำนวนช่อง (1=mono, 2=stereo)
        :param dma_buf_len: DMA buffer size (samples), default 256
        :param i2s_id: I2S bus ID (ESP32-C3: only 0)
        """
        if not HAS_I2S:
            raise RuntimeError("machine.I2S ไม่พร้อมใช้งานบนบอร์ดนี้")

        mode_int = self._MODE_MAP.get(mode)
        if mode_int is None:
            raise ValueError(f"mode ต้องเป็น 'tx', 'rx', หรือ 'txrx' — ได้รับ '{mode}'")

        self._mode = mode
        self._mode_int = mode_int
        self._sample_rate = sample_rate
        self._bits = bits
        self._channels = channels
        self._dma_buf_len = dma_buf_len
        self._volume_pct = 100  # output volume (0–100)
        self._muted = False

        # กำหนด format (mono/stereo)
        fmt = _I2S.MONO if channels == 1 else _I2S.STEREO

        # กำหนด I2S mode
        i2s_mode = self._I2S_MODE_MAP[mode_int]

        self._i2s = _I2S(
            i2s_id,
            sck=Pin(sck),
            ws=Pin(ws),
            sd=Pin(sd),
            mode=i2s_mode,
            bits=bits,
            format=fmt,
            rate=sample_rate,
            ibuf=dma_buf_len,
        )

        mode_labels = {MODE_TX: 'TX (Speaker)', MODE_RX: 'RX (Mic)', MODE_TXRX: 'TXRX (Full Duplex)'}
        if HAS_I2S:
            mode_labels = {self.MODE_TX: 'TX (Speaker)', self.MODE_RX: 'RX (Mic)', self.MODE_TXRX: 'TXRX (Full Duplex)'}

        print(f"🎵 I2S Audio เริ่มต้น — {mode_labels.get(mode_int, mode)}, "
              f"{sample_rate}Hz, {bits}-bit, "
              f"{'Mono' if channels == 1 else 'Stereo'}")

    # ── Properties ────────────────────────────────────────

    @property
    def sample_rate(self) -> int:
        """Sample rate ปัจจุบัน (Hz)"""
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value: int):
        """เปลี่ยน sample rate"""
        self._sample_rate = value
        self._i2s.init(rate=value)
        print(f"🎵 Sample rate → {value}Hz")

    @property
    def volume(self) -> int:
        """Volume TX (0–100)"""
        return self._volume_pct

    @volume.setter
    def volume(self, pct: int):
        """ตั้งค่า volume (0–100)"""
        if not 0 <= pct <= 100:
            raise ValueError("Volume ต้องอยู่ระหว่าง 0–100")
        self._volume_pct = pct
        if pct == 0:
            self._muted = True

    @property
    def is_muted(self) -> bool:
        """สถานะ mute"""
        return self._muted

    @property
    def is_playing(self) -> bool:
        """กำลังเล่นเสียงหรือไม่ (TX mode)"""
        return self._mode_int == self.MODE_TX and not self._muted

    # ── TX (Playback) ─────────────────────────────────────

    def write(self, data: bytes):
        """
        เล่นเสียง (TX mode)

        :param data: PCM audio data (bytes)
                     - 16-bit mono: 2 bytes per sample
                     - 16-bit stereo: 4 bytes per sample (L+R interleaved)
        """
        if self._mode_int not in (self.MODE_TX, self.MODE_TXRX):
            raise RuntimeError("write() ใช้ได้เฉพาะ TX หรือ TXRX mode")

        if self._muted:
            return  # silently skip

        # Apply volume scaling
        if self._volume_pct < 100:
            data = self._apply_volume(data)

        self._i2s.write(data)

    def _apply_volume(self, data: bytes) -> bytes:
        """
        ปรับ volume โดย scale amplitude

        :param data: 16-bit PCM bytes
        :return: scaled bytes
        """
        if self._bits != 16:
            return data  # scaling supports 16-bit only

        scale = self._volume_pct / 100.0
        result = bytearray(len(data))

        for i in range(0, len(data), 2):
            # Read 16-bit signed sample (little-endian)
            sample = int.from_bytes(data[i:i + 2], 'little', True)
            scaled = int(sample * scale)
            # Write back
            result[i:i + 2] = scaled.to_bytes(2, 'little', True)

        return bytes(result)

    # ── RX (Recording) ────────────────────────────────────

    def read(self, num_samples: int) -> bytes:
        """
        บันทึกเสียง (RX mode)

        :param num_samples: จำนวน samples ที่ต้องการอ่าน
        :return: PCM audio data (bytes)
        """
        if self._mode_int not in (self.MODE_RX, self.MODE_TXRX):
            raise RuntimeError("read() ใช้ได้เฉพาะ RX หรือ TXRX mode")

        bytes_per_sample = self._bits // 8 * self._channels
        total_bytes = num_samples * bytes_per_sample
        return self._i2s.read(total_bytes)

    def read_into(self, buffer: bytearray) -> int:
        """
        บันทึกเสียงลง buffer (RX mode, zero-copy)

        :param buffer: buffer ปลายทาง
        :return: จำนวน bytes ที่อ่านได้
        """
        if self._mode_int not in (self.MODE_RX, self.MODE_TXRX):
            raise RuntimeError("read_into() ใช้ได้เฉพาะ RX หรือ TXRX mode")

        return self._i2s.readinto(buffer)

    # ── Control ───────────────────────────────────────────

    def mute(self):
        """ปิดเสียง"""
        self._muted = True

    def unmute(self):
        """เปิดเสียง"""
        self._muted = False

    def toggle_mute(self):
        """สลับ mute"""
        self._muted = not self._muted

    def deinit(self):
        """ปิด I2S และคืนทรัพยากร"""
        if self._i2s:
            self._i2s.deinit()
            self._i2s = None
            print(f"🛑 I2S Audio ปิดแล้ว")
