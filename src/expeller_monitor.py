"""
expeller_monitor.py
===================
Senior Researcher Module — Mustard Oil Expeller Performance Monitor
Tracks real-time and historical operational parameters for screw press expellers.

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import json
import random
import logging
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(
    filename='logs/expeller_monitor.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

CONFIG_PATH = Path("config/factory_config.json")


@dataclass
class ExpellerReading:
    """Single snapshot of expeller operating conditions."""
    timestamp: str
    expeller_id: str
    feed_rate_kg_hr: float          # Seed input rate
    throughput_kg_hr: float         # Actual processed rate
    oil_flow_ltr_hr: float          # Oil output
    cake_output_kg_hr: float        # Oil cake output
    motor_current_A: float          # Motor ampere draw
    motor_voltage_V: float          # Supply voltage
    bearing_temp_front_C: float     # Front bearing temperature
    bearing_temp_rear_C: float      # Rear bearing temperature
    worm_shaft_rpm: int             # Screw shaft rotation
    press_cage_temp_C: float        # Press cage temperature
    oil_yield_pct: float            # Oil yield as % of seed
    alarm_flags: List[str] = field(default_factory=list)


class ExpellerMonitor:
    """
    Core monitoring engine for mustard oil screw press expellers.
    
    Factory context:
    - Processes black mustard (Brassica nigra) and yellow mustard
    - Two-stage pressing: pre-press (cold) + main press (warm, 60-70°C)
    - Target yield: 32–36% for Grade-A seed
    """

    def __init__(self):
        with open(CONFIG_PATH) as f:
            self.config = json.load(f)
        self.expellers = {e['id']: e for e in self.config['expellers']}
        self.thresholds = self.config['thresholds']
        self.history: List[ExpellerReading] = []
        logging.info("ExpellerMonitor initialized for %d expeller lines",
                     len(self.expellers))

    def simulate_reading(self, expeller_id: str, seed_grade: str = "B",
                         seed_moisture: float = 8.0) -> ExpellerReading:
        """
        Simulate a realistic sensor reading for a given expeller.
        In production, replace with actual PLC/SCADA data feed.
        
        Seed moisture heavily impacts yield:
          - Optimal: 6.5–8.0% → best oil extraction
          - High (>10%): reduces yield, increases cake moisture
          - Low (<6%): oil quality good but higher wear
        """
        exp = self.expellers.get(expeller_id)
        if not exp:
            raise ValueError(f"Unknown expeller ID: {expeller_id}")

        max_tp = exp['max_throughput_kg_hr']
        motor_kw = exp['motor_kw']

        # Throughput varies with seed grade and moisture
        grade_factor = {"A": 0.95, "B": 0.85, "C": 0.72}.get(seed_grade, 0.85)
        moisture_penalty = max(0, (seed_moisture - 8.0) * 0.8)
        throughput = round(max_tp * grade_factor - moisture_penalty + random.gauss(0, 3), 1)
        throughput = max(60.0, min(throughput, max_tp))

        # Yield calculation — core metric
        base_yield = {"A": 36.5, "B": 33.5, "C": 30.0}.get(seed_grade, 33.0)
        moisture_yield_loss = max(0, (seed_moisture - 7.5) * 0.6)
        oil_yield = round(base_yield - moisture_yield_loss + random.gauss(0, 0.8), 2)
        oil_yield = max(22.0, min(oil_yield, 42.0))

        oil_flow = round(throughput * oil_yield / 100 * 0.91, 1)   # density ~0.91 kg/L
        cake_output = round(throughput * (1 - oil_yield / 100), 1)

        # Motor load increases with throughput and seed hardness
        base_current = motor_kw / 0.415 * 1.05
        current = round(base_current * (throughput / max_tp) + random.gauss(0, 2), 1)

        # Bearing temps — rise with load and ambient temperature
        ambient = 34.0  # typical factory floor, Bangladesh summer
        front_temp = round(ambient + 38 + (throughput / max_tp) * 18 + random.gauss(0, 2), 1)
        rear_temp = round(front_temp - 4 + random.gauss(0, 1.5), 1)

        cage_temp = round(55 + (throughput / max_tp) * 22 + random.gauss(0, 3), 1)
        rpm = int(exp.get('worm_rpm', 30) if 'worm_rpm' in exp else
                  (30 if exp['stages'] == 2 else 35) + random.randint(-2, 2))

        reading = ExpellerReading(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            expeller_id=expeller_id,
            feed_rate_kg_hr=round(throughput + random.gauss(0, 1.5), 1),
            throughput_kg_hr=throughput,
            oil_flow_ltr_hr=oil_flow,
            cake_output_kg_hr=cake_output,
            motor_current_A=current,
            motor_voltage_V=round(415 + random.gauss(0, 5), 1),
            bearing_temp_front_C=front_temp,
            bearing_temp_rear_C=rear_temp,
            worm_shaft_rpm=rpm,
            press_cage_temp_C=cage_temp,
            oil_yield_pct=oil_yield,
        )

        reading.alarm_flags = self._check_alarms(reading)
        self.history.append(reading)

        if reading.alarm_flags:
            logging.warning("ALARMS on %s: %s", expeller_id,
                            ", ".join(reading.alarm_flags))
        return reading

    def _check_alarms(self, r: ExpellerReading) -> List[str]:
        """Evaluate sensor readings against factory alarm thresholds."""
        alarms = []
        t = self.thresholds

        if r.bearing_temp_front_C >= t['bearing_temp_critical']:
            alarms.append("🔴 CRITICAL: Front bearing overtemp")
        elif r.bearing_temp_front_C >= t['bearing_temp_warning']:
            alarms.append("🟡 WARN: Front bearing temp high")

        if r.bearing_temp_rear_C >= t['bearing_temp_critical']:
            alarms.append("🔴 CRITICAL: Rear bearing overtemp")
        elif r.bearing_temp_rear_C >= t['bearing_temp_warning']:
            alarms.append("🟡 WARN: Rear bearing temp high")

        if r.motor_current_A >= t['motor_current_critical']:
            alarms.append("🔴 CRITICAL: Motor overcurrent — stop immediately")
        elif r.motor_current_A >= t['motor_current_warning']:
            alarms.append("🟡 WARN: Motor current approaching limit")

        if r.oil_yield_pct < t['yield_critical']:
            alarms.append("🔴 CRITICAL: Oil yield below 28% — check seed/press")
        elif r.oil_yield_pct < t['yield_low_warning']:
            alarms.append("🟡 WARN: Oil yield below target")

        if r.press_cage_temp_C > 90:
            alarms.append("🟡 WARN: Press cage temperature elevated")

        return alarms

    def get_summary(self, expeller_id: Optional[str] = None) -> Dict:
        """Return performance summary for one or all expellers."""
        records = [r for r in self.history
                   if expeller_id is None or r.expeller_id == expeller_id]
        if not records:
            return {}

        yields = [r.oil_yield_pct for r in records]
        temps = [r.bearing_temp_front_C for r in records]
        currents = [r.motor_current_A for r in records]
        throughputs = [r.throughput_kg_hr for r in records]

        return {
            "expeller": expeller_id or "ALL",
            "readings_count": len(records),
            "avg_yield_pct": round(sum(yields) / len(yields), 2),
            "min_yield_pct": round(min(yields), 2),
            "max_yield_pct": round(max(yields), 2),
            "avg_throughput_kg_hr": round(sum(throughputs) / len(throughputs), 1),
            "avg_bearing_temp_C": round(sum(temps) / len(temps), 1),
            "max_bearing_temp_C": round(max(temps), 1),
            "avg_motor_current_A": round(sum(currents) / len(currents), 1),
            "alarm_events": sum(1 for r in records if r.alarm_flags),
        }

    def print_live_dashboard(self, reading: ExpellerReading):
        """Print formatted live console dashboard for an expeller reading."""
        from colorama import Fore, Style, init
        init(autoreset=True)

        print(f"\n{'='*60}")
        print(f"  📟 EXPELLER MONITOR — {reading.expeller_id}")
        print(f"  🕐 {reading.timestamp}")
        print(f"{'='*60}")
        print(f"  Feed Rate      : {reading.feed_rate_kg_hr:>7.1f} kg/hr")
        print(f"  Throughput     : {reading.throughput_kg_hr:>7.1f} kg/hr")
        print(f"  Oil Flow       : {reading.oil_flow_ltr_hr:>7.1f} L/hr")
        print(f"  Cake Output    : {reading.cake_output_kg_hr:>7.1f} kg/hr")
        print(f"  Worm Shaft RPM : {reading.worm_shaft_rpm:>7d} rpm")
        print(f"  Press Cage Temp: {reading.press_cage_temp_C:>7.1f} °C")
        print()

        # Color-coded yield
        y = reading.oil_yield_pct
        color = Fore.GREEN if y >= 33 else (Fore.YELLOW if y >= 30 else Fore.RED)
        print(f"  Oil Yield      : {color}{y:>7.2f} %{Style.RESET_ALL}")

        # Color-coded bearing temps
        bt = reading.bearing_temp_front_C
        bc = Fore.GREEN if bt < 80 else (Fore.YELLOW if bt < 90 else Fore.RED)
        print(f"  Bearing Temp F : {bc}{bt:>7.1f} °C{Style.RESET_ALL}")
        print(f"  Bearing Temp R : {bc}{reading.bearing_temp_rear_C:>7.1f} °C{Style.RESET_ALL}")

        mc = reading.motor_current_A
        mcolor = Fore.GREEN if mc < 60 else (Fore.YELLOW if mc < 72 else Fore.RED)
        print(f"  Motor Current  : {mcolor}{mc:>7.1f} A{Style.RESET_ALL}  "
              f"({reading.motor_voltage_V:.0f} V)")

        if reading.alarm_flags:
            print(f"\n  {'─'*40}")
            print(f"  ⚠️  ACTIVE ALARMS:")
            for a in reading.alarm_flags:
                print(f"     {a}")
        else:
            print(f"\n  {Fore.GREEN}  ✅ All parameters NORMAL{Style.RESET_ALL}")
        print(f"{'='*60}\n")
