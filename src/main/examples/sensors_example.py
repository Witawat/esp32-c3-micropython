"""
ตัวอย่างการใช้งาน Sensor Library
แสดงวิธี import และใช้งาน driver แต่ละตัวใน lib/sensors/
"""

import sys
sys.path.append('/lib')

import asyncio
from sensors.dht import DHTSensor
from sensors.bmp280 import BMP280
from sensors.ds18x20 import DS18B20
from sensors.mpu6050 import MPU6050
from sensors.hcsr04 import HCSR04
from sensors.ads1115 import ADS1115
from sensors.max30102 import MAX30102
from sensors.ldr import LDR
from sensors.soil import SoilMoisture
from sensors.pir import PIR
from sensors.rcwl0516 import RCWL0516
from sensors.mq_gas import MQGas
from sensors.ina219 import INA219
from sensors.oh49e import OH49E
from sensors.pzem004t import PZEM004T
from sensors.pzem004t_v3 import PZEM004Tv3
from sensors.pms7003 import PMS7003
from sensors.pms5003 import PMS5003


# ========== 1. DHT11 / DHT22 ==========
async def example_dht():
    """วัดอุณหภูมิและความชื้นด้วย DHT22"""
    print("\n" + "=" * 50)
    print("DHT22 — อุณหภูมิ + ความชื้น")
    print("=" * 50)

    sensor = DHTSensor(pin=4, model='DHT22')
    temp, hum = sensor.read()
    if temp is not None:
        print(f"🌡️ อุณหภูมิ: {temp} °C  |  💧 ความชื้น: {hum} %")
    else:
        print("❌ อ่านค่าไม่ได้ — ตรวจสอบการต่อสาย")

    # อ่านเป็น Fahrenheit
    temp_f, _ = sensor.read_fahrenheit()
    print(f"🌡️ อุณหภูมิ: {temp_f} °F")


# ========== 2. BMP280 / BME280 ==========
async def example_bmp280():
    """วัดอุณหภูมิ ความดัน (และความชื้น ถ้าเป็น BME280)"""
    print("\n" + "=" * 50)
    print("BMP280/BME280 — อุณหภูมิ + ความดัน")
    print("=" * 50)

    # I2C0: SDA=GPIO21, SCL=GPIO22, address=0x76
    sensor = BMP280(sda=21, scl=22, address=0x76)
    data = sensor.read()
    print(f"🌡️ อุณหภูมิ: {data['temperature']} °C")
    print(f"📊 ความดัน: {data['pressure']} hPa")
    if data['humidity'] is not None:
        print(f"💧 ความชื้น: {data['humidity']} %")

    alt = sensor.altitude()
    print(f"⛰️ ความสูง: {alt} เมตร")


# ========== 3. DS18B20 ==========
async def example_ds18b20():
    """วัดอุณหภูมิด้วย DS18B20 (รองรับหลายตัวบน bus เดียว)"""
    print("\n" + "=" * 50)
    print("DS18B20 — 1-Wire Temperature")
    print("=" * 50)

    sensor = DS18B20(pin=4)  # ต้องมี pull-up 4.7kΩ
    print(f"พบ sensor: {sensor.count} ตัว")

    # อ่านทุกตัวบน bus
    readings = sensor.read_all()
    for rom_hex, temp in readings:
        print(f"  ROM: {rom_hex}  →  {temp} °C")

    # อ่านตัวแรก
    temp = sensor.read(index=0)
    print(f"ตัวแรก: {temp} °C")


# ========== 4. MPU-6050 IMU ==========
async def example_mpu6050():
    """อ่านค่า Accelerometer และ Gyroscope"""
    print("\n" + "=" * 50)
    print("MPU-6050 — Accelerometer + Gyroscope")
    print("=" * 50)

    imu = MPU6050(sda=21, scl=22, address=0x68)
    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyroscope
    print(f"📐 Accel: X={ax}g  Y={ay}g  Z={az}g")
    print(f"🔄 Gyro:  X={gx}°/s  Y={gy}°/s  Z={gz}°/s")
    print(f"🌡️ Die temp: {imu.temperature} °C")


