"""
energy_analyzer.py
==================
Energy Consumption & Efficiency Analytics for Mustard Oil Expellers
Tracks kWh per tonne of seed processed — key operational cost metric.

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import random
import datetime
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class EnergyRecord:
    date: str
    expeller_id: str
    runtime_hr: float
    motor_kw: float
    avg_load_pct: float
    kwh_consumed: float
    seed_processed_kg: float
    crude_oil_kg: float
    specific_energy_kwh_per_tonne: float   # key metric
    peak_demand_kw: float
    power_factor: float


class EnergyAnalyzer:
    """
    Tracks energy efficiency of each expeller line.
    
    Industry benchmark (mustard oil screw press):
    - Good: 35–45 kWh/tonne seed
    - Average: 45–60 kWh/tonne
    - Poor: >60 kWh/tonne
    
    High specific energy usually indicates:
    - Low throughput (idle running)
    - Worn worm/cage (more resistance)
    - Seed too dry (harder pressing)
    - Mechanical friction (bearing wear)
    """

    BENCHMARK_KWH_PER_TONNE = 45.0

    def __init__(self):
        self.records: List[EnergyRecord] = []

    def log_energy(self, expeller_id: str, motor_kw: float,
                   runtime_hr: float, seed_kg: float,
                   oil_kg: float, load_pct: float = None) -> EnergyRecord:
        """Log an energy consumption record for a production period."""
        if load_pct is None:
            load_pct = round(random.uniform(65, 90), 1)

        kwh = round(motor_kw * (load_pct / 100) * runtime_hr, 2)
        specific = round(kwh / (seed_kg / 1000), 2) if seed_kg > 0 else 0
        peak = round(motor_kw * (load_pct / 100 + random.uniform(0.05, 0.15)), 2)
        pf = round(random.uniform(0.82, 0.94), 3)

        rec = EnergyRecord(
            date=datetime.date.today().strftime("%Y-%m-%d"),
            expeller_id=expeller_id,
            runtime_hr=runtime_hr,
            motor_kw=motor_kw,
            avg_load_pct=load_pct,
            kwh_consumed=kwh,
            seed_processed_kg=seed_kg,
            crude_oil_kg=oil_kg,
            specific_energy_kwh_per_tonne=specific,
            peak_demand_kw=peak,
            power_factor=pf,
        )
        self.records.append(rec)
        return rec

    def get_energy_summary(self) -> Dict:
        if not self.records:
            return {}
        total_kwh = sum(r.kwh_consumed for r in self.records)
        total_seed = sum(r.seed_processed_kg for r in self.records)
        specifics = [r.specific_energy_kwh_per_tonne for r in self.records]
        avg_pf = sum(r.power_factor for r in self.records) / len(self.records)

        # Efficiency rating
        avg_specific = sum(specifics) / len(specifics)
        if avg_specific < 40:
            efficiency_rating = "Excellent"
        elif avg_specific < 50:
            efficiency_rating = "Good"
        elif avg_specific < 60:
            efficiency_rating = "Average"
        else:
            efficiency_rating = "Poor — investigate"

        savings_potential_kwh = max(0,
            (avg_specific - self.BENCHMARK_KWH_PER_TONNE) * total_seed / 1000)

        return {
            "total_kwh_consumed": round(total_kwh, 1),
            "total_seed_processed_tonne": round(total_seed / 1000, 2),
            "avg_specific_energy_kwh_per_tonne": round(avg_specific, 2),
            "min_specific_kwh_per_tonne": round(min(specifics), 2),
            "max_specific_kwh_per_tonne": round(max(specifics), 2),
            "benchmark_kwh_per_tonne": self.BENCHMARK_KWH_PER_TONNE,
            "efficiency_rating": efficiency_rating,
            "avg_power_factor": round(avg_pf, 3),
            "savings_potential_kwh": round(savings_potential_kwh, 1),
        }

    def print_energy_dashboard(self):
        """Print energy analytics dashboard."""
        from colorama import Fore, Style, init
        init(autoreset=True)
        summary = self.get_energy_summary()
        if not summary:
            print("  No energy records available.")
            return

        avg_se = summary['avg_specific_energy_kwh_per_tonne']
        bench = summary['benchmark_kwh_per_tonne']
        eff_color = (Fore.GREEN if avg_se < 45 else
                     Fore.YELLOW if avg_se < 60 else Fore.RED)

        print(f"\n{'='*55}")
        print(f"  ⚡ ENERGY ANALYTICS DASHBOARD")
        print(f"{'='*55}")
        print(f"  Total kWh Consumed       : {summary['total_kwh_consumed']:>10.1f}")
        print(f"  Seed Processed           : {summary['total_seed_processed_tonne']:>10.2f} tonne")
        print(f"  Avg Specific Energy      : {eff_color}{avg_se:>10.2f} kWh/tonne{Style.RESET_ALL}")
        print(f"  Benchmark                : {bench:>10.1f} kWh/tonne")
        print(f"  Efficiency Rating        : {eff_color}{summary['efficiency_rating']}{Style.RESET_ALL}")
        print(f"  Avg Power Factor         : {summary['avg_power_factor']:>10.3f}")
        if summary['savings_potential_kwh'] > 0:
            print(f"  💡 Savings Potential     : {summary['savings_potential_kwh']:>10.1f} kWh")
        print(f"{'='*55}\n")

        print(f"  📋 Recent Records:")
        print(f"  {'Expeller':<10}{'Date':<13}{'kWh':>7}  {'Spec kWh/t':>12}  {'Load%':>6}  {'PF':>5}")
        print(f"  {'─'*58}")
        for r in self.records[-8:]:
            se_c = (Fore.GREEN if r.specific_energy_kwh_per_tonne < 45 else
                    Fore.YELLOW if r.specific_energy_kwh_per_tonne < 60 else Fore.RED)
            print(f"  {r.expeller_id:<10}{r.date:<13}{r.kwh_consumed:>7.1f}  "
                  f"{se_c}{r.specific_energy_kwh_per_tonne:>12.2f}{Style.RESET_ALL}  "
                  f"{r.avg_load_pct:>6.1f}  {r.power_factor:>5.3f}")
        print()
