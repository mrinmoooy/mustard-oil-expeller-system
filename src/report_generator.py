"""
report_generator.py
===================
Automated Report Generator — Mustard Oil Expeller System
Generates daily shift reports and monthly production summaries as CSV.

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import csv
import datetime
import json
from pathlib import Path
from typing import Dict, Any


class ReportGenerator:
    """Generates structured reports from system data."""

    def __init__(self):
        Path("reports").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)

    def generate_shift_report(self, expeller_summary: Dict,
                               qc_summary: Dict,
                               energy_summary: Dict,
                               production_summary: Dict,
                               maintenance_summary: Dict) -> str:
        """Generate a daily shift summary report as CSV."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        filepath = f"reports/shift_report_{today}.csv"

        rows = [
            ["MUSTARD OIL EXPELLER — DAILY SHIFT REPORT"],
            ["Date:", today],
            ["Generated:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            [],
            ["=== EXPELLER PERFORMANCE ==="],
            ["Metric", "Value"],
            ["Avg Oil Yield (%)", expeller_summary.get("avg_yield_pct", "N/A")],
            ["Min Yield (%)", expeller_summary.get("min_yield_pct", "N/A")],
            ["Max Yield (%)", expeller_summary.get("max_yield_pct", "N/A")],
            ["Avg Throughput (kg/hr)", expeller_summary.get("avg_throughput_kg_hr", "N/A")],
            ["Avg Bearing Temp (°C)", expeller_summary.get("avg_bearing_temp_C", "N/A")],
            ["Max Bearing Temp (°C)", expeller_summary.get("max_bearing_temp_C", "N/A")],
            ["Avg Motor Current (A)", expeller_summary.get("avg_motor_current_A", "N/A")],
            ["Alarm Events", expeller_summary.get("alarm_events", 0)],
            [],
            ["=== QUALITY CONTROL ==="],
            ["Metric", "Value"],
            ["Total QC Samples", qc_summary.get("total_samples", 0)],
            ["Pass Rate (%)", qc_summary.get("pass_rate_pct", "N/A")],
            ["Reject Rate (%)", qc_summary.get("reject_rate_pct", "N/A")],
            ["Avg FFA (%)", qc_summary.get("avg_ffa", "N/A")],
            ["Avg Peroxide (meq/kg)", qc_summary.get("avg_peroxide", "N/A")],
        ]

        # Grade breakdown
        if "grade_breakdown" in qc_summary:
            rows.append(["Grade Breakdown", ""])
            for grade, count in qc_summary["grade_breakdown"].items():
                rows.append([f"  {grade}", count])

        rows += [
            [],
            ["=== PRODUCTION SUMMARY ==="],
            ["Metric", "Value"],
            ["Total Batches", production_summary.get("total_batches", 0)],
            ["Seed Processed (kg)", production_summary.get("total_seed_processed_kg", 0)],
            ["Crude Oil (kg)", production_summary.get("total_crude_oil_kg", 0)],
            ["Oil Cake (kg)", production_summary.get("total_cake_kg", 0)],
            ["Avg Yield (%)", production_summary.get("avg_oil_yield_pct", "N/A")],
            [],
            ["=== ENERGY ==="],
            ["Metric", "Value"],
            ["Total kWh", energy_summary.get("total_kwh_consumed", "N/A")],
            ["Specific Energy (kWh/tonne)", energy_summary.get("avg_specific_energy_kwh_per_tonne", "N/A")],
            ["Efficiency Rating", energy_summary.get("efficiency_rating", "N/A")],
            ["Avg Power Factor", energy_summary.get("avg_power_factor", "N/A")],
            [],
            ["=== MAINTENANCE ==="],
            ["Metric", "Value"],
            ["Critical Components", maintenance_summary.get("critical_components", 0)],
            ["Service Due", maintenance_summary.get("service_due", 0)],
            ["Open Work Orders", maintenance_summary.get("open_work_orders", 0)],
            ["Est. Downtime (hr)", maintenance_summary.get("estimated_downtime_hours", 0)],
        ]

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        return filepath

    def generate_monthly_trend(self, batches_data: list) -> str:
        """Export batch-level data for monthly trend analysis."""
        today = datetime.date.today()
        filepath = f"reports/monthly_batches_{today.strftime('%Y%m')}.csv"

        if not batches_data:
            return filepath

        from dataclasses import asdict
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(batches_data[0]).keys())
            writer.writeheader()
            for b in batches_data:
                writer.writerow(asdict(b))

        return filepath

    def print_report_summary(self, all_summaries: Dict[str, Any]):
        """Print a formatted consolidated summary to console."""
        from colorama import Fore, Style, init
        init(autoreset=True)

        print(f"\n{'#'*62}")
        print(f"  🌾 MUSTARD OIL EXPELLER — CONSOLIDATED REPORT")
        print(f"  {datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
        print(f"{'#'*62}")

        sections = [
            ("⚙️  EXPELLER PERFORMANCE", "expeller", [
                ("Avg Oil Yield", "avg_yield_pct", "%"),
                ("Avg Throughput", "avg_throughput_kg_hr", "kg/hr"),
                ("Max Bearing Temp", "max_bearing_temp_C", "°C"),
                ("Alarm Events", "alarm_events", ""),
            ]),
            ("🧪 QUALITY CONTROL", "qc", [
                ("Pass Rate", "pass_rate_pct", "%"),
                ("Avg FFA", "avg_ffa", "%"),
                ("Avg Peroxide", "avg_peroxide", "meq/kg"),
            ]),
            ("📦 PRODUCTION", "production", [
                ("Total Batches", "total_batches", ""),
                ("Seed Processed", "total_seed_processed_kg", "kg"),
                ("Crude Oil", "total_crude_oil_kg", "kg"),
                ("Avg Yield", "avg_oil_yield_pct", "%"),
            ]),
            ("⚡ ENERGY", "energy", [
                ("Total kWh", "total_kwh_consumed", ""),
                ("Specific Energy", "avg_specific_energy_kwh_per_tonne", "kWh/t"),
                ("Efficiency", "efficiency_rating", ""),
            ]),
            ("🔧 MAINTENANCE", "maintenance", [
                ("Critical", "critical_components", ""),
                ("Service Due", "service_due", ""),
                ("Open WOs", "open_work_orders", ""),
            ]),
        ]

        for section_title, key, fields in sections:
            data = all_summaries.get(key, {})
            print(f"\n  {section_title}")
            print(f"  {'─'*45}")
            for label, field, unit in fields:
                val = data.get(field, "—")
                print(f"    {label:<30}: {val} {unit}")

        print(f"\n{'#'*62}\n")
