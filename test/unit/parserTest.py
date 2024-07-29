import unittest
from src.cparser import parser

class parserTest(unittest.TestCase):

    # initialise the parser
    def intialise(self):
        self.parser = parser()
    # test base case of well formed html
    def test_base(self):
        pass
    # test malformed html code
    def test_malformed(self):
        pass
    # test white space handling
    def test_whitespace(self):
        pass 
    # test handling of self closing tags
    def test_selfclosetags(self):
        pass 
    # test blocks and nested blocks
    def test_blocks(self):
        pass
    def test_nestedblocks(self):
        pass
    # test blocks inside list elements
    def test_listblocks(self):
        pass
    # test multiple blocks in list elements
    def test_mutliblocklist(self):
        pass
    # test special handling for elements liek title
    def test_IDspelements(self):
        pass
    # test handling of HTML entities & char references
    def test_htmlEntChar(self):
        pass 
    # testing handling of span(inline) elements
    def test_inlineelem(self):
        pass 
    # test handling custom scripts or Non-standard markup injection
    def test_customscripts(self):
        pass
    # test handling of different content types and missing content
    def test_content(self):
        pass 
    # test attributes handling
    def test_attributes(self):
        pass
    # test case sensitivity handling
    def test_casesensitivity(self):
        pass
    # test dealing with html versions & doctypes
    def test_htmlversion(self):
        pass
    # test parsing of foreign content
    def test_foreigncontent(self):
        pass
    # test handling contitional comments
    def test_conditionalcomments(self):
        pass
    