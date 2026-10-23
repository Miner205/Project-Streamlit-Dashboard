import unittest
from utils.language import normalize_language
from utils.content import CONTENT

class LanguageTests(unittest.TestCase):
    def test_locales(self):
        for value, expected in [("fr-FR", "fr"), ("en-US", "en"), (" EN_gb ", "en"), (None, "fr"), ("de-DE", "fr"), ({}, "fr")]:
            with self.subTest(value=value):
                self.assertEqual(normalize_language(value), expected)

    def test_content(self):
        self.assertEqual(set(CONTENT["fr"]), set(CONTENT["en"]))
        for lang in ("fr", "en"):
            self.assertEqual(sum(row[1] for row in CONTENT[lang]["rubric"]), 100)
            self.assertEqual(len(CONTENT[lang]["checks"]), 10)

if __name__ == "__main__":
    unittest.main()
