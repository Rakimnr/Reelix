import unittest
import os
from models.recognition_result import MovieRecognitionResult
from services.frame_selector import FrameSelector
from services.candidate_extractor import MovieCandidateExtractor
from services.recognition_orchestrator import RecognitionOrchestrator

class TestPipeline(unittest.TestCase):
    def test_frame_selector_no_frames(self):
        selector = FrameSelector()
        frame, score, reason = selector.select_best_frame([])
        self.assertEqual(frame, "")
        self.assertEqual(reason, "no_frames")

    def test_frame_selector_one_frame(self):
        selector = FrameSelector()
        frame, score, reason = selector.select_best_frame(["fake_frame.jpg"])
        self.assertEqual(frame, "fake_frame.jpg")
        self.assertEqual(reason, "only_frame")

    def test_candidate_extractor(self):
        extractor = MovieCandidateExtractor()
        res = MovieRecognitionResult(
            state="POSSIBLE",
            provider="google_web_movie",
            web_entities=["The Matrix Film", "Keanu Reeves"],
            matching_page_titles=["The Matrix - Wikipedia"],
            best_guess_labels=["the matrix movie scene"]
        )
        candidates = extractor.extract(res)
        
        self.assertTrue(len(candidates) > 0)
        # Should trim "film", "movie", "scene" -> expect "The Matrix"
        top_candidate = candidates[0].title
        self.assertEqual(top_candidate.lower(), "the matrix")
        
        # Verify deduplication / scoring
        # best_guess (weight 3), web_entity (weight 2), page_title (weight 1)
        # total score should be 6
        self.assertEqual(candidates[0].score, 6)

    def test_orchestrator_disabled_providers(self):
        orch = RecognitionOrchestrator()
        health = orch.get_health()
        
        self.assertEqual(health["providers"]["google_web_movie"], "disabled_by_config")
        self.assertEqual(health["providers"]["audd_music"], "disabled_by_config")

if __name__ == '__main__':
    unittest.main()
