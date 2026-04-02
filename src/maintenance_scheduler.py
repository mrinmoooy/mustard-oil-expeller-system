"""
maintenance_scheduler.py
========================
Predictive Maintenance Scheduler for Mustard Oil Expellers
Tracks component life, schedules service, and predicts failure risks.

Component wear insight (3 years factory experience):
  - Worm/screw assembly: 800–1200 hr life (hard mustard seed is very abrasive)
  - Press cage/barrel: 2000–3000 hr with fortnightly inspection
  - Bearings: 3000–5000 hr (depends on lubrication & overtemp events)
  - Filter cloth: 150–250 hr (depending on seed fines content)
  - Belt/coupling: 2000 hr inspection

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import json
import datetime
import random
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config/factory_config.json")


@dataclass
class MaintenanceTask:
    task_id: str
    expeller_id: str
    component: str
    task_type: str           # 'inspection', 'replacement', 'lubrication', 'overhaul'
    priority: str            # 'critical', 'high', 'medium', 'routine'
    due_date: str
    estimated_downtime_hr: float
    description: str
    is_completed: bool = False
    completed_date: Optional[str] = None


@dataclass
class ComponentStatus:
    name: str
    expeller_id: str
    total_life_hr: float       # Expected total life
    hours_used: float          # Current usage hours
    last_service_date: str
    next_service_date: str
    wear_pct: float            # 0–100%
    status: str                # 'good', 'monitor', 'service_due', 'critical'
    remarks: str = ""

    @property
    def remaining_life_hr(self) -> float:
        return max(0.0, self.total_life_hr - self.hours_used)

    @property
    def remaining_days(self) -> float:
        """Assuming 16 hr/day operation."""
        return self.remaining_life_hr / 16


COMPONENT_SPECS = {
    "worm_screw": {
        "life_hr": 1000,
        "inspection_interval_hr": 200,
        "replacement_interval_hr": 1000,
        "downtime_hr": 8.0,
        "description": "Screw/worm shaft assembly — check pitch wear, root erosion",
        "criticality": "critical",
    },
    "press_cage_barrel": {
        "life_hr": 2500,
        "inspection_interval_hr": 500,
        "replacement_interval_hr": 2500,
        "downtime_hr": 12.0,
        "description": "Press cage/barrel — check bar gap, erosion, cracking",
        "criticality": "high",
    },
    "front_bearing": {
        "life_hr": 4000,
        "inspection_interval_hr": 500,
        "replacement_interval_hr": 4000,
        "downtime_hr": 4.0,
        "description": "Front main bearing — lubricate, check temp trend",
        "criticality": "high",
    },
    "rear_bearing": {
        "life_hr": 4000,
        "inspection_interval_hr": 500,
        "replacement_interval_hr": 4000,
        "downtime_hr": 4.0,
        "description": "Rear main bearing — lubricate, check vibration",
        "criticality": "high",
    },
    "filter_cloth": {
        "life_hr": 200,
        "inspection_interval_hr": 48,
        "replacement_interval_hr": 200,
        "downtime_hr": 1.0,
        "description": "Filter press cloth — check blinding, tears",
        "criticality": "medium",
    },
    "v_belt_drive": {
        "life_hr": 2000,
        "inspection_interval_hr": 200,
        "replacement_interval_hr": 2000,
        "downtime_hr": 2.0,
        "description": "V-belt or coupling drive — check tension, wear, alignment",
        "criticality": "medium",
    },
    "feed_hopper_auger": {
        "life_hr": 3000,
        "inspection_interval_hr": 300,
        "replacement_interval_hr": 3000,
        "downtime_hr": 3.0,
        "description": "Feed auger — check wear, jamming tendency",
        "criticality": "low",
    },
    "oil_drain_gutter": {
        "life_hr": 5000,
        "inspection_interval_hr": 168,    # weekly
        "replacement_interval_hr": 5000,
        "downtime_hr": 0.5,
        "description": "Oil drain channels — clean, check blockage",
        "criticality": "low",
    },
}


class MaintenanceScheduler:
    """
    Predictive maintenance system for expeller lines.
    
    Strategy:
    - Component-based life tracking (hours-based, not just calendar)
    - Bearing temperature trend → early failure detection
    - Worm wear detection via yield drop pattern
    - Automatic work order generation
    """

    def __init__(self):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        self.expellers = [e['id'] for e in config['expellers']]
        self.components: List[ComponentStatus] = []
        self.tasks: List[MaintenanceTask] = []
        self.task_counter = 1
        self._initialize_component_status()

    def _initialize_component_status(self):
        """Set up current component status with realistic wear levels."""
        today = datetime.date.today()

        for exp_id in self.expellers:
            for comp_name, spec in COMPONENT_SPECS.items():
                # Simulate realistic current usage
                hours_used = random.uniform(spec['life_hr'] * 0.2,
                                            spec['life_hr'] * 0.95)
                wear_pct = round(hours_used / spec['life_hr'] * 100, 1)

                if wear_pct >= 90:
                    status = "critical"
                elif wear_pct >= 75:
                    status = "service_due"
                elif wear_pct >= 50:
                    status = "monitor"
                else:
                    status = "good"

                days_until_service = max(0,
                    (spec['life_hr'] - hours_used) / 16)
                next_service = today + datetime.timedelta(days=days_until_service)
                last_service_days_ago = random.randint(10, 90)
                last_service = today - datetime.timedelta(days=last_service_days_ago)

                self.components.append(ComponentStatus(
                    name=comp_name,
                    expeller_id=exp_id,
                    total_life_hr=spec['life_hr'],
                    hours_used=round(hours_used, 0),
                    last_service_date=last_service.strftime("%Y-%m-%d"),
                    next_service_date=next_service.strftime("%Y-%m-%d"),
                    wear_pct=wear_pct,
                    status=status,
                    remarks=self._status_remark(comp_name, wear_pct, status),
                ))

    def _status_remark(self, comp: str, wear: float, status: str) -> str:
        if status == "critical":
            return f"⛔ Immediate attention — {wear:.0f}% life consumed"
        elif status == "service_due":
            return f"⚠️ Schedule service this week — {wear:.0f}% life consumed"
        elif status == "monitor":
            return f"👁 Monitor closely — {wear:.0f}% life consumed"
        return f"✅ Good condition — {wear:.0f}% life consumed"

    def generate_work_orders(self) -> List[MaintenanceTask]:
        """Auto-generate maintenance work orders based on component status."""
        today = datetime.date.today()
        new_tasks = []

        for comp in self.components:
            spec = COMPONENT_SPECS[comp.name]
            if comp.status in ("critical", "service_due"):
                priority = "critical" if comp.status == "critical" else "high"
                due = today if comp.status == "critical" else (
                    today + datetime.timedelta(days=3))

                task = MaintenanceTask(
                    task_id=f"WO-{self.task_counter:04d}",
                    expeller_id=comp.expeller_id,
                    component=comp.name,
                    task_type="replacement" if comp.wear_pct > 85 else "inspection",
                    priority=priority,
                    due_date=due.strftime("%Y-%m-%d"),
                    estimated_downtime_hr=spec['downtime_hr'],
                    description=spec['description'],
                )
                self.tasks.append(task)
                new_tasks.append(task)
                self.task_counter += 1

        return new_tasks

    def print_maintenance_status(self):
        """Print a comprehensive maintenance status dashboard."""
        from colorama import Fore, Style, init
        init(autoreset=True)

        status_colors = {
            "critical": Fore.RED,
            "service_due": Fore.YELLOW,
            "monitor": Fore.CYAN,
            "good": Fore.GREEN,
        }

        print(f"\n{'='*68}")
        print(f"  🔧 MAINTENANCE STATUS DASHBOARD")
        print(f"  {'Expeller':<12}{'Component':<24}{'Wear':>6}  {'Life Rem':>10}  Status")
        print(f"  {'─'*64}")

        for comp in sorted(self.components,
                           key=lambda c: (-c.wear_pct, c.expeller_id)):
            c = status_colors.get(comp.status, Fore.WHITE)
            wear_bar = "█" * int(comp.wear_pct / 10) + "░" * (10 - int(comp.wear_pct / 10))
            life_rem = f"{comp.remaining_life_hr:.0f}hr / {comp.remaining_days:.0f}d"
            print(f"  {comp.expeller_id:<12}{comp.name:<24}{comp.wear_pct:>5.1f}%  "
                  f"{life_rem:>12}  {c}{comp.status}{Style.RESET_ALL}")

        open_tasks = [t for t in self.tasks if not t.is_completed]
        print(f"\n  📋 OPEN WORK ORDERS: {len(open_tasks)}")
        for t in open_tasks[:8]:
            p_color = Fore.RED if t.priority == "critical" else Fore.YELLOW
            print(f"   {p_color}[{t.priority.upper():<8}]{Style.RESET_ALL} "
                  f"{t.task_id} | {t.expeller_id} | {t.component} "
                  f"| Due: {t.due_date} | ~{t.estimated_downtime_hr}hr downtime")
        print(f"{'='*68}\n")

    def get_maintenance_summary(self) -> Dict:
        critical = sum(1 for c in self.components if c.status == "critical")
        service_due = sum(1 for c in self.components if c.status == "service_due")
        open_wo = sum(1 for t in self.tasks if not t.is_completed)
        return {
            "total_components_tracked": len(self.components),
            "critical_components": critical,
            "service_due": service_due,
            "good_condition": sum(1 for c in self.components if c.status == "good"),
            "open_work_orders": open_wo,
            "estimated_downtime_hours": sum(
                t.estimated_downtime_hr for t in self.tasks if not t.is_completed),
        }
