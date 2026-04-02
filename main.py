"""
main.py  (v2.0 — Project Complete)
====================================
Mustard Oil Expeller Management System — Full Integrated Entry Point
All 8 modules: Monitor · QC · Yield ML · Maintenance · Batch · Energy · Cost · Dashboard

Usage:
    python main.py              → Full system demo
    python main.py --mode qc    → QC only
    python main.py --mode cost  → Cost analysis only
    python main.py --mode charts → Generate KPI charts
"""

import sys, os, time, argparse, datetime, json, random
sys.path.insert(0, os.path.dirname(__file__))
for d in ("logs", "data", "reports", "reports/charts"):
    os.makedirs(d, exist_ok=True)


def print_header():
    from colorama import Fore, Style, init; init(autoreset=True)
    print(f"\n{Fore.YELLOW}{'*'*64}{Style.RESET_ALL}")
    print(f"   MUSTARD OIL EXPELLER MANAGEMENT SYSTEM  v2.0")
    print(f"   Agro Gold Mustard Oil Mills | Rajshahi, Bangladesh")
    print(f"   8 Modules | ML Yield Engine | Cost Analytics | KPI Charts")
    print(f"{Fore.YELLOW}{'*'*64}{Style.RESET_ALL}")
    print(f"  {datetime.datetime.now().strftime('%A, %d %B %Y  %H:%M:%S')}\n")


def section(title):
    from colorama import Fore, Style
    print(f"\n{Fore.CYAN}{'='*64}")
    print(f"  {title}")
    print(f"{'='*64}{Style.RESET_ALL}")


def run_full():
    from src.expeller_monitor import ExpellerMonitor
    from src.quality_control import QualityControlSystem
    from src.yield_predictor import YieldPredictor, PredictionInput
    from src.maintenance_scheduler import MaintenanceScheduler
    from src.batch_logger import BatchLogger
    from src.energy_analyzer import EnergyAnalyzer
    from src.cost_analyzer import CostAnalyzer
    from src.dashboard import generate_sample_data, create_charts, print_kpi_table
    from src.report_generator import ReportGenerator

    print_header()
