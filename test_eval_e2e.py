import unittest
from eval_e2e import (
    BENCHMARK_SCENARIOS,
    evaluate_single_scenario,
    run_e2e_benchmark,
)
import tempfile
import shutil


class TestE2EBenchmark(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_all_scenarios_pass_in_mock_mode(self):
        """Verifies that all 5 end-to-end benchmark scenarios satisfy all invariants."""
        results = await run_e2e_benchmark(use_mock=True)
        self.assertEqual(len(results), len(BENCHMARK_SCENARIOS))
        for res in results:
            self.assertTrue(res.passed, f"Scenario failed: {res.scenario_name} - {res.notes}")

    async def test_direct_hit_scenario_generates_all_packets(self):
        """Verifies Scenario 1 explicitly generates cover letter, outreach, and application packet."""
        scenario = BENCHMARK_SCENARIOS[0]
        res = await evaluate_single_scenario(scenario, output_dir=self.test_dir, use_mock=True)
        self.assertTrue(res.passed)
        self.assertEqual(res.actual_decision, "APPROVED")
        self.assertTrue(res.has_cover_letter)
        self.assertTrue(res.has_outreach)
        self.assertTrue(res.has_packet)

    async def test_mismatched_scenario_wastes_zero_artifacts(self):
        """Verifies Scenario 3 prevents unnecessary generation and creates no disk files."""
        scenario = BENCHMARK_SCENARIOS[2]
        res = await evaluate_single_scenario(scenario, output_dir=self.test_dir, use_mock=True)
        self.assertTrue(res.passed)
        self.assertEqual(res.actual_decision, "ABORTED")
        self.assertFalse(res.has_cover_letter)
        self.assertFalse(res.has_packet)


if __name__ == "__main__":
    unittest.main()
