# Plan — Stepper Motor Drivers & PM2.5 Sensors Expansion

> **Date**: 2026-05-01  
> **Project**: ESP32 MicroPython Library  
> **Branch**: feature/stepper-pm25-expansion

---

## Overview

ขยาย `lib/output/` ด้วย stepper motor drivers 4 ตัว (A4988, TMC2208/TMC2209, DRV8825, TMC5160) และขยาย `lib/sensors/` ด้วย PM2.5 sensors 2 ตัว (PMS7003, PMS5003) พร้อมอัปเดต documentation และ examples

### Design Decisions

| ข้อ | Decision | เหตุผล |
|-----|----------|--------|
| แยกไฟล์ per driver | แยก A4988, TMC2208, DRV8825, TMC5160 เป็นคนละไฟล์ | แต่ละตัวมี register/pinout/config ต่างกัน — แยก maintain ง่าย, pattern เดียวกับ PZEM v1/v2 vs v3 |
| PMS parsing shared | สร้าง `_pms_base.py` (private) สำหรับ parse 32-byte frame | PMS7003/PMS5003 ใช้ protocol frame เดียวกัน — ลด code duplication |
| TMC2208+2209 รวม | รวมใน `stepper_tmc2208.py` ไฟล์เดียว | TMC2209 เป็น superset ของ TMC2208 — `StepperTMC2209` extends `StepperTMC2208` |
| คง `stepper.py` ไว้ | เหลือเฉพาะ `StepperULN2003` (28BYJ-48) | ยังมีประโยชน์สำหรับมือใหม่/ราคาถูก |
| Advanced features | Implement พื้นฐานก่อน + docstring สำหรับ register direct access | TMC5160 มี 100+ registers — implement `write_reg()`/`read_reg()` ให้ user เข้าถึง advanced features ได้ |

---

## Phase A: Stepper Motor Drivers

| # | ไฟล์ | คลาส | Hardware | Interface | Microstepping |
|---|------|------|----------|-----------|---------------|
| A.1 | `stepper_a4988.py` | `StepperA4988` | A4988 | STEP/DIR + MS1/MS2/MS3 | Full, 1/2, 1/4, 1/8, 1/16 |
| A.2 | `stepper_tmc2208.py` | `StepperTMC2208`, `StepperTMC2209` | TMC2208/TMC2209 | STEP/DIR + UART (1-wire) | Up to 1/256 |
| A.3 | `stepper_drv8825.py` | `StepperDRV8825` | DRV8825 | STEP/DIR + M0/M1/M2 | Full, 1/2, 1/4, 1/8, 1/16, 1/32 |
| A.4 | `stepper_tmc5160.py` | `StepperTMC5160` | TMC5160 | SPI + STEP/DIR | Up to 1/256 |
| A.5 | `stepper.py` | `StepperULN2003` | 28BYJ-48 (unchanged) | 4-wire GPIO | Half/Full step |

### Tasks
- [ ] A.1 Create `lib/output/stepper_a4988.py`
- [ ] A.2 Create `lib/output/stepper_tmc2208.py`
- [ ] A.3 Create `lib/output/stepper_drv8825.py`
- [ ] A.4 Create `lib/output/stepper_tmc5160.py`
- [ ] A.5 Update `lib/output/stepper.py` — remove `StepperStepDir`, keep `StepperULN2003`
- [ ] A.6 Update `lib/output/__init__.py` — add 4 new imports

---

## Phase B: PM2.5 Sensors

| # | ไฟล์ | คลาส | Hardware | Interface | Protocol |
|---|------|------|----------|-----------|----------|
| B.1 | `_pms_base.py` | `_PMSBase` (private) | — | UART | 32-byte frame parser |
| B.2 | `pms7003.py` | `PMS7003` | PMS7003 | UART (9600bps) | Active/Passive mode |
| B.3 | `pms5003.py` | `PMS5003` | PMS5003 | UART (9600bps) | Active/Passive mode + warmup |

### Tasks
- [ ] B.1 Create `lib/sensors/_pms_base.py` — shared 32-byte frame parser
- [ ] B.2 Create `lib/sensors/pms7003.py`
- [ ] B.3 Create `lib/sensors/pms5003.py`
- [ ] B.4 Update `lib/sensors/__init__.py` — add PMS7003, PMS5003

---

## Phase C: Documentation & Examples

### Tasks
- [ ] C.1 Update `lib/output/README.md` — add stepper driver sections with 3-tier examples
- [ ] C.2 Update `lib/sensors/README.md` — add PMS sensor sections with 3-tier examples
- [ ] C.3 Update `main/examples/output_example.py` — add stepper examples
- [ ] C.4 Update `main/examples/sensors_example.py` — add PMS examples
- [ ] C.5 Update `lib/README.md` — update module counts
- [ ] C.6 Update `Task.md` — add new tasks

---

## Module Summary (หลังขยาย)

| Category | Modules | Change |
|----------|---------|--------|
| Output | 7 → 11 | +4 stepper drivers |
| Sensors | 15 → 17 | +2 PM sensors (+1 base) |
| **Total** | **48 → 54** | **+6 files** |

---

## Verification Checklist

- [ ] All imports work: `from output.stepper_a4988 import StepperA4988` (and others)
- [ ] PMS frame parser: `parse_pms_frame(32_bytes)` returns correct PM1.0/PM2.5/PM10
- [ ] A4988: `rotate(360)` produces correct step count with microstepping
- [ ] TMC2208: UART CRC check passes for register read/write
- [ ] DRV8825: 1/32 microstepping works (M0/M1/M2 = HIGH/HIGH/HIGH)
- [ ] TMC5160: SPI read IOIN register returns correct value
- [ ] READMEs: all sections have parameter table + 🟢/🟡/🔴 examples
- [ ] Task.md: all checkboxes reflect correct status
