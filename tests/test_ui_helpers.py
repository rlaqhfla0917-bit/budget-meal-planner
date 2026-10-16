import unittest
import json
from datetime import date, datetime
import pandas as pd
from ui_helpers import (
    KST, create_record, meal_parts, recipe_search_url, read_history,
    merge_history, meal_dates, record_dates, item_key,
    toggle_item, shopping_progress, history_json,
)

class TestHistoryAndCalendar(unittest.TestCase):
    def setUp(self):
        self.sample = {
            'selected': [{'name1': '현미밥', 'name2': '미역국', 'name3': '불고기', 'name4': '배추김치',
                          'kcal': 612, 'protein_g': 24, 'sodium_mg': 900}],
            'shopping': pd.DataFrame([{'price_key': 'beef', '품목': '소고기', '예상비용_원': 3500},
                                      {'price_key': 'onion', '품목': '양파', '예상비용_원': 700}]),
            'total_cost': 4200, 'within_budget': True, 'candidate_count': 14,
        }
        self.record = create_record(self.sample, 30000, 2, 1,
                                    now=datetime(2026, 10, 16, 10, 0, tzinfo=KST),
                                    start_date=date(2026, 10, 19))

    def test_calendar_date_range(self):
        self.assertEqual(meal_dates(date(2026, 10, 16), 3),
                         ['2026-10-16', '2026-10-17', '2026-10-18'])
        self.assertEqual(record_dates(self.record), ['2026-10-19'])

    def test_old_records_calendar_fallback(self):
        legacy = {k: v for k, v in self.record.items() if k not in ('meal_dates', 'planned_start')}
        self.assertEqual(record_dates(legacy), ['2026-10-16'])

    def test_no_fake_recipe(self):
        self.assertEqual(meal_parts(self.record['meals'][0])[1]['name'], '미역국')
        self.assertTrue(recipe_search_url('미역국').startswith('https://www.google.com/search?q='))

    def test_checklist_and_roundtrip(self):
        key = item_key(self.record['shopping'][0], 0)
        updated = toggle_item(self.record, key, True)
        self.assertEqual(shopping_progress(updated), (1, 2))
        self.assertEqual(shopping_progress(self.record), (0, 2))
        self.assertEqual(shopping_progress(toggle_item(updated, key, False)), (0, 2))
        self.assertEqual(shopping_progress(read_history(history_json([updated]))[0]), (1, 2))

    def test_duplicate_price_key_stable(self):
        self.assertNotEqual(item_key({'price_key': 'a'}, 0), item_key({'price_key': 'a'}, 1))

    def test_invalid_key_no_effect(self):
        self.assertEqual(toggle_item(self.record, 'bad', True), self.record)

    def test_legacy_checklist_safe(self):
        legacy = dict(self.record)
        legacy.pop('checked_items')
        self.assertEqual(shopping_progress(legacy), (0, 2))

    def test_merge_update_precedence_and_corrupt_json(self):
        older = dict(self.record, status='planned')
        latest = dict(self.record, status='purchased')
        self.assertEqual(merge_history([latest], [older])[0]['status'], 'purchased')
        self.assertEqual(read_history('not-json'), [])
        self.assertEqual(read_history({'items':[self.record]})[0]['id'], self.record['id'])

    def test_three_records_are_private_in_browser_structure(self):
        three = [dict(self.record, id=str(i)) for i in (1, 2, 3)]
        self.assertEqual(len(read_history(json.dumps(three))), 3)

if __name__ == '__main__':
    unittest.main()