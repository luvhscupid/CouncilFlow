import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))

from routing.contract import DecisionStatus, validate_route_config
from routing.core import VectorRouter
from routing.encoders import FastEmbedEncoder, HashEncoder


class TableEncoder:
    encoder_id = "table-v1"

    def __init__(self, values):
        self.values = values

    def encode(self, text):
        return tuple(self.values[text])


class FailingEncoder:
    def encode(self, text):
        raise RuntimeError("encoder unavailable")


class RoutingEncoderTests(unittest.TestCase):
    def config(self):
        return validate_route_config({
            "version": "routing-v1",
            "threshold": 0.7,
            "margin": 0.1,
            "routes": [
                {"name": "docs", "examples": ["docs example"], "metadata": {}},
                {"name": "security", "examples": ["security example"], "metadata": {}},
            ],
        })

    def test_hash_encoder_is_reproducible(self):
        encoder = HashEncoder(8)
        self.assertEqual(encoder.encode("same input"), encoder.encode("same input"))
        self.assertNotEqual(encoder.encode("same input"), encoder.encode("different input"))
        self.assertEqual(len(encoder.encode("same input")), 8)

    def test_vector_router_uses_cosine_score(self):
        encoder = TableEncoder({
            "docs example": (1.0, 0.0),
            "security example": (0.0, 1.0),
            "docs query": (0.99, 0.01),
        })
        decision = VectorRouter(self.config(), encoder).classify("docs query")
        self.assertEqual(decision.status, DecisionStatus.MATCHED)
        self.assertEqual(decision.route, "docs")
        self.assertGreater(decision.confidence, 0.9)
        self.assertEqual(decision.encoder_id, "table-v1")

    def test_encoder_failure_is_unavailable(self):
        decision = VectorRouter(self.config(), FailingEncoder()).classify("docs query")
        self.assertEqual(decision.status, DecisionStatus.UNAVAILABLE)
        self.assertIsNone(decision.route)
        self.assertIn("encoder_failed", decision.reason_codes)

    def test_fastembed_is_not_imported_by_default(self):
        self.assertNotIn("fastembed", sys.modules)

    def test_optional_fastembed_missing_is_explicit(self):
        with patch.dict(sys.modules, {"fastembed": None}):
            encoder = FastEmbedEncoder("missing-model")
            with self.assertRaises(ImportError):
                encoder.encode("text")


if __name__ == "__main__":
    unittest.main()
