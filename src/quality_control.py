"""
quality_control.py
==================
Mustard Oil Quality Control & Grading System
Tracks FFA, moisture, peroxide value, colour, and other parameters
against FSSAI / IS-546 / Agmark standards.

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import random
import datetime
import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


# ─── FSSAI / IS-546 STANDARDS ───────────────────────────────────────────────
STANDARDS = {
    "fssai_edible": {
        "ffa_max": 2.0,
        "moisture_max": 0.20,
        "peroxide_max": 5.0,
        "iodine_min": 94,
        "iodine_max": 105,
        "saponification_min": 170,
        "saponification_max": 184,
        "colour_lovibond_max_red": 5.0,
        "refractive_index_40C": (1.465, 1.467),
    },
    "agmark_grade1": {
        "ffa_max": 1.0,
        "moisture_max": 0.15,
        "peroxide_max": 2.5,
        "iodine_min": 94,
        "iodine_max": 105,
    },
    "agmark_grade2": {
        "ffa_max": 2.0,
        "moisture_max": 0.20,
        "peroxide_max": 5.0,
        "iodine_min": 94,
        "iodine_max": 105,
    },
}


@dataclass
class QCSample:
    """A quality control lab sample result."""
    sample_id: str
    batch_id: str
    expeller_id: str
    timestamp: str
    sample_type: str          # 'crude_oil', 'filtered_oil', 'cake'

    # Oil parameters
    ffa_pct: float            # Free Fatty Acid (as oleic acid)
    moisture_pct: float       # Karl Fischer moisture
    peroxide_value: float     # meq O2/kg
    iodine_value: float       # Wijs method
    saponification_value: float
    refractive_index: float
    colour_lovibond_red: float
    specific_gravity: float

    # Cake parameters (if applicable)
    cake_oil_residual_pct: float   # Soxhlet extraction
    cake_moisture_pct: float
    cake_protein_pct: float

    # Derived
    grade: str = ""
    remarks: List[str] = None

    def __post_init__(self):
        self.remarks = self.remarks or []
        self.grade = self._determine_grade()

    def _determine_grade(self) -> str:
        if (self.ffa_pct <= STANDARDS["agmark_grade1"]["ffa_max"] and
                self.peroxide_value <= STANDARDS["agmark_grade1"]["peroxide_max"] and
                self.moisture_pct <= STANDARDS["agmark_grade1"]["moisture_max"]):
            return "Agmark Grade-1"
        elif (self.ffa_pct <= STANDARDS["agmark_grade2"]["ffa_max"] and
              self.peroxide_value <= STANDARDS["agmark_grade2"]["peroxide_max"]):
            return "Agmark Grade-2"
        elif (self.ffa_pct <= STANDARDS["fssai_edible"]["ffa_max"] and
              self.moisture_pct <= STANDARDS["fssai_edible"]["moisture_max"]):
            return "FSSAI Edible"
        else:
            return "Sub-Standard / Reject"


class QualityControlSystem:
    """
    Quality Control system for mustard oil production.
    
    Key tests performed at factory:
    1. FFA — measured every 2 hours per expeller
    2. Moisture — before and after filtration
    3. Peroxide Value — daily for stored oil
    4. Organoleptic — colour, smell (every batch)
    5. Iodine Value — weekly / per consignment
    
    High FFA causes:
      - Old/damaged seed
      - Excessive heat during pressing (cage temp > 85°C)
      - Delayed processing after seed receipt
      - Microbial contamination in stored seed
    """

    def __init__(self):
        self.samples: List[QCSample] = []
        self.sample_counter = 1

    def generate_sample(self, batch_id: str, expeller_id: str,
                        sample_type: str = "crude_oil",
                        seed_age_days: int = 5,
                        cage_temp: float = 68.0,
                        seed_ffa_pct: float = 0.8) -> QCSample:
        """
        Generate a realistic QC sample result.
        
        Key relationships modelled from factory experience:
        - FFA rises with seed age, high cage temp, poor seed quality
        - Peroxide rises with storage time and light/air exposure
        - Iodine value is relatively stable for mustard (~94–105)
        - Refractive index varies narrowly (41°C measurement)
        """
        # FFA influenced by seed age and processing temp
        temp_ffa_boost = max(0, (cage_temp - 70) * 0.04)
        age_ffa_boost = seed_age_days * 0.03
        ffa = round(seed_ffa_pct + temp_ffa_boost + age_ffa_boost +
                    random.gauss(0, 0.12), 3)
        ffa = max(0.3, ffa)

        # Moisture — crude oil typically 0.1–0.3%
        moisture = round(random.uniform(0.08, 0.28) +
                         (0.05 if cage_temp < 60 else 0), 3)

        # Peroxide value — fresh pressed oil is typically low
        peroxide = round(random.uniform(0.5, 3.5) +
                         (seed_age_days * 0.08), 2)
        peroxide = max(0.3, peroxide)

        iodine = round(random.uniform(96, 104), 1)
        sap = round(random.uniform(172, 182), 1)
        ri = round(random.uniform(1.4650, 1.4670), 4)
        colour_red = round(random.uniform(2.5, 6.0), 1)
        sg = round(random.uniform(0.910, 0.920), 4)

        # Cake quality
        cake_oil = round(random.uniform(5.0, 9.5) +
                         (2.0 if cage_temp < 55 else 0), 2)   # lower temp = more oil in cake
        cake_moisture = round(random.uniform(5.5, 9.0), 2)
        cake_protein = round(random.uniform(32.0, 37.0), 1)

        sample = QCSample(
            sample_id=f"QC-{self.sample_counter:04d}",
            batch_id=batch_id,
            expeller_id=expeller_id,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_type=sample_type,
            ffa_pct=ffa,
            moisture_pct=moisture,
            peroxide_value=peroxide,
            iodine_value=iodine,
            saponification_value=sap,
            refractive_index=ri,
            colour_lovibond_red=colour_red,
            specific_gravity=sg,
            cake_oil_residual_pct=cake_oil,
            cake_moisture_pct=cake_moisture,
            cake_protein_pct=cake_protein,
        )

        sample.remarks = self._generate_remarks(sample, cage_temp, seed_age_days)
        self.samples.append(sample)
        self.sample_counter += 1
        return sample

    def _generate_remarks(self, s: QCSample, cage_temp: float,
                          seed_age: int) -> List[str]:
        remarks = []
        if s.ffa_pct > 3.0:
            remarks.append("⚠️ High FFA — check seed quality and age")
        elif s.ffa_pct > 2.0:
            remarks.append("🔸 Elevated FFA — monitor closely")
        if s.peroxide_value > 5.0:
            remarks.append("⚠️ High peroxide — review storage/oxidation")
        if s.moisture_pct > 0.20:
            remarks.append("🔸 Moisture above limit — filtration needed")
        if s.cake_oil_residual_pct > 8.0:
            remarks.append("⚠️ High oil in cake — adjust press pressure/worm clearance")
        if cage_temp > 80:
            remarks.append("🌡️ High cage temp may elevate FFA and damage tocopherols")
        if seed_age > 20:
            remarks.append("📅 Old seed batch — expedite processing")
        if not remarks:
            remarks.append("✅ All parameters within spec")
        return remarks

    def get_pass_fail_summary(self) -> Dict:
        """Summary of QC pass/fail rate."""
        total = len(self.samples)
        if total == 0:
            return {}
        grades = {}
        for s in self.samples:
            grades[s.grade] = grades.get(s.grade, 0) + 1
        reject = grades.get("Sub-Standard / Reject", 0)
        return {
            "total_samples": total,
            "grade_breakdown": grades,
            "pass_rate_pct": round((total - reject) / total * 100, 1),
            "reject_rate_pct": round(reject / total * 100, 1),
            "avg_ffa": round(sum(s.ffa_pct for s in self.samples) / total, 3),
            "avg_peroxide": round(sum(s.peroxide_value for s in self.samples) / total, 2),
        }

    def print_sample_report(self, sample: QCSample):
        """Pretty-print a QC sample report to console."""
        from colorama import Fore, Style, init
        init(autoreset=True)

        grade_color = {
            "Agmark Grade-1": Fore.GREEN,
            "Agmark Grade-2": Fore.CYAN,
            "FSSAI Edible": Fore.YELLOW,
            "Sub-Standard / Reject": Fore.RED,
        }.get(sample.grade, Fore.WHITE)

        print(f"\n{'─'*55}")
        print(f"  🧪 QC SAMPLE: {sample.sample_id}  |  Batch: {sample.batch_id}")
        print(f"  Expeller: {sample.expeller_id}  |  {sample.timestamp}")
        print(f"  Type: {sample.sample_type.upper()}")
        print(f"{'─'*55}")

        ffa_c = Fore.GREEN if sample.ffa_pct < 1.0 else (
            Fore.YELLOW if sample.ffa_pct < 2.0 else Fore.RED)
        print(f"  FFA (% oleic)       : {ffa_c}{sample.ffa_pct:>7.3f} %{Style.RESET_ALL}")
        print(f"  Moisture            : {sample.moisture_pct:>7.3f} %")
        print(f"  Peroxide Value      : {sample.peroxide_value:>7.2f} meq/kg")
        print(f"  Iodine Value        : {sample.iodine_value:>7.1f}")
        print(f"  Saponification Val  : {sample.saponification_value:>7.1f}")
        print(f"  Refractive Index    : {sample.refractive_index:>9.4f}")
        print(f"  Colour (Lovibond R) : {sample.colour_lovibond_red:>7.1f}")
        print(f"  Specific Gravity    : {sample.specific_gravity:>9.4f}")
        print(f"\n  Cake Oil Residual   : {sample.cake_oil_residual_pct:>7.2f} %")
        print(f"  Cake Moisture       : {sample.cake_moisture_pct:>7.2f} %")
        print(f"  Cake Protein        : {sample.cake_protein_pct:>7.1f} %")
        print(f"\n  GRADE: {grade_color}{sample.grade}{Style.RESET_ALL}")
        print(f"\n  Remarks:")
        for r in sample.remarks:
            print(f"    {r}")
        print(f"{'─'*55}\n")
