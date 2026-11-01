from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
SPLITS_CSV = ROOT / "data" / "splits.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

IMG_SIZE = 300                      # EfficientNet-B3 native; use 224 for B0 / ResNet50
MEAN = (0.485, 0.456, 0.406)        # ImageNet statistics (required for transfer learning)
STD = (0.229, 0.224, 0.225)
SEED = 42
