"""Tests for the HTML parser.

The parser produces a canonical recursive node tree (tag / attrs / text /
children). These tests assert targeted behaviours rather than full-tree
equality, using the HTML fixtures in test/data/parse_test/ as inputs.
"""

import os
import unittest

from src.parser import Parser

DATA_DIR = os.path.join("test", "data", "parse_test")


def load_html(name):
    with open(os.path.join(DATA_DIR, f"{name}Test.html"), encoding="utf-8") as f:
        return f.read()


def find_first(node, tag):
    """Depth-first search for the first node with the given tag."""
    if isinstance(node, dict):
        if node.get("tag") == tag:
            return node
        for child in node.get("children", []):
            found = find_first(child, tag)
            if found is not None:
                return found
    return None


def find_all(node, tag, acc=None):
    acc = [] if acc is None else acc
    if isinstance(node, dict):
        if node.get("tag") == tag:
            acc.append(node)
        for child in node.get("children", []):
            find_all(child, tag, acc)
    return acc


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_base_structure(self):
        tree = self.parser.parse(load_html("base"))
        self.assertEqual(tree["tag"], "root")
        html = find_first(tree, "html")
        self.assertIsNotNone(html)
        self.assertEqual(html["attrs"]["lang"], "en")

    def test_doctype_captured(self):
        tree = self.parser.parse(load_html("base"))
        self.assertIn("doctype", tree)
        self.assertEqual(tree["doctype"].lower(), "html")

    def test_class_attribute_is_list(self):
        tree = self.parser.parse(load_html("base"))
        h1 = find_first(tree, "h1")
        self.assertEqual(h1["attrs"]["class"], ["title", "highlight"])
        self.assertEqual(h1["attrs"]["id"], "main-title")

    def test_text_extraction(self):
        tree = self.parser.parse(load_html("base"))
        h1 = find_first(tree, "h1")
        self.assertEqual(h1["text"], "Welcome to Our Website")

    def test_multiple_children_collected(self):
        tree = self.parser.parse(load_html("base"))
        list_items = find_all(tree, "li")
        self.assertGreaterEqual(len(list_items), 3)

    def test_self_closing_tag(self):
        tree = self.parser.parse(load_html("base"))
        img = find_first(tree, "img")
        self.assertIsNotNone(img)
        self.assertEqual(img["attrs"]["src"], "home-image.jpg")
        self.assertNotIn("children", img)

    def test_malformed_html_does_not_crash(self):
        tree = self.parser.parse(load_html("malformed"))
        self.assertEqual(tree["tag"], "root")
        self.assertIsNotNone(find_first(tree, "p"))

    def test_empty_input(self):
        tree = self.parser.parse("")
        self.assertEqual(tree, {"tag": "root", "children": []})

    def test_nested_blocks(self):
        tree = self.parser.parse(load_html("nestedblocks"))
        self.assertEqual(tree["tag"], "root")
        self.assertTrue(tree["children"])


if __name__ == "__main__":
    unittest.main()
