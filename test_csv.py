
import sys
sys.path.insert(0, 'backend')
from app.services.csv_adapter_service import build_csv_adapter_preview
with open('ml_training/juni_2024.csv', 'rb') as f:
    res = build_csv_adapter_preview(f.read(), 'juni_2024.csv')
    print('Format:', res.detected_format)
    print('Issues:', [i.message for i in res.issues])
    print('Missing columns:', res.required_columns_missing)

