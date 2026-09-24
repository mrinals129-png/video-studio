import unittest
from tooling.cloud import captions, request, timestamp

class CloudTests(unittest.TestCase):
    def test_existing_script_and_voice(self):
        path, slug=request('scripts/hello-studio.md','bf_emma')
        self.assertTrue(path.is_file())
        self.assertEqual(slug,'hello-studio')

    def test_untrusted_paths_are_rejected(self):
        for value in ('../README.md','scripts/../README.md','scripts/a.md\nslug=bad','/etc/passwd','scripts/$(whoami).md','scripts/missing.md'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                request(value,'af_heart')

    def test_invalid_voice_is_rejected(self):
        with self.assertRaises(ValueError):
            request('scripts/hello-studio.md','$(whoami)')

    def test_caption_format_escapes_markup_and_preserves_final_sentence(self):
        vtt=captions({'words':[{'word':'<script>','start':0,'end':.5},
                               {'word':'Hello.','start':.5,'end':1},
                               {'word':'Goodbye','start':1,'end':1.75}]})
        self.assertTrue(vtt.startswith('WEBVTT\n'))
        self.assertIn('00:00:00.000 --> 00:00:01.000',vtt)
        self.assertIn('&lt;script&gt; Hello.',vtt)
        self.assertIn('00:00:01.000 --> 00:00:01.750\nGoodbye',vtt)

    def test_timestamp_rollover(self):
        self.assertEqual(timestamp(59.9996),'00:01:00.000')
        self.assertEqual(timestamp(3661.25),'01:01:01.250')

if __name__=='__main__':
    unittest.main()
