# Indic subtitle translation

## Overall flow

```text
Video/audio in OCI Object Storage
             ↓
      OCI Speech transcription
             ↓
       SRT subtitle file
             ↓
 Optional scene descriptions
             ↓
 Translation using AI4Bharat or OCI GenAI
             ↓
 Translated SRT → WebVTT for web playback
```

Translate existing SRT subtitles into Indian languages with AI4Bharat IndicTrans2.
Optional scripts also provide OCI Speech transcription, OCI GenAI translation,
video scene descriptions, and SRT to WebVTT conversion.

## Local AI4Bharat translation

Use a Python environment compatible with your selected PyTorch and CUDA versions.
Install `requirements.txt`, a compatible `flash-attn` build, and IndicTransToolkit
from its upstream project: https://github.com/VarunGumma/IndicTransToolkit .
The toolkit must be importable as `IndicTransToolkit`; no toolkit subfolder is
included here. Follow the model provider's access and licensing requirements.
The current model implementation requests Flash Attention 2 and float16, so a
compatible GPU setup is expected. Model weights download on first use.

```bash
python -m pip install -r requirements.txt
python translate_srt_languages.py input.srt --source en --targets hi mr ta te bn kn ml gu pa or as
```

Outputs are saved under `translated_srts/`. Each target reloads the model.
Local AI4Bharat translation does not require OCI credentials or a `.env` file.
Dependency versions are inherited/unpinned; GPU inference has not been validated
in this sanitized distribution.

## Main files

- `translate_srt_languages.py`: command-line entry point for multiple languages.
- `model_entry.py`: SRT parsing, grouping, translation selection, and redistribution.
- `indic_trans.py`: local AI4Bharat inference.
- `constants.py`: language and model mappings.
- `genai_client.py`, `utils.py`, `load_env_data.py`: optional OCI integration.
- `closed_captions.py`, `cc_models.py`: scene descriptions from video frames.
- `Transform_SRT.py`: merge short subtitle entries.
- `srt_to_vtt*.py`: subtitle conversion experiments.
- `perform_transcribe_translate*.py`: alternative OCI orchestration workflows.
- `*_orig.py`, `*_test.py`, `test*.py`, `genai_client copy.py`: historical variants
  and experiments, not an automated test suite.

## Optional OCI workflows

Copy `.env.example` to `.env` and supply your own configuration. Configure OCI
credentials outside this repository using the OCI SDK's standard configuration.
Legacy scripts containing `YOUR_*` placeholders need those settings replaced or
wired to your environment before use. Some legacy scripts perform cloud operations
at module scope, including uploads and deletion of generated `.vtt_new` objects;
inspect the selected script before running or importing it. Their active steps
vary: some transcription, translation, or upload calls are commented out.

## Publishing

This folder contains source files and dependency lists only. Original `.env`
files, credentials, media, generated subtitles, Git history, and subfolders were
not copied. Hardcoded OCI resource IDs, known account/bucket values, machine paths,
and historical comments were removed or replaced. `.gitignore` excludes runtime
configuration and outputs. Review any files you add before publishing.

No license is assumed or granted by this preparation. Choose a license only if
you have the necessary rights to publish the original code. Upstream models and
libraries retain their own licenses.
