# P10 LED Display Library
# ใช้งาน: from p10 import P10Mono, P10RGB, P10Chain
#
# p10_hub75   → HUB75Engine               (Low-level HUB75 protocol via RMT+GPIO)
# p10_buffer  → MonoBuffer, RGBBuffer      (Frame buffers)
# p10_display → P10Mono, P10RGB, P10Chain  (High-level display API)
#
# รองรับ: ESP32 / ESP32-S2 / ESP32-C3 (RMT-based, no LCD/DMA required)
# Protocol: HUB75 (14-pin standard)
# Panel: P10 32×16 (1/4 scan), 64×32 (1/16 scan)
# Mode: Monochrome, RGB Full Color, Chained panels

from p10.p10_hub75 import HUB75Engine
from p10.p10_buffer import MonoBuffer, RGBBuffer
from p10.p10_display import P10Mono, P10RGB, P10Chain