# ========== 5. HC-SR04 Ultrasonic ==========
async def example_hcsr04():
    """วัดระยะทางด้วย HC-SR04"""
    print("\n" + "=" * 50)
    print("HC-SR04 — Ultrasonic Distance")
    print("=" * 50)

    sonar = HCSR04(trig_pin=5, echo_pin=18)

    # อ่านค่าเดี่ยว
    dist = sonar.distance_cm()
    if dist:
        print(f"📏 ระยะ: {dist} cm  ({sonar.distance_mm()} mm)")
    else:
        print("⚠️ ไม่พบวัตถุในระยะ")

    # อ่านค่า median (แม่นยำกว่า)
    median = sonar.read_median(samples=5)
    print(f"📏 ระยะ median (5 samples): {median} cm")


# ========== 6. ADS1115 ADC ==========
async def example_ads1115():
    """อ่านค่า ADC 16-bit 4 ช่อง"""
    print("\n" + "=" * 50)
    print("ADS1115 — 16-bit ADC")
    print("=" * 50)

    adc = ADS1115(sda=21, scl=22, gain=2048)  # ±2.048V range
    for ch in range(4):
        v = adc.read_voltage(channel=ch)
        print(f"  CH{ch}: {v} V")


# ========== 7. MAX30102 Pulse Oximeter ==========
async def example_max30102():
    """วัด Heart Rate และ SpO2"""
    print("\n" + "=" * 50)
    print("MAX30102 — Pulse Oximeter")
    print("=" * 50)

    sensor = MAX30102(sda=21, scl=22, mode='spo2')
    print("วางนิ้วบน sensor แล้วรอ 3 วินาที...")
    await asyncio.sleep(3)

    if sensor.finger_detected():
        print("✅ พบนิ้ว — กำลังอ่านค่า")
        samples = sensor.read_samples(count=20)
        for i, (red, ir) in enumerate(samples[:5]):
            print(f"  Sample {i}: Red={red}  IR={ir}")
    else:
        print("⚠️ ไม่พบนิ้ว — วางนิ้วให้แน่นขึ้น")


# ========== 8. LDR Light Sensor ==========
async def example_ldr():
    """วัดความสว่างแสง"""
    print("\n" + "=" * 50)
    print("LDR — Light Sensor")
    print("=" * 50)

    ldr = LDR(pin=34, r_fixed=10000)
    print(f"💡 ความสว่าง: {ldr.light_level} %")
    print(f"⚡ แรงดัน: {ldr.voltage} V")
    print(f"🌑 มืด: {ldr.is_dark()}")
    print(f"📊 ค่าเฉลี่ย (10 samples): {ldr.read_average()} %")


# ========== 9. Soil Moisture ==========
async def example_soil():
    """วัดความชื้นดิน"""
    print("\n" + "=" * 50)
    print("Soil Moisture Sensor")
    print("=" * 50)

    # Calibrate: วัด raw ขณะแห้ง = 3000, ขณะจุ่มน้ำ = 1000
    soil = SoilMoisture(analog_pin=35, dry_value=3000, wet_value=1000)
    print(f"🌱 ความชื้น: {soil.moisture_percent} %")
    print(f"🏜️ แห้ง: {soil.is_dry()}")
    print(f"💧 เปียก: {soil.is_wet()}")


# ========== 10. PIR Motion ==========
async def example_pir():
    """ตรวจจับการเคลื่อนไหว"""
    print("\n" + "=" * 50)
    print("HC-SR501 PIR — Motion Detection")
    print("=" * 50)

    pir = PIR(pin=14, warmup_ms=2000)

    # ตรวจสอบแบบง่าย
    if pir.motion_detected:
        print("🚶 พบการเคลื่อนไหว!")
    else:
        print("😴 ไม่มีการเคลื่อนไหว")

    # ใช้ async watch (รัน 5 วินาที แล้วหยุด)
    async def on_motion():
        print("🚨 Motion detected!")

    async def run_watch():
        try:
            # รัน watch แบบมี timeout
            await asyncio.wait_for(
                pir.watch(interval_ms=200, on_motion=on_motion),
                timeout=5
            )
        except asyncio.TimeoutError:
            print("⏱️ หมดเวลา watch")

    await run_watch()


