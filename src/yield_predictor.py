"""
yield_predictor.py
==================
ML-Based Oil Yield Prediction for Mustard Expeller Operations
Uses a trained regression model to predict oil yield (%) before pressing.

Features used:
  - Seed moisture content (%)
  - Seed oil content (%)
  - Seed temperature (°C)
  - Feed rate (kg/hr)
  - Press cage temperature (°C)
  - Worm shaft RPM
  - Seed grade (A/B/C encoded)
  - FFA of incoming seed

Author: Senior Process Engineer (3 yrs exp, Mustard Oil Factory)
"""

import numpy as np
import random
import logging
from typing import Dict, Tuple, List
from dataclasses import dataclass

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PredictionInput:
    seed_moisture_pct: float      # Target: 6.5–8.0%
    seed_oil_content_pct: float   # Black mustard: 38–45%
    seed_temp_C: float            # Pre-conditioned seed temp
    feed_rate_kg_hr: float        # Throughput
    cage_temp_C: float            # Press cage/barrel temp
    worm_rpm: int                 # Screw shaft speed
    seed_grade: str               # A, B, or C
    incoming_ffa_pct: float       # Seed FFA before pressing


class YieldPredictor:
    """
    Gradient Boosting model trained on synthetic but realistic factory data.
    
    Field insight (3 years experience):
    - Seed moisture is THE single most impactful variable for yield.
      Optimal: 6.5–7.5%. Every 1% over 8% costs ~0.5–0.8% yield.
    - Press cage temperature balance is critical:
      Too cold (<55°C): Oil doesn't flow freely → more oil in cake
      Too hot (>80°C): FFA spike, colour darkens, tocopherols degrade
    - Worm shaft RPM affects residence time in barrel:
      Slower (28–32 rpm): More extraction but more heat and wear
    - Seed oil content drives theoretical yield ceiling
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        self.feature_names = [
            'seed_moisture_pct', 'seed_oil_content_pct', 'seed_temp_C',
            'feed_rate_kg_hr', 'cage_temp_C', 'worm_rpm',
            'seed_grade_enc', 'incoming_ffa_pct'
        ]
        self.training_mae = None
        self.training_r2 = None

    def _encode_grade(self, grade: str) -> float:
        return {"A": 1.0, "B": 0.0, "C": -1.0}.get(grade.upper(), 0.0)

    def _input_to_features(self, inp: PredictionInput) -> List[float]:
        return [
            inp.seed_moisture_pct,
            inp.seed_oil_content_pct,
            inp.seed_temp_C,
            inp.feed_rate_kg_hr,
            inp.cage_temp_C,
            inp.worm_rpm,
            self._encode_grade(inp.seed_grade),
            inp.incoming_ffa_pct,
        ]

    def _generate_training_data(self, n_samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate realistic training dataset based on factory observations.
        Real production: replace with actual historical CSV data.
        """
        X, y = [], []
        for _ in range(n_samples):
            moisture = random.uniform(5.5, 12.5)
            oil_content = random.uniform(34.0, 45.0)
            seed_temp = random.uniform(25.0, 45.0)
            feed_rate = random.uniform(70.0, 155.0)
            cage_temp = random.uniform(50.0, 95.0)
            worm_rpm = random.randint(26, 38)
            grade_enc = random.choice([1.0, 0.0, -1.0])
            ffa = random.uniform(0.3, 4.5)

            # Physics-based yield formula (from empirical observations)
            base_yield = oil_content * 0.85  # theoretical extraction efficiency

            # Moisture penalty: optimum at 7.2%
            moist_penalty = abs(moisture - 7.2) * 0.55 if moisture > 7.2 else (
                abs(moisture - 7.2) * 0.25)

            # Temperature factor (optimal 65–72°C cage)
            temp_factor = -0.05 * abs(cage_temp - 68) if cage_temp < 68 else (
                -0.08 * abs(cage_temp - 68))

            # Feed rate factor
            feed_penalty = max(0, (feed_rate - 120) * 0.03)

            # RPM: slower = marginally better extraction
            rpm_factor = max(0, (32 - worm_rpm) * 0.1)

            # Grade effect
            grade_bonus = grade_enc * 1.2

            # FFA: old/damaged seed slightly harder to press
            ffa_penalty = max(0, (ffa - 1.0) * 0.15)

            yield_pct = (base_yield - moist_penalty + temp_factor
                         - feed_penalty + rpm_factor + grade_bonus
                         - ffa_penalty + random.gauss(0, 0.7))
            yield_pct = max(22.0, min(42.0, yield_pct))

            X.append([moisture, oil_content, seed_temp, feed_rate,
                       cage_temp, worm_rpm, grade_enc, ffa])
            y.append(yield_pct)

        return np.array(X), np.array(y)

    def train(self, verbose: bool = True) -> Dict:
        """Train the yield prediction model."""
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available; using rule-based fallback")
            return {"error": "sklearn not installed"}

        if verbose:
            print("  🧠 Training yield prediction model on factory dataset...")

        X, y = self._generate_training_data(2500)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            random_state=42
        )
        self.model.fit(X_train_s, y_train)

        y_pred = self.model.predict(X_test_s)
        self.training_mae = round(mean_absolute_error(y_test, y_pred), 3)
        self.training_r2 = round(r2_score(y_test, y_pred), 4)
        self.is_trained = True

        result = {
            "status": "trained",
            "samples_used": len(X_train),
            "test_MAE_pct": self.training_mae,
            "test_R2": self.training_r2,
            "feature_importances": dict(zip(
                self.feature_names,
                [round(v, 4) for v in self.model.feature_importances_]
            ))
        }

        if verbose:
            print(f"  ✅ Model trained: MAE={self.training_mae}%  R²={self.training_r2}")
            print(f"\n  📊 Feature Importances (Top Variables):")
            sorted_fi = sorted(result["feature_importances"].items(),
                               key=lambda x: -x[1])
            for feat, imp in sorted_fi:
                bar = "█" * int(imp * 50)
                print(f"     {feat:<28s}: {bar}  {imp:.4f}")

        return result

    def predict(self, inp: PredictionInput) -> Dict:
        """Predict oil yield for given input parameters."""
        features = self._input_to_features(inp)

        if SKLEARN_AVAILABLE and self.is_trained:
            X = np.array([features])
            X_s = self.scaler.transform(X)
            predicted_yield = round(float(self.model.predict(X_s)[0]), 2)
            # Confidence interval (approximate ±2*MAE)
            ci = self.training_mae * 2 if self.training_mae else 1.0
        else:
            # Fallback: simple linear formula
            predicted_yield = round(
                inp.seed_oil_content_pct * 0.83
                - abs(inp.seed_moisture_pct - 7.2) * 0.6
                - max(0, (inp.feed_rate_kg_hr - 120) * 0.02), 2)
            ci = 2.0

        predicted_yield = max(22.0, min(42.0, predicted_yield))

        # Practical recommendations
        recs = self._generate_recommendations(inp, predicted_yield)

        return {
            "predicted_yield_pct": predicted_yield,
            "confidence_interval": f"±{ci:.2f}%",
            "expected_oil_L_per_hr": round(inp.feed_rate_kg_hr * predicted_yield / 100 * 0.91, 1),
            "expected_cake_kg_hr": round(inp.feed_rate_kg_hr * (1 - predicted_yield / 100), 1),
            "recommendations": recs,
        }

    def _generate_recommendations(self, inp: PredictionInput,
                                   yield_pct: float) -> List[str]:
        recs = []
        if inp.seed_moisture_pct > 8.5:
            recs.append(f"⚠️ Seed moisture {inp.seed_moisture_pct}% is too high. "
                        f"Dry seed to 6.5–7.5% to improve yield by ~"
                        f"{(inp.seed_moisture_pct - 7.5) * 0.55:.1f}%")
        elif inp.seed_moisture_pct < 6.0:
            recs.append("💧 Moisture too low (<6%) — increase slightly to reduce worm wear")

        if inp.cage_temp_C < 60:
            recs.append("🌡️ Cage temp too low — increase to 65–70°C for better oil flow")
        elif inp.cage_temp_C > 80:
            recs.append("🌡️ Cage temp too high — reduce to protect oil quality (FFA)")

        if inp.feed_rate_kg_hr > 130:
            recs.append("⚡ Feed rate high — reducing to 110–120 kg/hr may improve yield")

        if inp.incoming_ffa_pct > 2.0:
            recs.append("🔴 Seed FFA already high — process immediately, minimize delay")

        if yield_pct < 30:
            recs.append("🔴 Predicted yield critically low — review seed quality + press settings")
        elif yield_pct < 33:
            recs.append("🟡 Yield below target — check seed grade and press adjustment")
        else:
            recs.append(f"✅ Predicted yield {yield_pct}% is within good operating range")

        return recs
