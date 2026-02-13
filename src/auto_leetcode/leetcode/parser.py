from bs4 import BeautifulSoup


def strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()


def extract_code_snippet(snippets: list[dict[str, str]], lang: str = "python3") -> str:
    for snippet in snippets:
        if snippet.get("langSlug") == lang:
            return snippet.get("code", "")
    return ""
