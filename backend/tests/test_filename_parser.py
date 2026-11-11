import unittest

from app.filename_parser import parse_name, parse_tv_name, strip_order_prefix


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


class OrderPrefixTests(unittest.TestCase):
    """Prefixes numeriques de classement en debut de nom de fichier."""

    def test_spec_examples(self):
        for name in ("01 Prometheus.mkv", "001 - Prometheus.mkv", "01. Prometheus.mkv",
                     "02 Prometheus.mkv", "123 - Prometheus.mkv", "01.Prometheus.mkv",
                     "01-Prometheus.mkv", "001  -  Prometheus.mp4",
                     "01_Prometheus.mkv", "001_Prometheus.mkv", "12 - Prometheus.mkv",
                     "12. Prometheus.mkv", "12-Prometheus.mkv", "05_-_Prometheus.mkv"):
            with self.subTest(name=name):
                self.assertEqual(parse_name(name).title, "Prometheus")

    def test_year_and_technical_info_still_parsed(self):
        parsed = parse_name("01 - Prometheus (2012) 1080p BluRay x265.mkv")
        self.assertEqual(parsed.title, "Prometheus")
        self.assertEqual(parsed.year, 2012)
        parsed = parse_name("02.Alien.1979.1080p.BluRay.mkv")
        self.assertEqual((parsed.title, parsed.year), ("Alien", 1979))

    def test_numbers_elsewhere_are_kept(self):
        parsed = parse_name("Alien 3 (1992).mkv")
        self.assertEqual((parsed.title, parsed.year), ("Alien 3", 1992))
        parsed = parse_name("03 Alien 3 (1992).mkv")
        self.assertEqual((parsed.title, parsed.year), ("Alien 3", 1992))
        self.assertEqual(parse_name("L'été 2 (2021).mkv").title, "L'été 2")

    def test_only_one_prefix_is_removed(self):
        self.assertEqual(parse_name("01 - 12 Monkeys (1995).mkv").title, "12 Monkeys")
        self.assertEqual(parse_tv_name("01 - 24 S01E01.mkv").title, "24")

    def test_name_without_title_is_left_untouched(self):
        # Rien d'alphabetique apres le prefixe : on ne le retire pas.
        self.assertEqual(strip_order_prefix("1917 (2019)"), "1917 (2019)")
        self.assertEqual(strip_order_prefix("123 -"), "123 -")
        self.assertEqual(parse_name("300.mkv").title, "300")

    def test_numbers_that_belong_to_the_title_are_kept(self):
        # Nombre sans zero initial + simple espace ou souligne : c'est le titre.
        cases = {
            "12 Years a Slave (2013).mkv": ("12 Years a Slave", 2013),
            "21 Jump Street (2012).mkv": ("21 Jump Street", 2012),
            "28 Days Later (2002).mkv": ("28 Days Later", 2002),
            "10 Cloverfield Lane.mkv": ("10 Cloverfield Lane", None),
            "2 Alien.mkv": ("2 Alien", None),
            "12_Years_a_Slave_2013.mkv": ("12 Years a Slave", 2013),
            "10.000 BC (2008).mkv": ("10 000 BC", 2008),
        }
        for name, (title, year) in cases.items():
            with self.subTest(name=name):
                parsed = parse_name(name)
                self.assertEqual((parsed.title, parsed.year), (title, year))

    def test_underscore_separator(self):
        self.assertEqual(strip_order_prefix("01_Prometheus"), "Prometheus")
        self.assertEqual(strip_order_prefix("12_Prometheus"), "12_Prometheus")
        parsed = parse_name("01_Prometheus_2012_1080p.mkv")
        self.assertEqual((parsed.title, parsed.year), ("Prometheus", 2012))

    def test_decimal_number_is_not_a_prefix(self):
        self.assertEqual(strip_order_prefix("1.5 Hours"), "1.5 Hours")

    def test_no_prefix_no_change(self):
        self.assertEqual(strip_order_prefix("Prometheus"), "Prometheus")
        self.assertEqual(strip_order_prefix("Prometheus 2012"), "Prometheus 2012")

    def test_tv_names(self):
        self.assertEqual(parse_tv_name("01 - Breaking.Bad.S01E01.mkv").title, "Breaking Bad")
        self.assertEqual(parse_tv_name("01. Dark (2017) Saison 2.mkv").title, "Dark")
        self.assertEqual(parse_tv_name("Friends.1x05.mkv").title, "Friends")


if __name__ == "__main__":
    unittest.main()
