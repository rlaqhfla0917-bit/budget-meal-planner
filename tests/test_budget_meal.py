import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from core import load_data, plan_week, DEFAULT_PANTRY


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool, cls.ing, cls.prices, cls.options, cls.audit, cls.meta = load_data()

    def test_source_prices_have_valid_audit(self):
        import pandas as pd
        df = pd.read_csv(Path(__file__).resolve().parents[1] / 'data' / 'price_source_validation.csv')
        self.assertEqual(len(df), len(self.prices))
        self.assertTrue(df['raw_match'].all())
        self.assertTrue(df['formula_ok'].all())

    def test_data_catalog_integrity(self):
        self.assertEqual(len(self.pool), 36)
        self.assertEqual(len(self.options), 2916)
        self.assertEqual(self.audit['strict_menu_items_default_pantry'], 36)
        self.assertEqual(len(self.prices), 38)
        self.assertTrue(self.prices['price_key'].is_unique)
        self.assertTrue((self.prices['won_per_g'] > 0).all())
        self.assertFalse(self.options.duplicated().any())
        keys = set(self.prices['price_key'].astype(str))
        priced = self.ing.loc[self.ing['map_grade'] == 'A']
        self.assertTrue(set(priced['price_key'].dropna().astype(str)).issubset(keys))
        codes = set(self.pool['음식코드'].astype(str))
        for c in ['code1', 'code2', 'code3', 'code4']:
            self.assertTrue(set(self.options[c].astype(str)).issubset(codes))

    def test_audit_summary_is_consistent(self):
        # Precomputed whole-dataset audit (3,220) bundled from original notebook.
        # The deploy package contains the narrower, reviewed 36-menu subset.
        self.assertEqual(self.audit['menu_count'], 3220)
        self.assertEqual(self.audit['all5_complete_menus'], 2929)
        self.assertEqual(round(2929 / 3220 * 100, 1), 91.0)


class TestRecommendation(unittest.TestCase):
    def test_standard_budget(self):
        result = plan_week(30000, 5, 1, DEFAULT_PANTRY, 400, 850, 15, 2000)
        self.assertIsNotNone(result)
        self.assertEqual(len(result['selected']), 5)
        self.assertTrue(result['within_budget'])
        self.assertLessEqual(result['total_cost'], 30000)
        self.assertGreater(result['total_cost'], 0)
        for item in result['selected']:
            self.assertTrue(400 <= item['kcal'] <= 850)
            self.assertGreaterEqual(item['protein_g'], 15)
            self.assertLessEqual(item['sodium_mg'], 2000)

    def test_low_budget_fallback_or_within(self):
        result = plan_week(100, 3, 1, DEFAULT_PANTRY, 400, 850, 15, 2000)
        self.assertIsNotNone(result)
        self.assertFalse(result['within_budget'])
        self.assertGreater(result['total_cost'], 100)

    def test_seven_meals_supported(self):
        # Regression: with three side dishes and max repeat=2 the solver
        # had no feasible solution for seven meals, even at ample budget.
        result = plan_week(40000, 7, 1, DEFAULT_PANTRY, 400, 850, 15, 2000)
        self.assertIsNotNone(result)
        self.assertEqual(len(result['selected']), 7)
        self.assertTrue(result['within_budget'])

    def test_shopping_total_and_selected_count_consistent(self):
        for household in (1, 2):
            result = plan_week(30000, 5, household, DEFAULT_PANTRY)
            self.assertEqual(len(result['selected']), 5)
            # Shopping rows are individually rounded to KRW.
            self.assertAlmostEqual(
                result['total_cost'],
                float(result['shopping']['예상비용_원'].sum()),
                delta=0.51 * len(result['shopping'])
            )

    def test_no_pantry_does_not_crash(self):
        self.assertIsNone(plan_week(20000, 5, 1, [], 400, 850, 15, 2000))

    def test_no_nutrition_match_does_not_crash(self):
        self.assertIsNone(plan_week(30000, 5, 1, DEFAULT_PANTRY, 700, 700, 40, 1000))

    def test_inverted_range_fails_clearly(self):
        with self.assertRaises(ValueError):
            plan_week(30000, 5, 1, DEFAULT_PANTRY, 900, 400, 15, 2000)

    def test_invalid_numeric_inputs(self):
        with self.assertRaises(ValueError):
            plan_week(-1, 5)
        with self.assertRaises(ValueError):
            plan_week(float('nan'), 5)
        with self.assertRaises(ValueError):
            plan_week(30000, 0)


if __name__ == '__main__':
    unittest.main()
