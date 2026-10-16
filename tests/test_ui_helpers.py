import sys
import unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from ui_helpers import meal_parts, recipe_search_url, read_history, merge_history, create_record, mark_purchased, history_json, KST

class TestBowllyUIHelpers(unittest.TestCase):
    def test_real_four_component_meal(self):
        parts=meal_parts({"name1":"발아현미밥","name2":"감자짜글이","name3":"고추부각","name4":"배추김치"})
        self.assertEqual([p["role"] for p in parts], ["밥","국·찌개","주메뉴","반찬"])
        self.assertEqual(parts[1]["name"], "감자짜글이")

    def test_recipe_search_uses_encoding(self):
        link=recipe_search_url("배추김치")
        self.assertTrue(link.startswith("https://www.google.com/search?q="))
        self.assertIn("%EB",link)

    def test_invalid_history_is_never_shared(self):
        self.assertEqual(read_history(None),[])
        self.assertEqual(read_history("{bad"),[])
        self.assertEqual(read_history({"items":[{"id":"x","meals":[],"shopping":[]}]} )[0]["id"], "x")

    def test_history_merge_prefers_new(self):
        a={"id":"1","meals":[],"shopping":[],"status":"purchased"}
        old={"id":"1","meals":[],"shopping":[],"status":"planned"}
        self.assertEqual(merge_history([a],[old])[0]["status"], "purchased")

    def test_record_roundtrip(self):
        r={"selected":[{"name1":"밥","name2":"국","name3":"주메뉴","name4":"반찬","kcal":430,"protein_g":19,"sodium_mg":670}],
           "shopping":pd.DataFrame([{"품목":"감자","예상비용_원":1700}]),
           "total_cost":1700,"within_budget":True,"candidate_count":44}
        item=create_record(r,30000,1,5,datetime(2026,10,16,10,30,tzinfo=KST))
        self.assertEqual(item["created_at"],"2026.10.16 10:30")
        self.assertEqual(item["shopping"][0]["품목"],"감자")
        self.assertEqual(read_history(history_json([item]))[0]["id"],item["id"])
        self.assertEqual(mark_purchased(item)["status"],"purchased")

if __name__ == "__main__":
    unittest.main()
