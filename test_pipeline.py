import copy
import json
import tempfile
import unittest
from pathlib import Path
import scene_pipeline as pipeline
from worker import substitution

class ManifestTests(unittest.TestCase):
    def config(self):
        c=pipeline.template();c['settings']=dict(pipeline.DEFAULTS);return c

    def test_offscreen_is_explicit(self):
        c=self.config();pipeline.validate(c)
        del c['cues'][0]['lips']
        with self.assertRaisesRegex(ValueError,'explicitly'):pipeline.validate(c)

    def test_protected_laugh_cannot_be_overwritten(self):
        c=self.config();c['protected_audio']=[[2,2.5]]
        with self.assertRaisesRegex(ValueError,'protected'):pipeline.validate(c)

    def test_overlapping_audio_rejected(self):
        c=self.config();q=copy.deepcopy(c['cues'][0]);q['id']='other';c['cues'].append(q)
        with self.assertRaisesRegex(ValueError,'Overlapping audio'):pipeline.validate(c)

    def test_listener_cannot_be_selected_for_other_speaker(self):
        c=self.config();c['cues'][0]['lips']=[dict(start=1,end=2,speaker='listener',face_order='left-right')]
        with self.assertRaisesRegex(ValueError,'matching speaker'):pipeline.validate(c)

    def test_lip_range_cannot_leak_outside_cue(self):
        c=self.config();c['cues'][0]['lips']=[dict(start=.5,end=2,speaker='speaker-a',face_order='left-right')]
        with self.assertRaisesRegex(ValueError,'inside'):pipeline.validate(c)

    def test_selected_seed_must_exist(self):
        c=self.config();c['cues'][0]['selected_seed']=999
        with self.assertRaisesRegex(ValueError,'selected_seed'):pipeline.validate(c)

    def test_default_substitution_retains_question_delivery(self):
        self.assertEqual(substitution('Malkovich?','Amplifier?'),'<sub targ="Amplifier">Malkovich</sub>?')

    def test_markup_escapes_dialogue_quotes(self):
        self.assertIn('&quot;',substitution('Original.','Say "hello".'))

    def test_misspelled_cue_setting_rejected(self):
        c=self.config();c['cues'][0]['selected_sead']=43
        with self.assertRaisesRegex(ValueError,'Unknown cue'):pipeline.validate(c)

    def test_corrupt_output_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);output=run/'file.wav';output.write_bytes(b'first')
            pipeline.write(run/'mix.done.json',dict(outputs={'file.wav':pipeline.sha(output)}))
            self.assertTrue(pipeline.stage_valid(run,'mix'))
            output.write_bytes(b'second');self.assertFalse(pipeline.stage_valid(run,'mix'))

    def test_inputs_and_settings_change_run_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.mp4';path.write_bytes(b'media')
            c=self.config();c['source']['path']=str(path)
            first,_=pipeline.identity(c)
            c['cues'][0]['target_text']='Different words.'
            second,_=pipeline.identity(c);self.assertNotEqual(first,second)
            path.write_bytes(b'new media');third,_=pipeline.identity(c);self.assertNotEqual(second,third)

if __name__=='__main__':unittest.main()