# ========== 11. RCWL-0516 Microwave Radar ==========
async def example_rcwl0516():
    """ตรวจจับการเคลื่อนไหวด้วยคลื่นไมโครเวฟ"""
    print("\n" + "=" * 50)
    print("RCWL-0516 — Microwave Radar Motion")
    print("=" * 50)

    radar = RCWL0516(pin=14, hold_time_ms=2000)

    # ตรวจสอบแบบง่าย
    if radar.motion_detected:
        print("📡 พบการเคลื่อนไหว!")
    else:
        print("😴 ไม่มีการเคลื่อนไหว")

    # Blocking wait (5s timeout)
    print("รอการเคลื่อนไหว 5 วินาที...")
    if radar.wait_for_motion(timeout_ms=5000):
        print("✅ พบการเคลื่อนไหว!")
    else:
        print("⏰ Timeout — ไม่พบการเคลื่อนไหว")

    # ดูเวลา motion ล่าสุด
    last = radar.last_motion_time
    if last is not None:
        print(f"Last motion: {last}ms ago")

    # Async watch (รัน 3 วินาที)
    async def on_motion():
        print("📡 Motion detected!")

    async def on_clear():
        print("   Clear")

    try:
        await asyncio.wait_for(
            radar.watch(interval_ms=100,
                        on_motion=on_motion,
                        on_clear=on_clear),
            timeout=3
        )
    except asyncio.TimeoutError:
        print("⏱️ หมดเวลา watch")

    radar.deinit()
    print("✅ RCWL-0516 example complete")


# ========== 12. MQ Gas Sensor ==========
async def example_mq_gas():
    """วัดก๊าซด้วย MQ sensor"""
    print("\n" + "=" * 50)
    print("MQ-2 — Gas Sensor")
    print("=" * 50)

    # ใช้ R0 ที่ calibrate ไว้แล้ว
    mq2 = MQGas(analog_pin=36, model='MQ2', r0=9.83)
    print(f"📡 Ratio Rs/R0: {mq2.ratio}")
    print(f"💨 LPG: {mq2.read_ppm('LPG')} ppm")
    print(f"💨 CO:  {mq2.read_ppm('CO')} ppm")

    # Calibrate ในอากาศสะอาด (ใช้เวลา ~2.5 วินาที)
    # r0 = mq2.calibrate(samples=50)

    # Digital alarm
    alarm = mq2.digital_alarm()
    if alarm is not None:
        print(f"🚨 Alarm: {alarm}")


# ========== 13. INA219 Power Monitor ==========
async def example_ina219():
    """วัดแรงดัน กระแส และกำลังไฟฟ้า"""
    print("\n" + "=" * 50)
    print("INA219 — Current/Power Monitor")
    print("=" * 50)

    ina = INA219(sda=21, scl=22, address=0x40, shunt_ohms=0.1, max_current_a=3.2)
    data = ina.read_all()
    print(f"⚡ แรงดัน: {data['bus_voltage']} V")
    print(f"📉 Shunt: {data['shunt_voltage_mv']} mV")
    print(f"🔌 กระแส: {data['current_ma']} mA")
    print(f"💡 กำลัง: {data['power_mw']} mW")

    if ina.overflow():
        print("⚠️ ค่าเกิน range!")


