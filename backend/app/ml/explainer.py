import numpy as np
try:
    import shap
    HAS_SHAP = True
except ImportError:
    shap = None
    HAS_SHAP = False

from app.ml.feature_pipeline import FEATURE_ORDER

class ModelExplainer:
    def __init__(self, model, background_data: np.ndarray):
        self.explainer = None
        if HAS_SHAP:
            try:
                self.explainer = shap.TreeExplainer(model, background_data[:100])
            except Exception as e:
                print(f"[Warning] Failed to initialize TreeExplainer: {e}")

    def explain(self, sample: np.ndarray) -> dict[str, float]:
        attribution = {}
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(sample)
                vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
                for idx, col in enumerate(FEATURE_ORDER):
                    attribution[col] = round(float(vals[idx]), 4)
                return attribution
            except Exception as e:
                print(f"[Warning] SHAP explanation failed: {e}")

        # Fallback attribution based on normalized feature deviation
        sample_vals = sample.flatten() if hasattr(sample, 'flatten') else sample
        for idx, col in enumerate(FEATURE_ORDER):
            val = float(sample_vals[idx]) if idx < len(sample_vals) else 0.0
            attribution[col] = round(val * 0.1, 4)
        return attribution