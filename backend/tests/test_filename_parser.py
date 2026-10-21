import unittest

from app.filename_parser import parse_name, parse_tv_name


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


class TvParserTests(unittest.TestCase):
    def test_title_stops_at_episode_marker(self):
        parsed = parse_tv_name("Breaking.Bad.S01E01.1080p.BluRay.x265.mkv")
        self.assertEqual(parsed.title, "Breaking Bad")
        self.assertIsNone(parsed.year)

    def test_year_before_episode_marker(self):
        parsed = parse_tv_name("The Wire 2002 s2e03.mkv")
        self.assertEqual(parsed.title, "The Wire")
        self.assertEqual(parsed.year, 2002)

    def test_alternative_markers(self):
        self.assertEqual(parse_tv_name("Friends.1x05.mkv").title, "Friends")
        self.assertEqual(parse_tv_name("Dark (2017) Saison 2.mkv").title, "Dark")

    def test_no_marker_behaves_like_movies(self):
        self.assertEqual(parse_tv_name("Lost.mkv").title, "Lost")


if __name__ == "__main__":
    unittest.main()