# ========== 14. OH49E Hall Effect ==========
async def example_oh49e():
    """ตรวจจับสนามแม่เหล็กด้วย OH49E Linear Hall Effect Sensor"""
    print("\n" + "=" * 50)
    print("OH49E — Hall Effect Sensor")
    print("=" * 50)

    hall = OH49E(pin=2, null_zone_mv=60.0)

    # Calibrate midpoint (ต้องไม่มีแม่เหล็กอยู่ใกล้)
    print("กำลัง calibrate midpoint...")
    mid = hall.calibrate_midpoint(samples=50)
    print(f"  Midpoint: {mid:.4f} V")

    # อ่านค่าพื้นฐาน
    print(f"⚡ Voltage:     {hall.voltage:.4f} V")
    print(f"📏 Deviation:   {hall.deviation_mv:+.1f} mV")
    print(f"🧲 Field:       {hall.field_strength:.3f} mT")
    print(f"🔵 Polarity:    {hall.polarity}")         # north / south / none
    print(f"❓ Magnet near: {hall.is_magnet_near()}")

    # อ่านค่าเฉลี่ย (ลด noise)
    avg = hall.read_average(samples=20)
    print(f"📊 Avg deviation (20): {avg:+.1f} mV")

    # ตรวจจับขั้วแบบ loop สั้นๆ
    print("\nตรวจจับขั้ว 5 ครั้ง (ลองเอาแม่เหล็กเข้าใกล้):")
    import time
    for i in range(5):
        pol = hall.polarity
        dev = hall.deviation_mv
        icon = {OH49E.NORTH: "🔴", OH49E.SOUTH: "🔵", OH49E.NONE: "⚪"}[pol]
        print(f"  [{i+1}] {icon} {pol:6s}  {dev:+7.1f} mV")
        time.sleep_ms(300)

    # วัด RPM (ถ้ามีล้อติดแม่เหล็ก)
    # print("\nวัด RPM (1 วินาที)...")
    # rpm = hall.measure_rpm(magnets=1, window_ms=1000)
    # print(f"⚙️ RPM: {rpm:.1f}")

    # async watch callback
    print("\nWatch 3 วินาที (เปลี่ยนขั้วเมื่อ polarity เปลี่ยน):")
    def on_change(polarity):
        icons = {OH49E.NORTH: "🔴 North", OH49E.SOUTH: "🔵 South", OH49E.NONE: "⚪ None"}
        print(f"  → {icons.get(polarity, polarity)}")

    try:
        await asyncio.wait_for(
            hall.watch(on_change, poll_ms=20),
            timeout=3
        )
    except TimeoutError:
        print("⏱️ หมดเวลา watch")


# ========== 15. PZEM-004T v1/v2 ==========
async def example_pzem004t():
    """วัดแรงดัน กระแส กำลัง และพลังงาน AC ด้วย PZEM-004T v1/v2"""
    print("\n" + "=" * 50)
    print("PZEM-004T v1/v2 — Energy Monitor")
    print("=" * 50)

    pzem = PZEM004T(tx=21, rx=20)

    # อ่านค่าเดี่ยว
    v = pzem.voltage
    i = pzem.current
    p = pzem.power
    e = pzem.energy
    pf = pzem.power_factor
    print(f"⚡ Voltage:      {v} V")
    print(f"🔌 Current:      {i} A")
    print(f"💡 Power:        {p} W")
    print(f"📦 Energy:       {e} Wh")
    print(f"📐 Power Factor: {pf}")

    # อ่านครบในครั้งเดียว
    print("\nread_all():")
    data = pzem.read_all()
    for k, v in data.items():
        print(f"  {k}: {v}")

    # async monitor (รัน 5 วินาที)
    print("\nAsync monitor 5 วินาที:")
    def on_data(data):
        if data['voltage'] is not None:
            print(f"  ⚡ {data['voltage']}V  {data['current']}A  {data['power']}W")

    try:
        await asyncio.wait_for(
            pzem.monitor(on_data, interval_s=1.5),
            timeout=5
        )
    except TimeoutError:
        print("⏱️ หมดเวลา monitor")


# ========== 16. PZEM-004T v3 (Modbus RTU) ==========
async def example_pzem004t_v3():
    """วัด Voltage/Current/Power/Energy/Frequency/PF ด้วย PZEM-004T v3"""
    print("\n" + "=" * 50)
    print("PZEM-004T v3 — Energy Monitor (Modbus RTU)")
    print("=" * 50)

    pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)

    # อ่านทุกค่าใน request เดียว (แนะนำ)
    print("read_all() — 1 request ครบทุกค่า:")
    data = pzem.read_all()
    print(f"  ⚡ Voltage:      {data['voltage']} V")
    print(f"  🔌 Current:      {data['current']} A")
    print(f"  💡 Power:        {data['power']} W")
    print(f"  📦 Energy:       {data['energy']} Wh")
    print(f"  〰️ Frequency:    {data['frequency']} Hz")
    print(f"  📐 Power Factor: {data['power_factor']}")
    print(f"  🚨 Alarm:        {data['alarm']}")

    # อ่านค่าเดี่ยว
    print(f"\nvoltage property: {pzem.voltage} V")
    print(f"frequency property: {pzem.frequency} Hz")
    print(f"power_factor property: {pzem.power_factor}")

    # ตั้ง / อ่าน alarm threshold
    pzem.set_alarm_threshold(2000)  # alarm ที่ 2000W
    thr = pzem.get_alarm_threshold()
    print(f"\nAlarm threshold: {thr} W")
    print(f"Alarm status now: {pzem.alarm_status}")

    # Reset energy counter
    # pzem.reset_energy()  # ← uncomment ถ้าต้องการ reset

    # async monitor (รัน 5 วินาที)
    print("\nAsync monitor 5 วินาที:")
    async def on_data(data):
        if data['power'] is not None:
            print(f"  ⚡ {data['voltage']}V  "
                  f"{data['current']}A  "
                  f"{data['power']}W  "
                  f"{data['frequency']}Hz  "
                  f"PF={data['power_factor']}")
            if data['alarm']:
                print("  🚨 ALARM: กำลังไฟเกิน threshold!")

    try:
        await asyncio.wait_for(
            pzem.monitor(on_data, interval_s=1.5),
            timeout=5
        )
    except TimeoutError:
        print("⏱️ หมดเวลา monitor")


