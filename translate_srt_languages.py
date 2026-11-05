"""Translate an existing SRT into multiple languages using AI4Bharat."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source", default="en")
    parser.add_argument("--targets", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("translated_srts"))
    args = parser.parse_args()
    from constants import LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE
    for language in [args.source, *args.targets]:
        if language not in LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE:
            parser.error(f"Unsupported language: {language}")
    if not args.input.is_file():
        parser.error(f"Input does not exist: {args.input}")
    from model_entry import translate_srt
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for language in args.targets:
        if language == args.source:
            continue
        output = args.output_dir / f"{args.input.stem}_{language}.srt"
        translate_srt(str(args.input), str(output), args.source, language, "ai4bharat", {})


if __name__ == "__main__":
    main()
