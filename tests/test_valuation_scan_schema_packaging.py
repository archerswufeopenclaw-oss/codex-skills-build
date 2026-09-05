from pathlib import Path
import json
import unittest


class ValuationSchemaPackagingTests(unittest.TestCase):
    def test_installable_schema_matches_existing_repository_contract(self) -> None:
        root = Path(__file__).resolve().parents[1] / "valuation-scan"
        filename = "valuation_scan_terminal_receipt_v2.schema.json"
        existing = json.loads((root / "schemas" / filename).read_text(encoding="utf-8"))
        bundled = json.loads((root / "router" / "references" / filename).read_text(encoding="utf-8"))
        self.assertEqual(bundled, existing)


if __name__ == "__main__":
    unittest.main()
