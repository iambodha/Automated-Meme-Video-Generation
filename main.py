"""Build a local video compilation without accounts or uploads."""
import argparse
import json
from pathlib import Path
import sys

from local_pipeline import compile_clips, demo_inputs, require_tools


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='*', type=Path, help='Local video files in compilation order')
    parser.add_argument('--demo', type=Path, metavar='DIRECTORY', help='Generate original fixture clips in a fresh directory')
    parser.add_argument('--output', type=Path, required=True, help='New .mp4 output file; existing files are refused')
    parser.add_argument('--report', type=Path, help='Optional new JSON report file')
    args = parser.parse_args(argv)
    try:
        require_tools()
        if bool(args.inputs) == bool(args.demo):
            raise ValueError('Choose local input files OR --demo DIRECTORY')
        if args.output.exists() or (args.report and args.report.exists()):
            raise ValueError('Output/report already exists; choose new filenames')
        if args.report and args.report.resolve() == args.output.resolve():
            raise ValueError('Output and report must be different files')
        inputs = demo_inputs(args.demo) if args.demo else args.inputs
        result = compile_clips(inputs, args.output)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2)
                stream.write('\n')
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
