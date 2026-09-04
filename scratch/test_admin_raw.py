import sys
import unittest
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
sys.path.insert(0, r"c:\Users\ManuyNoe\.gemini\antigravity-ide\scratch\gangacheck\backend")

from app import app
from config import ADMIN_SECRET_KEY

class TestAdminRawListings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.headers = {"Authorization": f"Bearer {ADMIN_SECRET_KEY}"}

    def test_get_raw_listings(self):
        resp = self.client.get("/api/admin/raw-listings?limit=10", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("listings", data)
        self.assertIn("stats", data)
        print(f"✅ /api/admin/raw-listings returned {len(data['listings'])} items.")

    def test_harvest_endpoint(self):
        payload = {"keyword": "ps5", "platform": "vinted", "limit": 5}
        resp = self.client.post("/api/admin/harvest", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("metrics", data)
        self.assertIn("median_price", data["metrics"])
        print(f"✅ /api/admin/harvest returned: Median={data['metrics']['median_price']}€, Items={len(data.get('listings', []))}")

    def test_save_benchmark_from_harvest(self):
        payload = {
            "product_key": "test_harvest_ps5",
            "display_name": "Test Harvest PS5 Console",
            "median_price": 420.0,
            "min_normal_price": 380.0,
            "max_normal_price": 460.0,
            "category": "Consolas"
        }
        resp = self.client.post("/api/admin/save-benchmark-from-harvest", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("success"))
        print("✅ /api/admin/save-benchmark-from-harvest succeeded.")

if __name__ == "__main__":
    unittest.main()
