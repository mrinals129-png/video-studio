import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import studio
from _engine.tts.generate import read_script, generate_voice, generate_voice_segments
from _engine.overlay.generate import fill_template as overlay_fill
from _engine.overlay import generate as overlay

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = self.root/'script.md'

    def write(self, text):
        self.script.write_text(text, encoding='utf-8')
        return self.script

    def test_narration_only_with_unicode_crlf_and_links(self):
        self.write('## Feature name\r\nPrivate title\r\n## Narration\r\nTry **café** and [the studio](https://example.com).\r\n## Animation notes\r\nDo not speak this.')
        self.assertEqual(read_script(str(self.script)), 'Try café and the studio.')

    def test_structured_script_missing_narration_rejected(self):
        self.write('## Feature name\nMetadata is not narration.')
        with self.assertRaises(ValueError):
            studio.metadata(self.script)

    def test_empty_audio_rejected_before_loading_model(self):
        with self.assertRaises(ValueError):
            generate_voice(' ', str(self.root))
        with self.assertRaises(ValueError):
            generate_voice_segments([], str(self.root))

    def test_plain_text_script(self):
        self.write('A plain text story.')
        self.assertEqual(read_script(str(self.script)), 'A plain text story.')

    def test_timings_bounded_even_with_one_sentence(self):
        for duration in (6, 8, 12.5, 50):
            total, first, last = studio.timings({'duration':duration,'words':[{'word':'End.','end':duration}]})
            self.assertGreaterEqual(first, 2)
            self.assertGreaterEqual(last-first, 2)
            self.assertGreaterEqual(total-last, 2)

    def test_short_and_nonfinite_timing_rejected(self):
        for duration in (0, 5, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                studio.timings({'duration':duration,'words':[]})

    def test_template_missing_values_and_single_pass(self):
        with self.assertRaises(ValueError):
            studio.fill_template('{{MISSING}}', {})
        self.assertEqual(studio.fill_template('{{A}}', {'A':'{{B}}','B':'oops'}),'{{B}}')
        self.assertEqual(overlay_fill('{{TITLE}}',{'TITLE':'<script>"&'}),'&lt;script&gt;&quot;&amp;')

    def test_generated_html_escapes_copy_and_uses_local_assets(self):
        self.write('## Feature name\nA <script>alert(1)</script>\n## Narration\nFirst sentence. Second sentence. Last sentence.')
        out = self.root/'out'
        studio.build(self.script,out,{'duration':12,'words':[]})
        text=(out/'index.html').read_text(encoding='utf-8')
        self.assertNotIn('{{',text)
        self.assertNotIn('<script>alert',text)
        self.assertIn('&lt;script&gt;',text)
        self.assertIn('data-duration="12.0"',text)
        self.assertTrue((out/'brand.css').is_file())
        self.assertTrue((out/'gsap.min.js').is_file())

    def test_video_trim_and_portable_source(self):
        self.write('## Narration\nFirst. Second. Third.')
        source=self.root/'a recording.mp4'
        source.write_bytes(b'test fixture, not a real video')
        with patch('studio.probe',return_value={'format':{'duration':'20'},'streams':[{'codec_type':'video'}]}):
            studio.build(self.script,self.root/'out',{'duration':12,'words':[]},video=source,video_start=2)
        text=(self.root/'out/index.html').read_text(encoding='utf-8')
        self.assertIn('data-media-start="2"',text)
        self.assertIn('data-start="3.0" data-hf-media-start-basis="global"',text)
        self.assertIn('src="source.mp4"',text)
        self.assertTrue((self.root/'out/source.mp4').exists())

    def test_video_too_short_rejected(self):
        self.write('## Narration\nFirst. Second. Third.')
        source=self.root/'recording.mp4'
        source.write_bytes(b'fixture')
        with patch('studio.probe',return_value={'format':{'duration':'1'},'streams':[{'codec_type':'video'}]}):
            with self.assertRaisesRegex(ValueError,'Recording needs'):
                studio.build(self.script,self.root/'out',{'duration':12,'words':[]},video=source)

    def test_invalid_media_options_rejected(self):
        self.write('## Narration\nFirst. Second. Third.')
        for options in ({'video_start':-1},{'video_volume':1.1},{'video_start':float('nan')}):
            with self.assertRaises(ValueError):
                studio.build(self.script,self.root/'out',{'duration':12,'words':[]},**options)

    def test_native_skill_entrypoints_match(self):
        root=studio.ROOT
        self.assertEqual((root/'.agents/skills/video-studio/SKILL.md').read_bytes(),
                         (root/'.claude/skills/video-studio/SKILL.md').read_bytes())

    def test_overlay_generation_with_optional_cards_and_trim(self):
        self.write('## Feature name\nA <demo>\n## Narration\nFirst. Second. Third.')
        source=self.root/'recording.mp4'
        source.write_bytes(b'fixture')
        out=self.root/'overlay'
        out.mkdir()
        (out/'narration.wav').write_bytes(b'fixture')
        (out/'transcript.json').write_text(json.dumps({'duration':12,'words':[]}),encoding='utf-8')
        for flags in ([], ['--no-intro'], ['--no-outro'], ['--no-intro','--no-outro']):
            argv=['overlay','--video',str(source),'--script',str(self.script),'--out',str(out),'--video-start','1',*flags]
            with patch('sys.argv',argv), patch.object(overlay,'ffprobe_duration',return_value=20), contextlib.redirect_stdout(io.StringIO()):
                overlay.main()
            text=(out/'index.html').read_text(encoding='utf-8')
            self.assertNotIn('{{',text)
            self.assertIn('data-media-start="1.0"',text)
            self.assertIn('A &lt;demo&gt;',text)
            if '--no-outro' in flags:
                self.assertNotIn('.to("#outro-card"',text)
            if '--no-intro' in flags:
                self.assertIn('id="intro-card" style="display:none"',text)

if __name__=='__main__':
    unittest.main()
