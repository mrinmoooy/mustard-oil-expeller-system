"""
batch_logger.py
===============
Batch Production Traceability System — Mustard Oil Factory
Complete seed-to-oil batch tracking for quality complaints and recall.

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import json
import csv
import datetime
import random
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SeedLot:
    lot_id: str
    supplier_name: str
    vehicle_no: str
    receipt_date: str
    seed_variety: str         # 'black_mustard', 'yellow_mustard', 'toria'
    quantity_kg: float
    moisture_pct: float
    oil_content_pct: float
    ffa_pct: float
    grade: str
    impurity_pct: float
    storage_bin: str
    remarks: str = ""


@dataclass
class ProductionBatch:
    batch_id: str
    date: str
    shift: str
    expeller_id: str
    seed_lot_id: str
    operator_name: str

    # Input
    seed_processed_kg: float
    seed_moisture_pct: float
    seed_temp_C: float

    # Process parameters
    start_time: str
    end_time: str
    avg_feed_rate_kg_hr: float
    avg_cage_temp_C: float
    avg_motor_current_A: float
    avg_worm_rpm: int

    # Output
    crude_oil_kg: float
    oil_yield_pct: float
    cake_kg: float
    cake_oil_residual_pct: float
    cake_moisture_pct: float

    # Quality
    oil_ffa_pct: float
    oil_moisture_pct: float
    oil_peroxide_value: float
    oil_grade: str

    # Storage
    oil_tank_id: str
    cake_dispatch_to: str      # animal feed dealer or direct customer

    remarks: str = ""
    alarms_raised: int = 0


class BatchLogger:
    """
    Complete production traceability from seed lot to oil dispatch.
    Enables root-cause analysis for quality complaints.
    """

    SUPPLIERS = [
        "Rajshahi Seed Traders", "Bogura Agro Suppliers",
        "M/s Hossain Brothers", "National Seed Store", "Padma Seed House"
    ]
    VARIETIES = ["black_mustard", "yellow_mustard", "toria"]
    OPERATORS = ["Karim", "Rahman", "Hasan", "Ali", "Molla", "Das"]
    OIL_TANKS = ["T-01", "T-02", "T-03", "T-04"]
    CAKE_BUYERS = ["Poultry Feed Ltd", "Cattle Feed Co.", "Direct Export"]

    def __init__(self):
        self.seed_lots: List[SeedLot] = []
        self.batches: List[ProductionBatch] = []
        self._lot_counter = 1
        self._batch_counter = 1

    def create_seed_lot(self, **kwargs) -> SeedLot:
        """Register an incoming seed lot with quality parameters."""
        lot_id = f"SL-{datetime.date.today().strftime('%Y%m')}-{self._lot_counter:03d}"
        moisture = kwargs.get('moisture_pct', round(random.uniform(6.0, 10.0), 1))
        oil_content = kwargs.get('oil_content_pct', round(random.uniform(36.0, 44.0), 1))
        ffa = kwargs.get('ffa_pct', round(random.uniform(0.5, 2.5), 2))
        impurity = kwargs.get('impurity_pct', round(random.uniform(0.5, 3.0), 1))

        grade = "A" if (moisture <= 7.0 and oil_content >= 40 and impurity <= 1.0) else (
                "B" if (moisture <= 8.5 and oil_content >= 38 and impurity <= 2.0) else "C")

        lot = SeedLot(
            lot_id=lot_id,
            supplier_name=kwargs.get('supplier', random.choice(self.SUPPLIERS)),
            vehicle_no=kwargs.get('vehicle_no', f"DHAKA-{random.randint(1000,9999)}"),
            receipt_date=kwargs.get('receipt_date', datetime.date.today().strftime("%Y-%m-%d")),
            seed_variety=kwargs.get('variety', random.choice(self.VARIETIES)),
            quantity_kg=kwargs.get('quantity_kg', round(random.uniform(2000, 8000), 0)),
            moisture_pct=moisture,
            oil_content_pct=oil_content,
            ffa_pct=ffa,
            grade=grade,
            impurity_pct=impurity,
            storage_bin=f"BIN-{random.randint(1,6):02d}",
            remarks=f"Grade {grade} seed — {'expedite processing' if grade == 'C' else 'standard processing'}",
        )
        self.seed_lots.append(lot)
        self._lot_counter += 1
        logger.info("Seed lot registered: %s | Grade %s | %.0f kg", lot_id, grade, lot.quantity_kg)
        return lot

    def log_batch(self, seed_lot: SeedLot, expeller_id: str,
                  shift: str = "morning") -> ProductionBatch:
        """Log a completed production batch with full traceability."""
        batch_id = f"BATCH-{datetime.date.today().strftime('%Y%m%d')}-{self._batch_counter:03d}"

        # Simulate batch parameters derived from seed lot
        moisture = seed_lot.moisture_pct
        grade_factor = {"A": 0.95, "B": 0.85, "C": 0.72}.get(seed_lot.grade, 0.85)
        feed_rate = round(random.uniform(90, 140) * grade_factor, 1)
        duration_hr = round(random.uniform(6.5, 8.5), 1)
        seed_processed = round(feed_rate * duration_hr, 1)

        # Yield
        base_yield = seed_lot.oil_content_pct * 0.84
        moist_loss = max(0, (moisture - 7.5) * 0.55)
        yield_pct = round(base_yield - moist_loss + random.gauss(0, 0.6), 2)
        yield_pct = max(26.0, min(40.0, yield_pct))

        crude_oil_kg = round(seed_processed * yield_pct / 100, 1)
        cake_kg = round(seed_processed - crude_oil_kg, 1)

        # Oil quality
        ffa = round(seed_lot.ffa_pct + random.uniform(0.1, 0.5), 3)
        oil_moisture = round(random.uniform(0.08, 0.22), 3)
        peroxide = round(random.uniform(0.8, 4.5), 2)

        oil_grade = ("Agmark Grade-1" if ffa <= 1.0 and peroxide <= 2.5
                     else "Agmark Grade-2" if ffa <= 2.0 and peroxide <= 5.0
                     else "FSSAI Edible" if ffa <= 3.0
                     else "Sub-Standard")

        start_dt = datetime.datetime.now() - datetime.timedelta(hours=duration_hr)

        batch = ProductionBatch(
            batch_id=batch_id,
            date=datetime.date.today().strftime("%Y-%m-%d"),
            shift=shift,
            expeller_id=expeller_id,
            seed_lot_id=seed_lot.lot_id,
            operator_name=random.choice(self.OPERATORS),
            seed_processed_kg=seed_processed,
            seed_moisture_pct=moisture,
            seed_temp_C=round(random.uniform(28, 42), 1),
            start_time=start_dt.strftime("%H:%M"),
            end_time=datetime.datetime.now().strftime("%H:%M"),
            avg_feed_rate_kg_hr=feed_rate,
            avg_cage_temp_C=round(random.uniform(58, 78), 1),
            avg_motor_current_A=round(random.uniform(45, 68), 1),
            avg_worm_rpm=random.randint(28, 35),
            crude_oil_kg=crude_oil_kg,
            oil_yield_pct=yield_pct,
            cake_kg=cake_kg,
            cake_oil_residual_pct=round(random.uniform(5.5, 9.0), 2),
            cake_moisture_pct=round(random.uniform(5.5, 8.5), 2),
            oil_ffa_pct=ffa,
            oil_moisture_pct=oil_moisture,
            oil_peroxide_value=peroxide,
            oil_grade=oil_grade,
            oil_tank_id=random.choice(self.OIL_TANKS),
            cake_dispatch_to=random.choice(self.CAKE_BUYERS),
            alarms_raised=random.randint(0, 3),
        )
        self.batches.append(batch)
        self._batch_counter += 1
        logger.info("Batch logged: %s | Yield %.2f%% | Grade: %s",
                    batch_id, yield_pct, oil_grade)
        return batch

    def export_to_csv(self, filepath: str = "data/production_batches.csv"):
        """Export all batch records to CSV."""
        Path("data").mkdir(exist_ok=True)
        if not self.batches:
            return
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.batches[0]).keys())
            writer.writeheader()
            for b in self.batches:
                writer.writerow(asdict(b))
        print(f"  💾 Exported {len(self.batches)} batches → {filepath}")

    def get_production_summary(self) -> Dict:
        if not self.batches:
            return {}
        total_seed = sum(b.seed_processed_kg for b in self.batches)
        total_oil = sum(b.crude_oil_kg for b in self.batches)
        total_cake = sum(b.cake_kg for b in self.batches)
        yields = [b.oil_yield_pct for b in self.batches]
        return {
            "total_batches": len(self.batches),
            "total_seed_processed_kg": round(total_seed, 1),
            "total_crude_oil_kg": round(total_oil, 1),
            "total_cake_kg": round(total_cake, 1),
            "avg_oil_yield_pct": round(sum(yields) / len(yields), 2),
            "min_yield_pct": round(min(yields), 2),
            "max_yield_pct": round(max(yields), 2),
            "grade_distribution": {
                g: sum(1 for b in self.batches if b.oil_grade == g)
                for g in set(b.oil_grade for b in self.batches)
            },
        }

    def print_batch_record(self, batch: ProductionBatch):
        """Print formatted batch production record."""
        print(f"\n{'─'*60}")
        print(f"  📦 BATCH RECORD: {batch.batch_id}")
        print(f"  Date: {batch.date}  |  Shift: {batch.shift.upper()}")
        print(f"  Expeller: {batch.expeller_id}  |  Operator: {batch.operator_name}")
        print(f"  Seed Lot: {batch.seed_lot_id}")
        print(f"{'─'*60}")
        print(f"  ── INPUTS ──")
        print(f"  Seed Processed     : {batch.seed_processed_kg:>8.1f} kg")
        print(f"  Seed Moisture      : {batch.seed_moisture_pct:>8.1f} %")
        print(f"  Feed Rate (avg)    : {batch.avg_feed_rate_kg_hr:>8.1f} kg/hr")
        print(f"  Cage Temp (avg)    : {batch.avg_cage_temp_C:>8.1f} °C")
        print(f"  Motor Current (avg): {batch.avg_motor_current_A:>8.1f} A")
        print(f"\n  ── OUTPUTS ──")
        print(f"  Crude Oil          : {batch.crude_oil_kg:>8.1f} kg")
        print(f"  Oil Yield          : {batch.oil_yield_pct:>8.2f} %")
        print(f"  Oil Cake           : {batch.cake_kg:>8.1f} kg")
        print(f"  Cake Oil Residual  : {batch.cake_oil_residual_pct:>8.2f} %")
        print(f"\n  ── OIL QUALITY ──")
        print(f"  FFA                : {batch.oil_ffa_pct:>8.3f} %")
        print(f"  Moisture           : {batch.oil_moisture_pct:>8.3f} %")
        print(f"  Peroxide Value     : {batch.oil_peroxide_value:>8.2f} meq/kg")
        print(f"  Grade              : {batch.oil_grade}")
        print(f"  Oil Stored In      : {batch.oil_tank_id}")
        print(f"  Cake Dispatched To : {batch.cake_dispatch_to}")
        if batch.alarms_raised:
            print(f"  ⚠️  Alarms During Run: {batch.alarms_raised}")
        print(f"{'─'*60}\n")
