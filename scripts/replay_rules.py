"""Replay current rules on frozen model answers. No API or automatic grading."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dark-pattern'))
from common import parse_log
from verified_failure_rules import apply_verified_fallback
from interface_interference_prompt_v2 import subtype_from_joint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/local_replay/predictions.json')
    args = parser.parse_args()
    source = ROOT / 'outputs/interface_semantic_freemium_20261120/confirmation_run/predictions.json'
    baseline = ROOT / 'outputs/interface_boundary_rules_20261120/predictions.json'
    rows = json.loads(source.read_text(encoding='utf-8'))
    expected = {r['sample_id']: r for r in json.loads(baseline.read_text(encoding='utf-8'))}
    inputs = ROOT / 'dark-pattern/interface_interference_examples/INTERFACE_INTERFERENCE_all(87)'
    results = []
    changed = []
    for row in rows:
        turns = parse_log((inputs / row['log_file']).read_text(encoding='utf-8'))
        first = apply_verified_fallback(row['controlled_variants']['model_only'], turns)
        result = {'sample_id': row['sample_id'], 'log_file': row['log_file'], **first,
                  'step3_subtype_prediction': subtype_from_joint(first)}
        results.append(result)
        old = expected[row['sample_id']]
        if (result['primary_type_prediction']['type'], result['step3_subtype_prediction']['subtype']) != (old['primary_type_prediction']['type'], old['step3_subtype_prediction']['subtype']):
            changed.append(row['sample_id'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'samples': len(results), 'changed_primary_path_ids': changed,
                      'api_calls': 0, 'automatic_grading': False, 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
