"""Canonical, single-source style-attribute/style-block inventory helper.

BYS360 CSP migration waves (Style-1, Style-2A, Style-2B, ...) all need the
SAME repo-wide counting methodology so their contract tests agree with each
other and with manual verification. This module is the one canonical
implementation; no other test file should hand-roll its own regex scan of
the whole repo for these numbers again.

Methodology (deliberately NOT a naive regex over raw file text):

- Uses ``html.parser.HTMLParser`` (stdlib) to actually tokenize each
  template into tags/attributes, so occurrences of the literal text
  ``style=`` inside HTML comments, inside a `<script>`/`<style>` block's own
  text content, inside a Jinja comment (`{# ... #}`), or inside a plain
  documentation/example string are never miscounted as a real HTML
  attribute. ``HTMLParser`` treats ``<script>`` and ``<style>`` as CDATA
  content elements (their inner text is never re-scanned for tags), and
  comments are delivered via ``handle_comment`` instead of being scanned
  for tags/attributes.
- BEFORE tokenizing, ``{% ... %}``/``{{ ... }}`` Jinja spans that occur
  OUTSIDE any quoted string are neutralized (replaced with matching-length
  whitespace, preserving newlines so line numbers stay accurate). This
  repo's templates routinely put a *bare*, unquoted Jinja conditional in
  the middle of a tag to conditionally include a whole attribute, e.g.
  ``<span class="mini-badge" {% if badge|int <= 0 %}style="display:none;"
  {% endif %}>`` (see app/templates/base.html around line 471) or
  ``<input ... {% if checked %}checked{% endif %} style="...">`` (see
  app/templates/settings.html around line 1440). A raw ``HTMLParser`` loses
  sync on the unquoted ``%`` characters and silently drops the tag's
  remaining attributes -- including the genuinely real, fully-static
  ``style="..."`` that follows. This is a parser tokenizer limitation, not
  a false positive: the attribute is really present in the rendered output
  (conditionally), and its value is genuinely static (no ``{{``/``{%``
  inside the quotes), so it must count. Jinja that occurs INSIDE a quoted
  attribute value (e.g. ``style="margin-top:{{ x }}px"``) is left
  untouched by this pass, since that quoted content is exactly what the
  dynamic/static classification below inspects.
- A ``style`` attribute is "dynamic" iff its literal value contains ``{{``
  or ``{%`` (Jinja expression or statement syntax); otherwise it is
  "active"/"static".
- ``<style>`` blocks are counted as literal ``<style`` start tags seen by
  the parser (i.e. real style-block elements, not incidental text).
- Scope is exactly: ``app/templates``, ``app/modules/*/templates``,
  ``app/workflow/templates`` -- matching the Flask/Jinja template roots
  actually used by ``render_template``. ``app/static`` HTML (PWA
  offline pages) is deliberately excluded: it is served as a static file,
  not rendered via Jinja, and mixing it in previously caused a scope bug
  (see test_csp_style2a_repo_wide_contract.py history).
- Files are deduplicated by resolved absolute path so that if two scope
  roots ever overlapped, the same file could not be double-counted.
"""

from __future__ import annotations

import dataclasses
import subprocess
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

STYLE_ATTR_SCOPE_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "app" / "templates",
    *sorted((REPO_ROOT / "app" / "modules").glob("*/templates")),
    REPO_ROOT / "app" / "workflow" / "templates",
)


def _neutralize_bare_jinja(text: str) -> str:
    """Blank out `{% ... %}` / `{{ ... }}` spans that sit OUTSIDE any
    quoted string, preserving length and newlines so `HTMLParser`'s line
    numbers still line up with the original source. Content inside single
    or double quotes is left byte-for-byte untouched."""
    out = list(text)
    quote: str | None = None
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if text.startswith("{%", i) or text.startswith("{{", i):
            close = "%}" if text[i + 1] == "%" else "}}"
            end = text.find(close, i + 2)
            end = (end + len(close)) if end != -1 else n
            for j in range(i, end):
                if out[j] != "\n":
                    out[j] = " "
            i = end
            continue
        i += 1
    return "".join(out)


@dataclasses.dataclass(frozen=True)
class StyleAttrHit:
    path: str
    line: int
    value: str
    dynamic: bool


@dataclasses.dataclass(frozen=True)
class InventoryResult:
    active_static_total: int
    dynamic_total: int
    style_block_total: int
    attr_hits: tuple[StyleAttrHit, ...]
    inline_handler_total: int
    javascript_url_total: int


