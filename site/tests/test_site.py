import importlib.util
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('retake_site',ROOT/'site/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.output=builder.build(cls.tmp.name)
        cls.html=(cls.output/'index.html').read_text(encoding='utf-8')

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_readiness_is_explicit(self):
        self.assertIn('In development.',self.html)
        self.assertIn('local manifest pipeline is implemented',self.html)
        self.assertNotIn('Your agent can install the tool',self.html)
        self.assertNotIn('help in skill format',self.html)

    def test_family_identity_and_navigation_preserved(self):
        self.assertIn('Amplifier Smart Tools',self.html)
        self.assertIn('microsoft.github.io/amplifier-smart-tools-catalog/',self.html)
        self.assertIn('Microsoft Office of the CTO',self.html)

    def test_motion_has_still_fallback_and_pause(self):
        self.assertIn('data-motion-src="./assets/retake-loop.gif"',self.html)
        self.assertIn('data-still-src="./assets/retake-static.png"',self.html)
        self.assertIn('data-motion-toggle',self.html)
        self.assertIn('prefers-reduced-motion',(self.output/'assets/site.js').read_text())
        for name in ['retake-loop.gif','retake-static.png','retake-mark.svg']:
            self.assertTrue((self.output/'assets'/name).is_file())

    def test_art_is_not_presented_as_product_demo(self):
        self.assertIn('Illustration, not a scene-generation demo.',self.html)
        self.assertNotIn('<video',self.html)

    def test_public_links_target_retakes_repository(self):
        self.assertIn('https://github.com/robotdad/amplifier-smart-tool-retake',self.html)
        self.assertIn('retake-mark.svg',self.html)

    def test_vendored_theme_matches_pinned_source(self):
        source=json.loads((ROOT/'site/theme-source.json').read_text())
        for name,digest in source['files'].items():
            data=(ROOT/'site/theme'/name).read_bytes()
            if Path(name).suffix not in ['.png','.gif','.mp4']:data=data.replace(b'\r\n',b'\n')
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest,name)

if __name__=='__main__':unittest.main()
