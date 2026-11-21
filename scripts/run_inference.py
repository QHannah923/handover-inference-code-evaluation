"""Run the current model-first classifier; explicitly requires an API key."""
import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/local_inference/predictions.json')
    args = parser.parse_args()
    if not os.environ.get('OPENAI_API_KEY'):
        parser.error('Set OPENAI_API_KEY in the environment; never store it in the repository.')
    files = args.files or sorted((ROOT / 'dark-pattern/interface_interference_examples/INTERFACE_INTERFERENCE_all(87)').glob('*.txt'))
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        parser.error('Input file missing: ' + ', '.join(missing))
    if not files:
        parser.error('No input files found.')
    sys.path.insert(0, str(ROOT / 'dark-pattern'))
    from run_interface_interference import run
    with contextlib.redirect_stdout(sys.stderr):
        results = run(files)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {len(results)} predictions to {args.output}')


if __name__ == '__main__':
    main()
