"""Tests for formatting helpers."""

from protonmail_cli.formatting import format_size, strip_html


class TestStripHtml:
    def test_plain_text_unchanged(self):
        assert strip_html("hello world") == "hello world"

    def test_removes_tags(self):
        assert strip_html("<b>bold</b> text") == "bold text"

    def test_br_to_newline(self):
        assert strip_html("line1<br>line2") == "line1\nline2"
        assert strip_html("line1<br/>line2") == "line1\nline2"
        assert strip_html("line1<BR />line2") == "line1\nline2"

    def test_p_to_newline(self):
        result = strip_html("<p>para1</p><p>para2</p>")
        assert "para1" in result
        assert "para2" in result

    def test_decodes_entities(self):
        assert strip_html("&amp; &lt; &gt;") == "& < >"

    def test_collapses_blank_lines(self):
        result = strip_html("a\n\n\n\n\nb")
        assert "\n\n\n" not in result
        assert "a" in result and "b" in result

    def test_strips_whitespace(self):
        assert strip_html("  hello  ") == "hello"

    def test_complex_html(self):
        html = (
            '<div class="x"><p>Hello</p><br><span style="color:red">World</span></div>'
        )
        result = strip_html(html)
        assert "Hello" in result
        assert "World" in result
        assert "<" not in result


class TestFormatSize:
    def test_bytes(self):
        assert format_size(0) == "0B"
        assert format_size(512) == "512B"

    def test_kilobytes(self):
        assert format_size(1024) == "1KB"
        assert format_size(2048) == "2KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1MB"

    def test_gigabytes(self):
        assert format_size(1024**3) == "1GB"

    def test_terabytes(self):
        assert format_size(1024**4) == "1.0TB"
