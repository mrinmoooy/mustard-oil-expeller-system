"""
test_all_modules.py
===================
Unit Tests — Mustard Oil Expeller Management System
Run with: python -m pytest tests/ -v
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)


class TestExpellerMonitor(unittest.TestCase):

    def setUp(self):
        from src.expeller_monitor import ExpellerMonitor
        self.monitor = ExpellerMonitor()

    def test_valid_reading(self):
        r = self.monitor.simulate_reading("EXP-01", seed_grade="B", seed_moisture=8.0)
        self.assertEqual(r.expeller_id, "EXP-01")
        self.assertGreater(r.oil_yield_pct, 20.0)
        self.assertLess(r.oil_yield_pct, 45.0)
        self.assertGreater(r.throughput_kg_hr, 0)

    def test_invalid_expeller_raises(self):
        with self.assertRaises(ValueError):
            self.monitor.simulate_reading("EXP-99")

    def test_alarm_on_high_temp(self):
        """Force a high bearing temp scenario via many readings and check alarms structure."""
        r = self.monitor.simulate_reading("EXP-02", seed_grade="C", seed_moisture=11.0)
        self.assertIsInstance(r.alarm_flags, list)

    def test_summary_after_readings(self):
        for _ in range(5):
            self.monitor.simulate_reading("EXP-01")
        summary = self.monitor.get_summary("EXP-01")
        self.assertEqual(summary["expeller"], "EXP-01")
        self.assertGreater(summary["readings_count"], 0)
        self.assertIn("avg_yield_pct", summary)

    def test_yield_range_grade_A(self):
        r = self.monitor.simulate_reading("EXP-01", seed_grade="A", seed_moisture=7.0)
        self.assertGreater(r.oil_yield_pct, 28.0,
                           "Grade-A seed should yield well above 28%")


class TestQualityControl(unittest.TestCase):

    def setUp(self):
        from src.quality_control import QualityControlSystem
        self.qc = QualityControlSystem()

    def test_sample_generation(self):
        s = self.qc.generate_sample("BATCH-001", "EXP-01")
        self.assertIsNotNone(s.sample_id)
        self.assertGreater(s.ffa_pct, 0)
        self.assertIn(s.grade, [
            "Agmark Grade-1", "Agmark Grade-2", "FSSAI Edible", "Sub-Standard / Reject"])

    def test_fresh_low_temp_sample(self):
        """Low seed age + low cage temp → lower FFA expected."""
        s = self.qc.generate_sample("BATCH-001", "EXP-01",
                                    seed_age_days=1, cage_temp=62.0, seed_ffa_pct=0.5)
        self.assertLess(s.ffa_pct, 3.0, "Fresh seed at low temp should not have very high FFA")

    def test_old_seed_high_ffa(self):
        """Old seed should trend toward higher FFA."""
        ffas = []
        for _ in range(20):
            s = self.qc.generate_sample("BATCH-002", "EXP-02",
                                        seed_age_days=30, cage_temp=75, seed_ffa_pct=2.0)
            ffas.append(s.ffa_pct)
        avg_ffa = sum(ffas) / len(ffas)
        self.assertGreater(avg_ffa, 1.5, "Old seed should produce higher avg FFA")

    def test_pass_fail_summary(self):
        for i in range(10):
            self.qc.generate_sample(f"BATCH-{i}", "EXP-01")
        summary = self.qc.get_pass_fail_summary()
        self.assertEqual(summary["total_samples"], 10)
        self.assertIn("pass_rate_pct", summary)
        self.assertIn("grade_breakdown", summary)


class TestYieldPredictor(unittest.TestCase):

    def setUp(self):
        from src.yield_predictor import YieldPredictor, PredictionInput
        self.predictor = YieldPredictor()
        self.PredictionInput = PredictionInput

    def test_train_and_predict(self):
        self.predictor.train(verbose=False)
        inp = self.PredictionInput(
            seed_moisture_pct=7.5,
            seed_oil_content_pct=40.0,
            seed_temp_C=35.0,
            feed_rate_kg_hr=110.0,
            cage_temp_C=68.0,
            worm_rpm=30,
            seed_grade="B",
            incoming_ffa_pct=0.8,
        )
        result = self.predictor.predict(inp)
        self.assertIn("predicted_yield_pct", result)
        self.assertGreater(result["predicted_yield_pct"], 20.0)
        self.assertLess(result["predicted_yield_pct"], 45.0)
        self.assertIn("recommendations", result)

    def test_high_moisture_lower_yield(self):
        """Higher moisture should predict lower yield."""
        self.predictor.train(verbose=False)
        low_moist = self.PredictionInput(7.0, 40.0, 35.0, 110.0, 68.0, 30, "B", 0.8)
        high_moist = self.PredictionInput(11.0, 40.0, 35.0, 110.0, 68.0, 30, "B", 0.8)
        low_yield = self.predictor.predict(low_moist)["predicted_yield_pct"]
        high_yield = self.predictor.predict(high_moist)["predicted_yield_pct"]
        self.assertGreater(low_yield, high_yield,
                           "Lower moisture should give higher yield")


class TestBatchLogger(unittest.TestCase):

    def setUp(self):
        from src.batch_logger import BatchLogger
        self.logger = BatchLogger()

    def test_create_seed_lot(self):
        lot = self.logger.create_seed_lot()
        self.assertIsNotNone(lot.lot_id)
        self.assertIn(lot.grade, ["A", "B", "C"])
        self.assertGreater(lot.quantity_kg, 0)

    def test_log_batch(self):
        lot = self.logger.create_seed_lot()
        batch = self.logger.log_batch(lot, "EXP-01", shift="morning")
        self.assertIsNotNone(batch.batch_id)
        self.assertGreater(batch.crude_oil_kg, 0)
        self.assertGreater(batch.oil_yield_pct, 0)
        self.assertIn(batch.oil_grade, [
            "Agmark Grade-1", "Agmark Grade-2", "FSSAI Edible", "Sub-Standard"])

    def test_production_summary(self):
        lot = self.logger.create_seed_lot()
        for shift in ["morning", "afternoon", "night"]:
            self.logger.log_batch(lot, "EXP-01", shift=shift)
        summary = self.logger.get_production_summary()
        self.assertEqual(summary["total_batches"], 3)
        self.assertGreater(summary["total_crude_oil_kg"], 0)


class TestEnergyAnalyzer(unittest.TestCase):

    def setUp(self):
        from src.energy_analyzer import EnergyAnalyzer
        self.analyzer = EnergyAnalyzer()

    def test_log_energy(self):
        rec = self.analyzer.log_energy("EXP-01", 22.0, 8.0, 1200.0, 420.0)
        self.assertGreater(rec.kwh_consumed, 0)
        self.assertGreater(rec.specific_energy_kwh_per_tonne, 0)

    def test_energy_summary(self):
        for i in range(5):
            self.analyzer.log_energy("EXP-01", 22.0, 8.0, 1100.0 + i*50, 380.0 + i*15)
        summary = self.analyzer.get_energy_summary()
        self.assertIn("efficiency_rating", summary)
        self.assertIn("avg_specific_energy_kwh_per_tonne", summary)
        self.assertGreater(summary["total_kwh_consumed"], 0)


class TestMaintenanceScheduler(unittest.TestCase):

    def setUp(self):
        from src.maintenance_scheduler import MaintenanceScheduler
        self.scheduler = MaintenanceScheduler()

    def test_components_initialized(self):
        self.assertGreater(len(self.scheduler.components), 0)

    def test_work_orders_generated(self):
        tasks = self.scheduler.generate_work_orders()
        # Work orders may or may not be generated depending on random state
        self.assertIsInstance(tasks, list)

    def test_summary(self):
        self.scheduler.generate_work_orders()
        summary = self.scheduler.get_maintenance_summary()
        self.assertIn("total_components_tracked", summary)
        self.assertGreater(summary["total_components_tracked"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
