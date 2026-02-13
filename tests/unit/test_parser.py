from auto_leetcode.leetcode.parser import extract_code_snippet, strip_html


class TestStripHtml:
    def test_strips_tags(self) -> None:
        html = "<p>Given an array of integers <code>nums</code></p>"
        result = strip_html(html)
        assert "Given an array" in result
        assert "<p>" not in result
        assert "<code>" not in result

    def test_empty_string(self) -> None:
        assert strip_html("") == ""

    def test_plain_text(self) -> None:
        assert strip_html("hello world") == "hello world"


class TestExtractCodeSnippet:
    def test_finds_python3(self) -> None:
        snippets = [
            {"langSlug": "java", "code": "class Solution {}"},
            {"langSlug": "python3", "code": "class Solution:\n    def twoSum(self):"},
            {"langSlug": "cpp", "code": "class Solution {};"},
        ]
        result = extract_code_snippet(snippets)
        assert "def twoSum" in result

    def test_missing_python3(self) -> None:
        snippets = [{"langSlug": "java", "code": "class Solution {}"}]
        assert extract_code_snippet(snippets) == ""

    def test_empty_list(self) -> None:
        assert extract_code_snippet([]) == ""

    def test_custom_lang(self) -> None:
        snippets = [{"langSlug": "golang", "code": "func twoSum()"}]
        result = extract_code_snippet(snippets, lang="golang")
        assert "func twoSum" in result
