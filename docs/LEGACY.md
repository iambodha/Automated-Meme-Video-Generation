# Historical automation

The original orchestration is retained in `legacy_pipeline.py`; `functions.py`, `variables.py`, `youtubeUploader.py`, and `YouTubeUploader/` retain the historical OCR, speech-service, file-management, and upload experiments.

This route is not the supported local demo. It depends on old MoviePy APIs, OCR/Tesseract configuration, Selenium selectors for an external speech website, Chrome driver paths, watermark assets, a CSV database, stage directories, and account state. The original script also omitted its imports; the retained orchestration now imports its legacy modules explicitly.

Its file-management helpers can delete/move source media and rewrite the database. Review it and use disposable copies before attempting that historical workflow. Its dependencies and third-party integrations have not been restored or tested in this maintenance pass. No uploader was executed.

Use `main.py` for the account-free local workflow. It reads input clips, normalizes video/audio, concatenates them, adds a text watermark, and writes a new local MP4. OCR and generated narration remain future integration work rather than features claimed by this demo.
