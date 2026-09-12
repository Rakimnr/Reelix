import unittest
from unittest.mock import patch, Mock
import os
import requests

from providers.google_web_movie_provider import GoogleWebMovieProvider
from providers.audd_music_provider import AudDMusicProvider
from services.metadata_service import MetadataService
from services.recognition_orchestrator import RecognitionOrchestrator
import config

class TestExternalProviders(unittest.TestCase):

    def setUp(self):
        # Create a dummy image file for testing
        self.dummy_img = "test_dummy.jpg"
        with open(self.dummy_img, "wb") as f:
            f.write(b"dummy image data")
            
        self.dummy_audio = "test_dummy.wav"
        with open(self.dummy_audio, "wb") as f:
            f.write(b"dummy audio data")

    def tearDown(self):
        if os.path.exists(self.dummy_img):
            os.remove(self.dummy_img)
        if os.path.exists(self.dummy_audio):
            os.remove(self.dummy_audio)

    @patch('providers.google_web_movie_provider.config')
    @patch('requests.post')
    def test_google_web_success(self, mock_post, mock_config):
        mock_config.GOOGLE_WEB_DETECTION_ENABLED = True
        mock_config.GOOGLE_API_KEY = "dummy_key"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "responses": [{
                "webDetection": {
                    "bestGuessLabels": [{"label": "the matrix movie scene"}],
                    "webEntities": [{"description": "The Matrix"}],
                    "pagesWithMatchingImages": [{"pageTitle": "The Matrix (1999) - IMDb"}]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        provider = GoogleWebMovieProvider()
        res = provider.recognize([self.dummy_img])
        
        self.assertEqual(res.state, "POSSIBLE")
        self.assertEqual(res.best_guess_labels, ["the matrix movie scene"])
        self.assertEqual(res.web_entities, ["The Matrix"])

    @patch('providers.google_web_movie_provider.config')
    @patch('requests.post')
    def test_google_web_timeout(self, mock_post, mock_config):
        mock_config.GOOGLE_WEB_DETECTION_ENABLED = True
        mock_config.GOOGLE_API_KEY = "dummy_key"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        provider = GoogleWebMovieProvider()
        res = provider.recognize([self.dummy_img])
        self.assertEqual(res.state, "ERROR")

    @patch('providers.audd_music_provider.config')
    @patch('requests.post')
    def test_audd_success(self, mock_post, mock_config):
        mock_config.AUDD_ENABLED = True
        mock_config.AUDD_API_TOKEN = "dummy_token"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "result": {
                "title": "Never Gonna Give You Up",
                "artist": "Rick Astley"
            }
        }
        mock_post.return_value = mock_response
        
        provider = AudDMusicProvider()
        res = provider.recognize(self.dummy_audio)
        self.assertEqual(res.state, "MATCH")
        self.assertEqual(res.track, "Never Gonna Give You Up")
        self.assertEqual(res.artist, "Rick Astley")

    @patch('providers.audd_music_provider.config')
    @patch('requests.post')
    def test_audd_timeout(self, mock_post, mock_config):
        mock_config.AUDD_ENABLED = True
        mock_config.AUDD_API_TOKEN = "dummy_token"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        provider = AudDMusicProvider()
        res = provider.recognize(self.dummy_audio)
        self.assertEqual(res.state, "ERROR")

    @patch('services.metadata_service.config')
    @patch('requests.get')
    def test_tmdb_resolution_success(self, mock_get, mock_config):
        mock_config.TMDB_BEARER_TOKEN = "dummy"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "id": 123,
                "title": "The Matrix",
                "media_type": "movie"
            }]
        }
        mock_get.return_value = mock_response
        
        service = MetadataService()
        meta = service.resolve_candidates(["the matrix"])
        self.assertIsNotNone(meta)
        self.assertEqual(meta["canonical_title"], "The Matrix")

    @patch('services.metadata_service.config')
    @patch('requests.get')
    def test_tmdb_resolution_no_match(self, mock_get, mock_config):
        mock_config.TMDB_BEARER_TOKEN = "dummy"
        mock_config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS = 8
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        service = MetadataService()
        meta = service.resolve_candidates(["random nonsensical title"])
        self.assertIsNone(meta)

    @patch('services.recognition_orchestrator.GoogleWebMovieProvider')
    @patch('services.recognition_orchestrator.LocalMovieProvider')
    def test_orchestrator_fallback_behavior(self, MockLocal, MockGoogle):
        # Even if external throws error, it shouldn't break the orchestrator
        local_inst = MockLocal.return_value
        local_res = Mock()
        local_res.state = "NO_MATCH"
        local_res.provider = "local_index"
        local_inst.recognize.return_value = local_res
        
        google_inst = MockGoogle.return_value
        google_res = Mock()
        google_res.state = "ERROR" # Simulate timeout/error
        google_res.provider = "google_web_movie"
        google_inst.recognize.return_value = google_res
        
        orch = RecognitionOrchestrator()
        # Mock frame selector to avoid needing actual files
        orch.frame_selector.select_best_frame = Mock(return_value=("dummy.jpg", 1.0, "fake"))
        
        res = orch.recognize_movie(["dummy.jpg"])
        
        # Should gracefully fall back to returning NO_MATCH without raising an exception
        self.assertEqual(res["state"], "NO_MATCH")

if __name__ == '__main__':
    unittest.main()
