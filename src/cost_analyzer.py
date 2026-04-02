"""
cost_analyzer.py
================
Production Cost & Profitability Analysis — Mustard Oil Factory
Tracks seed cost, oil revenue, cake revenue, energy cost per batch.

Author: Project Engineer | Mustard Oil Factory (3 yrs exp)
"""

import datetime
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class CostRecord:
    date: str
    batch_id: str
    expeller_id: str

    # Inputs
    seed_kg: float
    seed_price_per_kg: float          # BDT/kg
    energy_kwh: float
    energy_price_per_kwh: float       # BDT/kWh
    labor_cost: float                 # BDT per shift

    # Outputs
    crude_oil_kg: float
    oil_price_per_kg: float           # BDT/kg (market)
    cake_kg: float
    cake_price_per_kg: float          # BDT/kg

    @property
    def total_input_cost(self) -> float:
        return (self.seed_kg * self.seed_price_per_kg
                + self.energy_kwh * self.energy_price_per_kwh
                + self.labor_cost)

    @property
    def total_revenue(self) -> float:
        return (self.crude_oil_kg * self.oil_price_per_kg
                + self.cake_kg * self.cake_price_per_kg)

    @property
    def gross_profit(self) -> float:
        return self.total_revenue - self.total_input_cost

    @property
    def margin_pct(self) -> float:
        if self.total_revenue == 0:
            return 0
        return round(self.gross_profit / self.total_revenue * 100, 2)

    @property
    def cost_per_litre_oil(self) -> float:
        oil_litres = self.crude_oil_kg / 0.91
        return round(self.total_input_cost / oil_litres, 2) if oil_litres > 0 else 0


class CostAnalyzer:
    """
    Production economics tracker.

    Typical Bangladesh mustard oil market (2024-25):
    - Mustard seed: BDT 70–90/kg
    - Crude mustard oil: BDT 160–200/kg
    - Mustard oil cake: BDT 18–25/kg
    - Electricity: BDT 10–12/kWh (industrial)
    """

    # Market price benchmarks (BDT)
    DEFAULT_SEED_PRICE = 82.0
    DEFAULT_OIL_PRICE = 185.0
    DEFAULT_CAKE_PRICE = 22.0
    DEFAULT_ENERGY_PRICE = 11.0
    DEFAULT_LABOR_PER_SHIFT = 1200.0

    def __init__(self):
        self.records: List[CostRecord] = []

    def analyze_batch(self, batch_id: str, expeller_id: str,
                      seed_kg: float, crude_oil_kg: float,
                      cake_kg: float, energy_kwh: float,
                      seed_price: float = None, oil_price: float = None,
                      cake_price: float = None) -> CostRecord:

        rec = CostRecord(
            date=datetime.date.today().strftime("%Y-%m-%d"),
            batch_id=batch_id,
            expeller_id=expeller_id,
            seed_kg=seed_kg,
            seed_price_per_kg=seed_price or self.DEFAULT_SEED_PRICE,
            energy_kwh=energy_kwh,
            energy_price_per_kwh=self.DEFAULT_ENERGY_PRICE,
            labor_cost=self.DEFAULT_LABOR_PER_SHIFT,
            crude_oil_kg=crude_oil_kg,
            oil_price_per_kg=oil_price or self.DEFAULT_OIL_PRICE,
            cake_kg=cake_kg,
            cake_price_per_kg=cake_price or self.DEFAULT_CAKE_PRICE,
        )
        self.records.append(rec)
        return rec

    def get_profitability_summary(self) -> Dict:
        if not self.records:
            return {}
        total_profit = sum(r.gross_profit for r in self.records)
        total_revenue = sum(r.total_revenue for r in self.records)
        total_cost = sum(r.total_input_cost for r in self.records)
        margins = [r.margin_pct for r in self.records]
        cpl = [r.cost_per_litre_oil for r in self.records]

        return {
            "total_batches": len(self.records),
            "total_revenue_BDT": round(total_revenue, 0),
            "total_cost_BDT": round(total_cost, 0),
            "total_gross_profit_BDT": round(total_profit, 0),
            "avg_margin_pct": round(sum(margins) / len(margins), 2),
            "avg_cost_per_litre_oil_BDT": round(sum(cpl) / len(cpl), 2),
            "profitable_batches": sum(1 for r in self.records if r.gross_profit > 0),
        }

    def print_cost_report(self, record: CostRecord):
        from colorama import Fore, Style, init
        init(autoreset=True)
        profit_color = Fore.GREEN if record.gross_profit > 0 else Fore.RED

        print(f"\n  💰 COST ANALYSIS: {record.batch_id}")
        print(f"  {'─'*48}")
        print(f"  Seed Cost       : BDT {record.seed_kg * record.seed_price_per_kg:>10,.0f}")
        print(f"  Energy Cost     : BDT {record.energy_kwh * record.energy_price_per_kwh:>10,.0f}")
        print(f"  Labor Cost      : BDT {record.labor_cost:>10,.0f}")
        print(f"  TOTAL INPUT     : BDT {record.total_input_cost:>10,.0f}")
        print(f"  {'─'*48}")
        print(f"  Oil Revenue     : BDT {record.crude_oil_kg * record.oil_price_per_kg:>10,.0f}")
        print(f"  Cake Revenue    : BDT {record.cake_kg * record.cake_price_per_kg:>10,.0f}")
        print(f"  TOTAL REVENUE   : BDT {record.total_revenue:>10,.0f}")
        print(f"  {'─'*48}")
        print(f"  GROSS PROFIT    : {profit_color}BDT {record.gross_profit:>10,.0f}{Style.RESET_ALL}")
        print(f"  Margin          : {profit_color}{record.margin_pct:>9.1f}%{Style.RESET_ALL}")
        print(f"  Cost/Litre Oil  : BDT {record.cost_per_litre_oil:>10.2f}")
        print()
