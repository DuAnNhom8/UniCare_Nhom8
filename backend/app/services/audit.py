import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from ..config import ROOT

_logger = logging.getLogger('unicareer.admin.audit')
_logger.setLevel(logging.INFO)
_logger.propagate = False
if not _logger.handlers:
    log_dir = ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    _logger.addHandler(logging.FileHandler(log_dir / 'admin_actions.jsonl', encoding='utf-8'))

def audit_action(admin_id: int, action: str, target_id: int, old_value: str, new_value: str):
    record = {
        'at': datetime.now(timezone.utc).isoformat(),
        'admin_id': admin_id,
        'action': action,
        'target_id': target_id,
        'old_value': old_value,
        'new_value': new_value,
    }
    _logger.info(json.dumps(record, ensure_ascii=False))
