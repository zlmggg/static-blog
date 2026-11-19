from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

DIST = Path(r"D:\Develop\static-blog\docs\.vitepress\dist")
PAGES = [
    DIST / "projects" / "homelab.html",
    DIST / "projects" / "homelab" / "materials.html",
    DIST / "projects" / "homelab" / "practice" / "index.html",
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value:
                    self.links.append(value)

def target_for(href: str) -> Path | None:
    path = unquote(urlsplit(href).path)
    if path.startswith("/ops-project/files/"):
        return DIST / path.lstrip("/")
    if path.startswith("/projects/"):
        if path.endswith("/"):
            return DIST / path.lstrip("/") / "index.html"
        candidate = DIST / path.lstrip("/")
        return candidate.with_suffix(".html") if candidate.suffix == "" else candidate
    return None

broken = []
for page in PAGES:
    parser = LinkParser()
    parser.feed(page.read_text(encoding="utf-8"))
    for href in parser.links:
        target = target_for(href)
        if target is not None and not target.exists():
            broken.append((page.name, href, str(target)))

if broken:
    print(f"BROKEN {len(broken)}")
    for item in broken:
        print(item)
else:
    print("OK: all project/asset links resolve")
