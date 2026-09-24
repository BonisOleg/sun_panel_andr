from django.test import SimpleTestCase

from src.content.map_embed import normalize_map_embed


class MapEmbedTests(SimpleTestCase):
    def test_url_with_line_breaks_becomes_one_src(self):
        raw = (
            "https://www.google.com/maps/embed?\n"
            "pb=!1m18!1m12!1m3!1d3320.1851524758526!2d34.50!3d49.54\n"
            "!5m2!1suk!2sua"
        )
        src = normalize_map_embed(raw)
        self.assertTrue(src.startswith("https://www.google.com/maps/embed?pb="))
        self.assertNotIn("\n", src)
        self.assertNotIn(" ", src)

    def test_iframe_html_extracts_src(self):
        raw = (
            '<iframe src="https://www.google.com/maps/embed?pb=abc" '
            'width="600" height="450"></iframe>'
        )
        self.assertEqual(
            normalize_map_embed(raw),
            "https://www.google.com/maps/embed?pb=abc",
        )

    def test_coordinates_are_not_a_map_src(self):
        self.assertEqual(normalize_map_embed("49°32'46.2\"N 34°30'06.8\"E"), "")
