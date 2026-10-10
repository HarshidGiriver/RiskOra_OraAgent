"""
RISKORA - Production System Runner
Launches the complete AI/ML-powered Digital Micro-Lending Risk Platform.
Initializes SQLite database, primes ML model artifacts, and launches FastAPI server.
"""

import os
import sys
import uvicorn

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from riskora.backend.database import init_db
from riskora.ml.inference_engine import get_engine
from riskora.backend.services.dataset_service import get_dataset_manager

def main():
    print("=" * 65)
    print("  RISKORA : Digital Micro-Lending Risk Platform (Production Mode)")
    print("  AI-Assisted Risk-Based Framework for Digital Micro-Lending")
    print("=" * 65)

    print("\n[1/3] Initializing SQLite Relational Database & Pre-Seeding Portfolio...")
    init_db()

    print("\n[2/3] Priming ML Inference Engine & Calibrated Champion Model Artifact...")
    engine = get_engine()
    print(f"      Active Model: {engine.model_card.get('model_name', 'RISKORA-ML-v1.0')}")
    print(f"      Calibration:  {engine.model_card.get('calibration_method', 'Sigmoid CalibratedClassifierCV')}")

    print("\n[3/3] Priming Ingestion Service & Benchmark Historical Analytics...")
    get_dataset_manager()

    host = "127.0.0.1"
    port = int(os.environ.get("PORT", 8000))

    print("\n" + "=" * 65)
    print(f"  ● RISKORA Workstation: http://{host}:{port}")
    print(f"  ● OpenAPI Documentation: http://{host}:{port}/docs")
    print(f"  ● Health Check: http://{host}:{port}/api/health")
    print("=" * 65 + "\n")

    uvicorn.run("riskora.backend.main:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
