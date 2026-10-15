import unittest

from app.filename_parser import parse_name


class FilenameParserTests(unittest.TestCase):
    def test_release_title_and_year_ignore_technical_suffix(self):
        parsed = parse_name("The.Dark.Knight.2008.1080p.BluRay.x265.DTS.5.1.mkv")
        self.assertEqual(parsed.title, "The Dark Knight")
        self.assertEqual(parsed.year, 2008)

    def test_underscores_and_webdl(self):
        parsed = parse_name("Le_Pacte_2023.2160p.WEB-DL.mkv")
        self.assertEqual(parsed.title, "Le Pacte")
        self.assertEqual(parsed.year, 2023)

    def test_unicode_and_title_numbers_are_preserved(self):
        parsed = parse_name("L'été 2 (2021).mkv")
        self.assertEqual(parsed.title, "L'été 2")
        self.assertEqual(parsed.year, 2021)

    def test_missing_year_is_unknown(self):
        parsed = parse_name("FilmSansAnnee.mkv")
        self.assertEqual(parsed.title, "FilmSansAnnee")
        self.assertIsNone(parsed.year)


if __name__ == "__main__":
    unittest.main()