class _StyleInventoryHTMLParser(HTMLParser):
    """Collects style attrs / style blocks / inline handlers / js: urls."""

    _URL_ATTRS = {"href", "src", "action", "formaction"}

    def __init__(self, relative_path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.relative_path = relative_path
        self.attr_hits: list[StyleAttrHit] = []
        self.style_block_total = 0
        self.inline_handler_total = 0
        self.javascript_url_total = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_any_tag(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_any_tag(tag, attrs)

    def _handle_any_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "style":
            self.style_block_total += 1
        line, _ = self.getpos()
        for name, value in attrs:
            if value is None:
                continue
            lname = name.lower()
            if lname == "style":
                dynamic = "{{" in value or "{%" in value
                self.attr_hits.append(
                    StyleAttrHit(
                        path=self.relative_path,
                        line=line,
                        value=value,
                        dynamic=dynamic,
                    )
                )
            elif lname.startswith("on") and len(lname) > 2:
                self.inline_handler_total += 1
            elif lname in self._URL_ATTRS and value.strip().lower().startswith("javascript:"):
                self.javascript_url_total += 1


def _iter_scope_files(roots: tuple[Path, ...] = STYLE_ATTR_SCOPE_ROOTS) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for html_file in sorted(root.rglob("*.html")):
            resolved = html_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(html_file)
    return files


def compute_inventory_from_worktree(
    roots: tuple[Path, ...] = STYLE_ATTR_SCOPE_ROOTS,
) -> InventoryResult:
    """Canonical inventory of the current on-disk working tree."""
    active = dynamic = blocks = handlers = jsurls = 0
    hits: list[StyleAttrHit] = []
    for html_file in _iter_scope_files(roots):
        relative_path = str(html_file.relative_to(REPO_ROOT))
        text = html_file.read_text(encoding="utf-8", errors="replace")
        parser = _StyleInventoryHTMLParser(relative_path)
        parser.feed(_neutralize_bare_jinja(text))
        parser.close()
        blocks += parser.style_block_total
        handlers += parser.inline_handler_total
        jsurls += parser.javascript_url_total
        for hit in parser.attr_hits:
            hits.append(hit)
            if hit.dynamic:
                dynamic += 1
            else:
                active += 1
    return InventoryResult(
        active_static_total=active,
        dynamic_total=dynamic,
        style_block_total=blocks,
        attr_hits=tuple(hits),
        inline_handler_total=handlers,
        javascript_url_total=jsurls,
    )


def compute_inventory_at_git_ref(git_ref: str) -> InventoryResult:
    """Canonical inventory of the scope roots as of a specific git commit.

    Uses `git ls-tree` + `git show <ref>:<path>` so no checkout/worktree
    mutation is required -- safe to call against a different commit while
    the actual worktree has uncommitted changes.
    """
    active = dynamic = blocks = handlers = jsurls = 0
    hits: list[StyleAttrHit] = []
    relative_roots = [
        str(root.relative_to(REPO_ROOT)).replace("\\", "/") for root in STYLE_ATTR_SCOPE_ROOTS
    ]
    seen: set[str] = set()
    for relative_root in relative_roots:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", git_ref, "--", relative_root],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line.lower().endswith(".html") or line in seen:
                continue
            seen.add(line)
            show = subprocess.run(
                ["git", "show", f"{git_ref}:{line}"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            if show.returncode != 0:
                continue
            parser = _StyleInventoryHTMLParser(line)
            parser.feed(_neutralize_bare_jinja(show.stdout))
            parser.close()
            blocks += parser.style_block_total
            handlers += parser.inline_handler_total
            jsurls += parser.javascript_url_total
            for hit in parser.attr_hits:
                hits.append(hit)
                if hit.dynamic:
                    dynamic += 1
                else:
                    active += 1
    return InventoryResult(
        active_static_total=active,
        dynamic_total=dynamic,
        style_block_total=blocks,
        attr_hits=tuple(hits),
        inline_handler_total=handlers,
        javascript_url_total=jsurls,
    )


def count_static_style_attrs_in_text(text: str, relative_path: str = "<memory>") -> int:
    """Static (non-Jinja) `style=` attribute count for a single in-memory
    HTML/Jinja source string (used to diff before/after a single template)."""
    parser = _StyleInventoryHTMLParser(relative_path)
    parser.feed(_neutralize_bare_jinja(text))
    parser.close()
    return sum(1 for hit in parser.attr_hits if not hit.dynamic)
