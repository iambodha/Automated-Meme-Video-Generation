"""Local compilation workflow. Standard-library Python + FFmpeg/FFprobe only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def run(command, **kwargs):
    result = subprocess.run(command, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise ValueError(f'{command[0]} failed: {result.stderr[-1600:]}')
    return result.stdout


def require_tools():
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise ValueError(f'{tool} is required; install FFmpeg and add it to PATH')


def probe(path):
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    if not any(s['codec_type'] == 'video' for s in info.get('streams', [])):
        raise ValueError(f'No video stream: {path}')
    return info


def demo_inputs(folder):
    """Produce original test-pattern clips with authored captions and a synthetic tone."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder/'01-build.mp4', folder/'02-tests.mp4']
    scenes = [('color=c=0x192b45:s=320x240:r=24:d=2', 'WHEN THE BUILD PASSES'),
              ('testsrc2=s=320x240:r=24:d=2', 'AND THE TESTS PASS TOO')]
    for index, (path, (scene, caption)) in enumerate(zip(paths, scenes)):
        if path.exists():
            raise ValueError(f'Demo fixture already exists: {path}; choose a fresh demo directory')
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-f', 'lavfi', '-i', scene]
        if index == 0:
            command += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2']
        command += ['-vf', f'drawtext=text={caption}:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7:x=(w-tw)/2:y=(h-th)/2',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(path)]
        run(command)
    return paths


def compile_clips(inputs, output, width=360, height=640, fps=24):
    require_tools()
    inputs = [Path(p).resolve() for p in inputs]
    output = Path(output).resolve()
    if width < 64 or height < 64 or width % 2 or height % 2 or not 1 <= fps <= 60:
        raise ValueError('Dimensions must be even and at least 64; FPS must be 1..60')
    if not inputs:
        raise ValueError('At least one input clip is required')
    if output.suffix.lower() != '.mp4':
        raise ValueError('Output must use the .mp4 extension')
    if output.exists():
        raise ValueError(f'Output already exists: {output}')
    for path in inputs:
        if not path.is_file():
            raise ValueError(f'Input does not exist: {path}')
    metadata = [probe(path) for path in inputs]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.local-render-', dir=output.parent) as temporary:
        folder = Path(temporary)
        for index, (path, info) in enumerate(zip(inputs, metadata)):
            has_audio = any(s['codec_type'] == 'audio' for s in info['streams'])
            command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(path)]
            if not has_audio:
                command += ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000']
            command += ['-map', '0:v:0', '-map', '0:a:0' if has_audio else '1:a:0',
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},drawtext=text=LOCAL COMPILATION:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6:x=12:y=h-th-18',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-af', 'apad', '-shortest', str(folder/f'part-{index}.mp4')]
            run(command)
        (folder/'clips.txt').write_text(''.join(f"file part-{index}.mp4\n" for index in range(len(inputs))), encoding='utf-8')
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '1', '-i', 'clips.txt',
             '-c', 'copy', '-movflags', '+faststart', 'compiled.mp4'], cwd=folder)
        # Same-directory hard link is an atomic no-overwrite publish of the finished output.
        os.link(folder/'compiled.mp4', output)
    result = probe(output)
    return {'output': output.name, 'width': width, 'height': height, 'fps': fps,
        'duration_s': float(result['format']['duration']),
        'inputs': [{'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in inputs],
        'mode': 'local compilation; no OCR, speech service, browser login, or upload'}
