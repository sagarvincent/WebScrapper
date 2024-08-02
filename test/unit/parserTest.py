import unittest
import os
import json
from src.cparser import parser

class parserTest(unittest.TestCase):

    # initialise the parser
    def setUp(self):
        self.parser = parser()
        self.test_data_dir = "src/test/data/parse_test/"

    def run_test(self, test_name):
        with open(os.path.join(self.test_data_dir, f"{test_name}Test.html"), "r") as html_file:
            html_content = html_file.read()
        
        with open(os.path.join(self.test_data_dir, f"{test_name}Test.json"), "r") as json_file:
            expected_output = json.load(json_file)
        
        parsed_output = self.parser.parse(html_content)
        self.assertEqual(parsed_output, expected_output)

   
    # Test base case of well-formed HTML
    def test_base(self):
        self.run_test("base")

    # Test malformed HTML code
    def test_malformed(self):
        self.run_test("malformed")

    # Test whitespace handling
    def test_whitespace(self):
        self.run_test("whitespace")

    # Test handling of self-closing tags
    def test_selfclosetags(self):
        self.run_test("selfclosetags")

    # Test blocks
    def test_blocks(self):
        self.run_test("blocks")

    # Test nested blocks
    def test_nestedblocks(self):
        self.run_test("nestedblocks")

    # Test blocks inside list elements
    def test_listblocks(self):
        self.run_test("listblocks")

    # Test multiple blocks in list elements
    def test_multiblocklist(self):
        self.run_test("multiblockslist")

    # Test special handling for elements like title
    def test_IDspelements(self):
        self.run_test("IDspelements")

    # Test handling of HTML entities & character references
    def test_htmlEntChar(self):
        self.run_test("htmlEntChar")

    # Test handling of span (inline) elements
    def test_inlineelem(self):
        self.run_test("inlineelem")

    # Test handling custom scripts or non-standard markup injection
    def test_customscripts(self):
        self.run_test("customscripts")

    # Test handling of different content types and missing content
    def test_content(self):
        self.run_test("content")

    # Test attributes handling
    def test_attributes(self):
        self.run_test("attributes")

    # Test case sensitivity handling
    def test_casesensitivity(self):
        self.run_test("casesensitivity")

    # Test dealing with HTML versions & doctypes
    def test_htmlversion(self):
        self.run_test("htmlversion")

    # Test parsing of foreign content
    def test_foreigncontent(self):
        self.run_test("foreigncontent")

    # Test handling conditional comments
    def test_conditionalcomments(self):
        self.run_test("conditionalcomments")
    