# Automated Meme Video Generation

A Python media-automation project that assembles short clips into a vertical video compilation. The supported local workflow normalizes aspect ratio, frame rate, and audio, concatenates clips in the supplied order, and adds a text watermark.

**[Watch the generated local sample](docs/demo.mp4)** · **[Historical OCR/upload experiments](docs/LEGACY.md)**

[![Frame from the generated local demo](docs/demo-preview.png)](docs/demo.mp4)

## Run the local demo

Requires **Python 3.10+** and **FFmpeg/FFprobe** on `PATH`, with libx264, AAC, and drawtext support. No third-party Python packages, accounts, browser automation, API keys, or uploads are needed.

```sh
python main.py --demo demo-output/inputs \
  --output demo-output/compilation.mp4 --report demo-output/report.json
```

The demo generates two original test-pattern clips with authored captions and a synthetic tone. One clip has audio and the other is silent, exercising both normalization paths. These are shareable fixtures, not downloaded memes or a claim that the old OCR/speech/upload integrations currently work. Use a fresh directory and output filename for another run.

## Compile your own clips

```sh
python main.py /path/to/first.mp4 /path/to/second.mp4 \
  --output demo-output/my-compilation.mp4 --report demo-output/my-report.json
```

Use media you are allowed to process and share. The local workflow preserves its inputs and refuses existing output/report paths. It produces a **360 × 640**, **24 FPS** H.264/AAC MP4. Inputs are processed in argument order; missing audio is replaced with silence. Original source audio is otherwise retained.

The optional JSON report records input names and SHA-256 hashes, output dimensions, frame rate, and measured duration. FFmpeg versions and codecs can affect byte-level output; the reproducible contract is the processing workflow and media properties.

## Pipeline

```text
Local clips → probe streams → normalize portrait video + stereo audio
            → concatenate → text watermark → local MP4 + optional JSON report
```

`main.py` provides the CLI; `local_pipeline.py` contains media processing. Temporary intermediates are isolated beside the output and cleaned up when processing finishes. The finished video is published without overwriting an existing destination.

## History and scope

The earlier project explored CSV-backed clip selection, duplicate handling, OCR, speech generation through a website, animated image sequences, watermarking, and YouTube upload automation. Those experiments remain in the repository and are described in [docs/LEGACY.md](docs/LEGACY.md). The new local workflow provides a reproducible entry point without their external-service dependencies.

No automatic collection or upload runs from the supported CLI. This maintenance pass did not validate OCR, narration generation, account login, or platform uploading.

## Validation

```sh
python -m unittest discover -s tests -v
```

Integration tests actually encode original fixture clips and inspect the compilation with FFprobe. They check dimensions, frame rate, audio presence, duration, input preservation, paths with spaces/apostrophes, and refusal to overwrite an existing output. CI repeats the tests and uploads the generated clips, compilation, and report as an artifact.

## License

Code and the authored demonstration fixtures use the repository's [Apache License 2.0](LICENSE). Media supplied by users retains its own rights and licensing.
