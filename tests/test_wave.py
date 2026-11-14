
import os
import struct
from io import BytesIO

import mutagen

from mutagen.wave import WAVE
from mutagen._iff import InvalidChunk
from tests import TestCase, DATA_DIR, get_temp_copy


RIFF_UNKNOWN_SIZE = 0xFFFFFFFF


def _set_riff_size(path, size):
    """Overwrites the size field of the root RIFF chunk."""

    with open(path, "r+b") as fileobj:
        fileobj.seek(4)
        fileobj.write(struct.pack("<I", size))


def _get_riff_size(path):
    with open(path, "rb") as fileobj:
        fileobj.seek(4)
        return struct.unpack("<I", fileobj.read(4))[0]


class TWave(TestCase):
    def test_score_requires_wave_form(self):
        for form, filename in [(b"WEBP", "cover.webp"), (b"AVI ", "video.avi")]:
            header = b"RIFF\x08\x00\x00\x00" + form
            with self.subTest(form=form):
                self.assertEqual(WAVE.score(filename, BytesIO(header), header), 0)
                self.assertIsNone(mutagen.File(BytesIO(header)))

    def test_score_wave_header_and_extensions(self):
        header = b"RIFF\x08\x00\x00\x00WAVE"
        self.assertEqual(WAVE.score("audio", BytesIO(header), header), 2)
        for filename in ("audio.wav", "audio.WAVE"):
            with self.subTest(filename=filename):
                self.assertEqual(WAVE.score(filename, BytesIO(header), header), 3)
                self.assertEqual(WAVE.score(filename, BytesIO(), b""), 1)
        for header in (b"", b"RIFF", b"RIFF\x08\x00\x00\x00WA",
                       b"xxxx\x00\x00\x00\x00WAVE"):
            with self.subTest(header=header):
                self.assertEqual(WAVE.score("audio", BytesIO(header), header), 0)

    def setUp(self):
        fn_wav_pcm_2s_16000_08_id3v23 = \
            os.path.join(DATA_DIR, "silence-2s-PCM-16000-08-ID3v23.wav")
        self.wav_pcm_2s_16000_08_ID3v23 = \
            WAVE(fn_wav_pcm_2s_16000_08_id3v23)

        self.tmp_fn_pcm_2s_16000_08_ID3v23 = \
            get_temp_copy(fn_wav_pcm_2s_16000_08_id3v23)
        self.tmp_wav_pcm_2s_16000_08_ID3v23 = \
            WAVE(self.tmp_fn_pcm_2s_16000_08_ID3v23)

        self.fn_wav_pcm_2s_16000_08_notags = \
            os.path.join(DATA_DIR, "silence-2s-PCM-16000-08-notags.wav")
        self.wav_pcm_2s_16000_08_notags = \
            WAVE(self.fn_wav_pcm_2s_16000_08_notags)

        self.tmp_fn_pcm_2s_16000_08_notag = \
            get_temp_copy(self.fn_wav_pcm_2s_16000_08_notags)
        self.tmp_wav_pcm_2s_16000_08_notag = \
            WAVE(self.tmp_fn_pcm_2s_16000_08_notag)

        fn_wav_pcm_2s_44100_16_id3v23 = \
            os.path.join(DATA_DIR, "silence-2s-PCM-44100-16-ID3v23.wav")
        self.wav_pcm_2s_44100_16_ID3v23 = WAVE(fn_wav_pcm_2s_44100_16_id3v23)

    def test_channels(self):
        self.failUnlessEqual(self.wav_pcm_2s_16000_08_ID3v23.info.channels, 2)
        self.failUnlessEqual(self.wav_pcm_2s_44100_16_ID3v23.info.channels, 2)

    def test_sample_rate(self):
        self.failUnlessEqual(self.wav_pcm_2s_16000_08_ID3v23.info.sample_rate,
                             16000)
        self.failUnlessEqual(self.wav_pcm_2s_44100_16_ID3v23.info.sample_rate,
                             44100)

    def test_number_of_samples(self):
        self.failUnlessEqual(self.wav_pcm_2s_16000_08_ID3v23.
                             info._number_of_samples, 32000)
        self.failUnlessEqual(self.wav_pcm_2s_44100_16_ID3v23.
                             info._number_of_samples, 88200)

    def test_bits_per_sample(self):
        self.failUnlessEqual(self.wav_pcm_2s_16000_08_ID3v23.
                             info.bits_per_sample, 8)
        self.failUnlessEqual(self.wav_pcm_2s_44100_16_ID3v23.
                             info.bits_per_sample, 16)

    def test_bitrate(self):
        self.failUnlessEqual(self.wav_pcm_2s_16000_08_ID3v23.
                             info.bitrate, 256000)
        self.failUnlessEqual(self.wav_pcm_2s_44100_16_ID3v23.
                             info.bitrate, 1411200)

    def test_length(self):
        self.failUnlessAlmostEqual(self.wav_pcm_2s_16000_08_ID3v23.info.length,
                                   2.0, 2)
        self.failUnlessAlmostEqual(self.wav_pcm_2s_44100_16_ID3v23.info.length,
                                   2.0, 2)

    def test_not_my_file(self):
        self.failUnlessRaises(
            InvalidChunk, WAVE, os.path.join(DATA_DIR, "empty.ogg"))

    def test_pprint(self):
        self.wav_pcm_2s_44100_16_ID3v23.pprint()

    def test_mime(self):
        self.failUnless("audio/wav" in self.wav_pcm_2s_44100_16_ID3v23.mime)
        self.failUnless("audio/wave" in self.wav_pcm_2s_44100_16_ID3v23.mime)

    def test_id3_tags(self):
        id3 = self.wav_pcm_2s_44100_16_ID3v23.tags
        self.assertEquals(id3["TALB"], "Quod Libet Test Data")
        self.assertEquals(id3["TCON"], "Silence")
        self.assertEquals(id3["TIT2"], "Silence")
        self.assertEquals(id3["TPE1"], ["piman / jzig"])

    def test_id3_tags_uppercase_chunk(self):
        id3 = self.wav_pcm_2s_16000_08_ID3v23
        self.assertEquals(id3["TALB"], "Quod Libet Test Data")
        self.assertEquals(id3["TCON"], "Silence")
        self.assertEquals(id3["TIT2"], "Silence")
        self.assertEquals(id3["TPE1"], ["piman / jzig"])

    def test_delete(self):
        self.tmp_wav_pcm_2s_16000_08_ID3v23.delete()

        self.failIf(self.tmp_wav_pcm_2s_16000_08_ID3v23.tags)
        self.failUnless(WAVE(self.tmp_fn_pcm_2s_16000_08_ID3v23).tags is None)

    def test_save_no_tags(self):
        self.tmp_wav_pcm_2s_16000_08_ID3v23.tags = None
        self.tmp_wav_pcm_2s_16000_08_ID3v23.save()
        self.assertTrue(self.tmp_wav_pcm_2s_16000_08_ID3v23.tags is None)

    def test_add_tags_already_there(self):
        self.failUnless(self.tmp_wav_pcm_2s_16000_08_ID3v23.tags)
        self.failUnlessRaises(Exception,
                              self.tmp_wav_pcm_2s_16000_08_ID3v23.add_tags)

    def test_roundtrip(self):
        self.failUnlessEqual(self.tmp_wav_pcm_2s_16000_08_ID3v23["TIT2"],
                             ["Silence"])
        self.tmp_wav_pcm_2s_16000_08_ID3v23.save()
        new = WAVE(self.tmp_wav_pcm_2s_16000_08_ID3v23.filename)
        self.failUnlessEqual(new["TIT2"], ["Silence"])

    def test_save_tags(self):
        from mutagen.id3 import TIT1
        tags = self.tmp_wav_pcm_2s_16000_08_ID3v23.tags
        tags.add(TIT1(encoding=3, text="foobar"))
        tags.save()

        new = WAVE(self.tmp_wav_pcm_2s_16000_08_ID3v23.filename)
        self.failUnlessEqual(new["TIT1"], ["foobar"])

    """" Simulate the way Picard writes and update tags """
    def test_picard_lifecycle(self):
        path_tmp_wav_file = \
            get_temp_copy(self.fn_wav_pcm_2s_16000_08_notags)
        from mutagen.id3 import ID3
        wav = WAVE(path_tmp_wav_file)
        id3 = wav.tags
        """" Picard WaveFile._get_tags: """
        self.assertIsNone(id3, "Ensure ID3-tag-header does not exist")
        """" Picard WaveFile._get_tags: initialize tags """
        wav.add_tags()
        id3 = wav.tags
        self.assertIsInstance(id3, ID3)
        """ ID3v2.3 separator """
        separator = '/'
        """ Initialize Picard like metadata tags """
        self.__init_id3_tags(id3, major=3)
        """ Write the Picard like metadata to the empty WAVE-file """
        id3.save(path_tmp_wav_file, v23_sep=separator)
        """ Tags (metadata) have been added; now load the file again """
        wav = WAVE(path_tmp_wav_file)
        id3 = wav.tags
        self.assertIsInstance(id3, ID3)
        self.assertEquals(id3["TRCK"], "1/10")
        self.assertEquals(id3["TPOS"], "1/1")
        self.assertEquals(id3["TXXX:MusicBrainz Release Group Id"],
                          "e00305af-1c72-469b-9a7c-6dc665ca9adc")
        self.assertEquals(id3["TXXX:MusicBrainz Album Artist Id"], [
                          "3fe817fc-966e-4ece-b00a-76be43e7e73c",
                          "984f8239-8fe1-4683-9c54-10ffb14439e9"])
        self.assertEquals(id3["TXXX:CATALOGNUMBER"], ["PRAR931391"])
        self.assertEquals(id3["TSRC"], ["NLB931100460", "USMH51100098"])

    @staticmethod
    def __init_id3_tags(id3, major=3):
        """
        Attributes:
            id3 ID3 Tag object
            major ID3 major version, e.g.: 3 for ID3v2.3
        """
        from mutagen.id3 import TRCK, TPOS, TXXX, TPUB, TALB, UFID, TPE2, \
            TSO2, TMED, TIT2, TPE1, TSRC, IPLS, TORY, TDAT, TYER
        id3.add(TRCK(encoding=major, text="1/10"))
        id3.add(TPOS(encoding=major, text="1/1"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Release Group Id",
                     text="e00305af-1c72-469b-9a7c-6dc665ca9adc"))
        id3.add(TXXX(encoding=major, desc="originalyear", text="2011"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Album Type",
                     text="album"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Album Id",
                     text="e7050302-74e6-42e4-aba0-09efd5d431d8"))
        id3.add(TPUB(encoding=major, text="J&R Adventures"))
        id3.add(TXXX(encoding=major, desc="CATALOGNUMBER", text="PRAR931391"))
        id3.add(TALB(encoding=major, text="Don\'t Explain"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Album Status",
                     text="official"))
        id3.add(TXXX(encoding=major, desc="SCRIPT", text="Latn"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Album Release Country",
                     text="US"))
        id3.add(TXXX(encoding=major, desc="BARCODE", text="804879313915"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Album Artist Id",
                     text=[
                        "3fe817fc-966e-4ece-b00a-76be43e7e73c",
                        "984f8239-8fe1-4683-9c54-10ffb14439e9"]))
        id3.add(TPE2(encoding=major, text="Beth Hart & Joe Bonamassa"))
        id3.add(TSO2(encoding=major, text="Hart, Beth & Bonamassa, Joe"))
        id3.add(TXXX(encoding=major, desc="ASIN", text="B005NPEUB2"))
        id3.add(TMED(encoding=major, text="CD"))
        id3.add(UFID(encoding=major, owner="http://musicbrainz.org",
                     data=b"f151cb94-c909-46a8-ad99-fb77391abfb8"))
        id3.add(TIT2(encoding=major, text="Sinner's Prayer"))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Artist Id",
                     text=[
                        "3fe817fc-966e-4ece-b00a-76be43e7e73c",
                        "984f8239-8fe1-4683-9c54-10ffb14439e9"]))
        id3.add(TPE1(encoding=major, text=["Beth Hart & Joe Bonamassa"]))
        id3.add(TXXX(encoding=major, desc="Artists",
                     text=["Beth Hart", "Joe Bonamassa"]))
        id3.add(TSRC(encoding=major, text=["NLB931100460", "USMH51100098"]))
        id3.add(TXXX(encoding=major, desc="MusicBrainz Release Track Id",
                     text="d062f484-253c-374b-85f7-89aab45551c7"))
        id3.add(IPLS(encoding=major, people=[
            ["engineer", "James McCullagh"],
            ["engineer", "Jared Kvitka"],
            ["arranger", "Jeff Bova"],
            ["producer", "Roy Weisman"],
            ["piano", "Beth Hart"],
            ["guitar", "Blondie Chaplin"],
            ["guitar", "Joe Bonamassa"],
            ["percussion", "Anton Fig"],
            ["drums", "Anton Fig"],
            ["keyboard", "Arlan Schierbaum"],
            ["bass guitar", "Carmine Rojas"],
            ["orchestra", "The Bovaland Orchestra"],
            ["vocals", "Beth Hart"],
            ["vocals", "Joe Bonamassa"]])),
        id3.add(TORY(encoding=major, text="2011"))
        id3.add(TYER(encoding=major, text="2011"))
        id3.add(TDAT(encoding=major, text="2709"))

    def _streaming_copy(self, source):
        """A copy of `source` with the RIFF size set to the streaming
        sentinel value 0xFFFFFFFF, as written by streaming recorders."""

        path = get_temp_copy(source)
        _set_riff_size(path, RIFF_UNKNOWN_SIZE)
        self.addCleanup(os.unlink, path)
        return path

    def test_streaming_riff_size_sentinel_loads(self):
        path = self._streaming_copy(self.fn_wav_pcm_2s_16000_08_notags)
        wav = WAVE(path)
        self.assertIsNone(wav.tags)
        self.assertEqual(wav.info.sample_rate, 16000)

    def test_save_streaming_wav_without_tags(self):
        from mutagen.id3 import TIT2

        path = self._streaming_copy(self.fn_wav_pcm_2s_16000_08_notags)
        wav = WAVE(path)
        wav.add_tags()
        wav.tags.add(TIT2(encoding=3, text=u"streaming title"))
        wav.tags.save(path)

        # The unknown size gets normalized to the actual RIFF size and the
        # tag is readable.
        self.assertEqual(_get_riff_size(path), os.path.getsize(path) - 8)
        new = WAVE(path)
        self.assertEqual(new[u"TIT2"], [u"streaming title"])

        # Saving again must not change the file any further.
        size_after_first_save = os.path.getsize(path)
        new.save()
        self.assertEqual(os.path.getsize(path), size_after_first_save)
        self.assertEqual(_get_riff_size(path),
                         size_after_first_save - 8)

    def test_save_streaming_wav_with_existing_id3_chunk(self):
        from mutagen.id3 import TIT2

        path = self._streaming_copy(
            os.path.join(DATA_DIR,
                         "silence-2s-PCM-16000-08-ID3v23.wav"))
        wav = WAVE(path)
        self.assertEqual(wav[u"TIT2"], [u"Silence"])
        wav.tags.add(TIT2(encoding=3, text=u"updated"))
        wav.tags.save(path)

        self.assertEqual(_get_riff_size(path), os.path.getsize(path) - 8)
        self.assertEqual(WAVE(path)[u"TIT2"], [u"updated"])

    def test_failed_save_does_not_modify_streaming_wav(self):
        from unittest.mock import patch
        from mutagen import _iff
        from mutagen.wave import error as WaveError

        path = self._streaming_copy(self.fn_wav_pcm_2s_16000_08_notags)
        original_data = open(path, "rb").read()

        wav = WAVE(path)
        wav.add_tags()
        # Simulate a write failure while the new chunk is inserted.
        with patch.object(_iff, "insert_bytes",
                          side_effect=OSError("simulated disk error")):
            self.failUnlessRaises(WaveError, wav.tags.save, path)

        # The file must be untouched and keep its streaming sentinel.
        self.assertEqual(open(path, "rb").read(), original_data)
        self.assertEqual(_get_riff_size(path), RIFF_UNKNOWN_SIZE)