# ========== 17. PMS7003 PM2.5 Sensor ==========
# async def example_pms7003():
#     """วัด PM1.0/PM2.5/PM10 ด้วย PMS7003"""
#     print("\n" + "=" * 50)
#     print("PMS7003 — PM2.5 Air Quality (Compact)")
#     print("=" * 50)
#
#     pms = PMS7003(rx=16, tx=17, mode='active')
#     data = pms.read()
#     if data:
#         print(f"🌫️ PM1.0: {data.pm1_0_atm} µg/m³")
#         print(f"🌫️ PM2.5: {data.pm2_5_atm} µg/m³")
#         print(f"🌫️ PM10:  {data.pm10_atm} µg/m³")
#         print(f"🔬 Particles >0.3µm: {data.particles_03um}")
#         print(f"🔬 Particles >2.5µm: {data.particles_25um}")
#     else:
#         print("❌ อ่านค่าไม่ได้ — ตรวจสอบการต่อสาย")


# ========== 18. PMS5003 PM2.5 Sensor ==========
# async def example_pms5003():
#     """วัด PM1.0/PM2.5/PM10 ด้วย PMS5003 (median filter)"""
#     print("\n" + "=" * 50)
#     print("PMS5003 — PM2.5 Air Quality (Standard)")
#     print("=" * 50)
#
#     pms = PMS5003(rx=16, tx=17, mode='active')
#     print("⏳ Warming up 30 วินาที...")
#     pms.warmup()
#
#     # อ่านหลายครั้ง ใช้ median ลด noise
#     data = pms.read_multiple(count=5, delay_ms=200)
#     if data:
#         print(f"🌫️ PM1.0: {data.pm1_0_atm} µg/m³")
#         print(f"🌫️ PM2.5: {data.pm2_5_atm} µg/m³")
#         print(f"🌫️ PM10:  {data.pm10_atm} µg/m³")
#
#         # Simple AQI
#         aqi = (data.pm2_5_atm / 12.0 * 50)
#         level = ("🟢 Good" if aqi <= 50 else "🟡 Moderate" if aqi <= 100
#                  else "🟠 Unhealthy")
#         print(f"📊 AQI: {aqi:.0f} ({level})")
#     else:
#         print("❌ อ่านค่าไม่ได้ — ตรวจสอบการต่อสาย")


# ========== Main: รัน example ทั้งหมด ==========
async def main():
    print("🚀 เริ่มต้น Sensor Examples\n")
    # เปิด/ปิด comment example ที่ต้องการทดสอบ
    await example_dht()
    # await example_bmp280()
    # await example_ds18b20()
    # await example_mpu6050()
    # await example_hcsr04()
    # await example_ads1115()
    # await example_max30102()
    # await example_ldr()
    # await example_soil()
    # await example_pir()
    # await example_rcwl0516()
    # await example_mq_gas()
    # await example_ina219()
    # await example_oh49e()
    # await example_pzem004t()
    # await example_pzem004t_v3()
    # await example_pms7003()    # uncomment เมื่อต่อวงจร
    # await example_pms5003()
    print("\n✅ จบการทดสอบ")


asyncio.run(main())
