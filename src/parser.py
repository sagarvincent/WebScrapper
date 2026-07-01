"""HTML parser built on BeautifulSoup.

Converts raw HTML into a canonical, recursive JSON-friendly tree. Every
element becomes a node of the form::

    {
        "tag":      "div",
        "attrs":    {"id": "x", "class": ["a", "b"]},
        "text":     "text directly inside this element",
        "children": [ ...child nodes... ],
    }

Empty fields are omitted to keep the output compact. The recursive shape
handles arbitrary nesting, attributes, self-closing tags and malformed
markup uniformly, which makes it convenient for downstream filtering and
ML/analysis pipelines.
"""

from bs4 import BeautifulSoup
from bs4.element import Comment, NavigableString, Tag

# Attributes BeautifulSoup returns as lists by default (class, rel, ...).
# We preserve that list shape; everything else stays a string.


class Parser:
    def __init__(self, features: str = "html.parser"):
        self.features = features

    def parse(self, html_content: str) -> dict:
        """Parse an HTML document into a canonical node tree."""
        soup = BeautifulSoup(html_content or "", self.features)

        root = {"tag": "root", "children": []}

        doctype = self._find_doctype(soup)
        if doctype is not None:
            root["doctype"] = doctype

        for child in soup.children:
            node = self._node(child)
            if node is not None:
                root["children"].append(node)

        return root

    def _find_doctype(self, soup):
        from bs4 import Doctype

        for child in soup.children:
            if isinstance(child, Doctype):
                return str(child)
        return None

    def _node(self, element):
        """Convert a single BeautifulSoup element into a node dict.

        Returns None for content that carries no information (whitespace,
        comments, doctype) so it does not clutter the tree.
        """
        if isinstance(element, Comment):
            return None
        if isinstance(element, NavigableString):
            text = element.strip()
            return {"tag": "#text", "text": text} if text else None
        if not isinstance(element, Tag):
            return None

        node = {"tag": element.name}

        if element.attrs:
            node["attrs"] = dict(element.attrs)

        direct_text = self._direct_text(element)
        if direct_text:
            node["text"] = direct_text

        children = []
        for child in element.children:
            if isinstance(child, NavigableString):
                continue  # captured via direct_text
            child_node = self._node(child)
            if child_node is not None:
                children.append(child_node)
        if children:
            node["children"] = children

        return node

    @staticmethod
    def _direct_text(element) -> str:
        """Concatenate text that sits directly inside this element.

        Text nested inside child elements is left to those children.
        """
        parts = [
            str(child).strip()
            for child in element.children
            if isinstance(child, NavigableString) and not isinstance(child, Comment)
        ]
        return " ".join(p for p in parts if p)
