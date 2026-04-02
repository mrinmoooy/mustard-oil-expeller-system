# mustard-oil-expeller-system
Python-based production management system for mustard oil screw press factories — 8 modules including ML yield prediction, QC tracking, predictive maintenance, and KPI dashboard
# 🌾 Mustard Oil Expeller Management System
### Industrial Research & Monitoring Platform | v1.0.0

> Built from 3 years of hands-on experience at a mustard oil processing facility.  
> Designed for expeller operators, quality engineers, and factory managers.

---

## 📋 Overview

This Python project provides a complete data-driven management system for **mustard oil cold/hot expeller operations**, covering:

- Real-time expeller performance monitoring
- Oil yield prediction using ML regression
- Quality control (FFA, moisture, peroxide value tracking)
- Maintenance scheduling with predictive alerts
- Batch production logs and traceability
- Automated PDF/CSV report generation
- Energy consumption analytics
- Seed-to-oil efficiency benchmarking

---

## 🏗️ Project Structure

```
mustard_oil_expeller/
│
├── src/
│   ├── expeller_monitor.py       # Core expeller performance engine
│   ├── quality_control.py        # QC parameter tracking & grading
│   ├── yield_predictor.py        # ML-based oil yield prediction
│   ├── maintenance_scheduler.py  # Predictive maintenance system
│   ├── batch_logger.py           # Batch production traceability
│   ├── energy_analyzer.py        # Power & energy consumption analytics
│   └── report_generator.py       # Automated reporting module
│
├── data/
│   ├── sample_batches.csv        # Sample historical batch data
│   └── seed_grades.json          # Mustard seed grade specifications
│
├── config/
│   └── factory_config.json       # Factory-specific configuration
│
├── tests/
│   └── test_all_modules.py       # Unit tests for all modules
│
├── logs/                         # Auto-generated operational logs
├── reports/                      # Auto-generated reports output
│
├── main.py                       # CLI entry point — run everything here
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
# Clone or download the project
cd mustard_oil_expeller

# Install dependencies
pip install -r requirements.txt

# Run the full system
python main.py
```

---

## 🚀 Quick Start

```bash
# Run complete simulation with all modules
python main.py --mode full

# Run only quality control analysis
python main.py --mode qc

# Run yield prediction for a new batch
python main.py --mode predict --seed-moisture 7.5 --feed-rate 120

# Generate monthly report
python main.py --mode report --month 2025-06
```

---

## 📊 Key Metrics Tracked

| Parameter | Typical Range | Alarm Threshold |
|-----------|--------------|-----------------|
| Oil Yield | 32–38% | < 30% |
| FFA (Free Fatty Acid) | 0.5–2.0% | > 3.0% |
| Moisture in cake | 5–8% | > 10% |
| Bearing Temperature | 60–80°C | > 95°C |
| Motor Current | 45–65 A | > 75 A |
| Throughput (seed) | 100–150 kg/hr | < 80 kg/hr |
| Peroxide Value | < 5 meq/kg | > 10 meq/kg |

---

## 🔬 Research Basis

Parameters and thresholds are derived from:
- FSSAI standards for mustard oil (IS 546)
- BIS specification for edible mustard oil
- Internal factory logs (3-year operational dataset)
- Agmark Grade-1 & Grade-2 specifications
- Industrial best practices from Punjab/Rajasthan expeller mills

---

## 👨‍🔬 Author Note

This system was architected based on operational challenges observed in a mid-scale mustard oil factory (5-tonne/day capacity, 3 expeller lines). Common pain points addressed:
- Manual batch record errors → automated logging
- Unexpected bearing failures → predictive maintenance
- Variable seed quality affecting yield → ML prediction
- No traceability for quality complaints → batch traceability

---

## 📄 License
MIT — Free to use and adapt for factory operations.
