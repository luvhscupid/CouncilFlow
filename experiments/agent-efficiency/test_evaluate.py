import json
import unittest
from pathlib import Path
from evaluate import evaluate, draft_protocol

FIX=Path(__file__).parent/"fixtures"/"paired-evaluation.json"

class EvaluationTests(unittest.TestCase):
    def setUp(self): self.pairs=json.loads(FIX.read_text())

    def test_paired_metrics_keep_missing_values_and_find_blind_spot(self):
        result=evaluate(self.pairs,minimum_worthwhile_improvement=.1,reliability_threshold=.8,spending_budget=10)
        self.assertEqual(result["pair_count"],3)
        self.assertEqual(result["accepted_cost_improvement_fraction"]["n"],2)
        self.assertEqual(result["reliability"]["optimized"]["known"],3)
        self.assertEqual(result["digest_missed_failures"][0]["task_id"],"task-2")
        self.assertIsNone(result["spending"]["observed_total"])
        self.assertEqual(result["provisional_outcome"],"CLOSED_NO_BENEFIT")
        self.assertEqual(result["approval_status"],"NOT_APPROVED; offline analysis only")

    def test_task_mismatch_rejected(self):
        self.pairs[0]["optimized"]["task_id"]="different"
        with self.assertRaises(ValueError): evaluate(self.pairs,minimum_worthwhile_improvement=0,reliability_threshold=0,spending_budget=1)

    def test_protocol_is_draft_and_hash_binding_precedes_run(self):
        p=draft_protocol(task_set="owner-selected fixture tasks",minimum_worthwhile_improvement=.1,reliability_threshold=.95,spending_budget=5,max_runs=12,max_elapsed_minutes=30)
        self.assertEqual(p["status"],"PROPOSED_FOR_OWNER_APPROVAL")
        self.assertIn("SHA-256",p["hash_binding"])
        self.assertIn("does not approve",p["approval"])

if __name__=="__main__": unittest.main()
