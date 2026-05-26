"""
I2S Audio Module สำหรับ ESP32-C3 (MicroPython)
รองรับ speaker output (TX), microphone input (RX), และ duplex (TXRX)

วิธีใช้งาน:
    from audio import I2SAudio
    audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx', sample_rate=16000)
    audio.write(audio_data)
"""

from audio.i2s_audio import I2SAudio
