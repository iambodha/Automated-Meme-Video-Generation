from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from local_pipeline import compile_clips, demo_inputs, probe


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class PipelineTests(unittest.TestCase):
    def test_demo_normalizes_audio_video_and_preserves_inputs(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix="fixture ' ") as directory:
            root=Path(directory)
            inputs=demo_inputs(root/'inputs')
            hashes=[hashlib.sha256(p.read_bytes()).digest() for p in inputs]
            self.assertFalse(any(s['codec_type']=='audio' for s in probe(inputs[1])['streams']))
            result=compile_clips(inputs, root/'output.mp4')
            streams=probe(root/'output.mp4')['streams']
            video=next(s for s in streams if s['codec_type']=='video')
            self.assertEqual((video['width'], video['height']), (360,640))
            self.assertEqual(video['r_frame_rate'], '24/1')
            self.assertTrue(any(s['codec_type']=='audio' for s in streams))
            self.assertGreater(result['duration_s'],3.8)
            self.assertLess(result['duration_s'],4.5)
            self.assertEqual(hashes,[hashlib.sha256(p.read_bytes()).digest() for p in inputs])
            with self.assertRaisesRegex(ValueError,'already exists'):
                compile_clips(inputs,root/'output.mp4')

    def test_missing_input_and_invalid_dimensions_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'out.mp4'
            with self.assertRaisesRegex(ValueError,'Input does not exist'):
                compile_clips([Path(directory)/'missing.mp4'],output)
            with self.assertRaisesRegex(ValueError,'Dimensions'):
                compile_clips([],output,width=321)

    def test_cli_requires_one_input_mode_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'out.mp4'
            output.write_bytes(b'keep this file')
            result=subprocess.run([sys.executable,'main.py','--demo',str(Path(directory)/'inputs'),'--output',str(output)],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(output.read_bytes(),b'keep this file')
            self.assertFalse((Path(directory)/'inputs').exists())
