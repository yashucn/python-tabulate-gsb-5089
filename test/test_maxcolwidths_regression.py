"""Regression tests for maxcolwidths / maxheadercolwidths / rowalign fixes:

- sequence parameters given as tuples behave exactly like lists
- the maxcolwidths wrapping path honors disable_numparse
- blank lines inside cells survive wrapping
- OSC 8 hyperlinks wrap by visible width without being split
"""

import pytest

from tabulate import _CustomTextWrap, _strip_ansi, tabulate

from common import assert_equal


# (1) sequence-type parameters must accept tuples just like lists


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rowalign": ("top", "bottom")},
        {"maxheadercolwidths": (4, 4)},
        {"maxcolwidths": (5,)},  # shorter than the number of columns
        {"maxcolwidths": (5, 5)},
        {"colalign": ("right", "left")},
        {"headers": ("c1", "c2")},
        {"headers": ("c1", "c2"), "maxcolwidths": (5, 5), "colalign": ("left", "left")},
    ],
)
def test_sequence_arguments_accept_tuples(kwargs):
    "Regression: tuple sequence arguments behave exactly like lists"
    table = [["alpha beta", "gamma\ndelta"], ["x", "y"]]
    headers = kwargs.pop("headers", ["c1", "c2"])
    tuple_kwargs = dict(kwargs)
    list_kwargs = {key: list(value) for key, value in kwargs.items()}
    result_tuple = tabulate(table, headers=list(headers), tablefmt="grid", **tuple_kwargs)
    result_list = tabulate(table, headers=headers, tablefmt="grid", **list_kwargs)
    assert_equal(result_list, result_tuple)


def test_rowalign_tuple_expected_output():
    "Regression: rowalign given as a tuple aligns rows vertically"
    table = [["a1\na2", "b1"], ["a3", "b2\nb3"]]
    expected = "\n".join(
        [
            "+------+------+",
            "| c1   | c2   |",
            "+======+======+",
            "| a1   | b1   |",
            "| a2   |      |",
            "+------+------+",
            "|      | b2   |",
            "| a3   | b3   |",
            "+------+------+",
        ]
    )
    result = tabulate(
        table, headers=["c1", "c2"], tablefmt="grid", rowalign=("top", "bottom")
    )
    assert_equal(expected, result)


def test_maxheadercolwidths_tuple_expected_output():
    "Regression: maxheadercolwidths given as a tuple wraps headers"
    expected = "\n".join(
        [
            "+--------+",
            "| alph   |",
            "| a      |",
            "| beta   |",
            "+========+",
            "| x      |",
            "+--------+",
        ]
    )
    result = tabulate([["x"]], headers=["alpha beta"], tablefmt="grid", maxheadercolwidths=(4,))
    assert_equal(expected, result)


def test_scalar_arguments_unchanged():
    "Regression: scalar rowalign and int maxcolwidths keep their meaning"
    table = [["a1\na2", "b1"]]
    result_str = tabulate(table, headers=["c1", "c2"], tablefmt="grid", rowalign="top")
    result_tuple = tabulate(table, headers=["c1", "c2"], tablefmt="grid", rowalign=("top",))
    assert_equal(result_str, result_tuple)
    result_int = tabulate(table, headers=["c1", "c2"], tablefmt="grid", maxcolwidths=3)
    result_list = tabulate(table, headers=["c1", "c2"], tablefmt="grid", maxcolwidths=[3, 3])
    assert_equal(result_int, result_list)


# (2) the maxcolwidths wrapping path must honor disable_numparse


@pytest.mark.parametrize("value", ["80,443", "100,120", "1,000"])
def test_maxcolwidths_disable_numparse_no_type_conversion(value):
    "Regression: disable_numparse=True must not cast cells while wrapping"
    row = ["ports", "str", "comma-separated port list", value]
    headers = ["name", "type", "desc", "default"]
    result = tabulate(
        [row], headers, tablefmt="grid", disable_numparse=True, maxcolwidths=40
    )
    expected = tabulate([row], headers, tablefmt="grid", disable_numparse=True)
    assert_equal(expected, result)


@pytest.mark.parametrize("value", ["80,443", "100,120", "1,000"])
def test_maxcolwidths_thousands_separator_no_crash(value):
    "Regression: number-like strings must not crash wrapping even with numparse"
    row = ["ports", "str", "desc", value]
    headers = ["name", "type", "desc", "default"]
    result = tabulate([row], headers, tablefmt="grid", maxcolwidths=40)
    assert value in result


@pytest.mark.parametrize(
    "value", ["007", "0012", "1_000", "1.50", "True", "0x10", "80,443"]
)
def test_maxcolwidths_disable_numparse_preserves_strings(value):
    "Regression: disable_numparse=True keeps string cells byte-identical"
    result = tabulate([[value]], tablefmt="grid", disable_numparse=True, maxcolwidths=40)
    expected = tabulate([[value]], tablefmt="grid", disable_numparse=True)
    assert_equal(expected, result)
    assert value in result


# (3) blank lines inside cells must survive wrapping


def test_maxcolwidths_preserves_blank_lines():
    "Regression: empty lines inside cells are preserved when wrapping"
    expected = "\n".join(
        [
            "+---------+",
            "| c       |",
            "+=========+",
            "| para 1  |",
            "|         |",
            "|  para 2 |",
            "+---------+",
        ]
    )
    result = tabulate([["para 1\n\n para 2"]], headers=["c"], tablefmt="grid", maxcolwidths=20)
    assert_equal(expected, result)


def test_maxcolwidths_preserves_consecutive_blank_lines():
    "Regression: consecutive empty lines inside cells are preserved"
    expected = "\n".join(
        [
            "+-----+",
            "| c   |",
            "+=====+",
            "| a   |",
            "|     |",
            "|     |",
            "| b   |",
            "+-----+",
        ]
    )
    result = tabulate([["a\n\n\nb"]], headers=["c"], tablefmt="grid", maxcolwidths=20)
    assert_equal(expected, result)


def test_maxcolwidths_blank_lines_still_wrap_to_width():
    "Regression: wrapping still honors maxcolwidths around blank lines"
    expected = "\n".join(
        [
            "+------+",
            "| c    |",
            "+======+",
            "| aaaa |",
            "| bbbb |",
            "|      |",
            "| cccc |",
            "| dddd |",
            "+------+",
        ]
    )
    result = tabulate([["aaaa bbbb\n\ncccc dddd"]], headers=["c"], tablefmt="grid", maxcolwidths=6)
    assert_equal(expected, result)


def test_maxcolwidths_without_blank_lines_unchanged():
    "Regression: cells without blank lines wrap exactly as before"
    expected = "\n".join(
        [
            "+-----------+",
            "| 123456789 |",
            "| bbb       |",
            "| ccc       |",
            "+-----------+",
        ]
    )
    result = tabulate([["123456789 bbb\nccc"]], tablefmt="grid", maxcolwidths=10)
    assert_equal(expected, result)


# (4) OSC 8 hyperlinks must wrap by visible width


LINK = "\x1b]8;;http://example.com\x1b\\click here\x1b]8;;\x1b\\"


def test_maxcolwidths_hyperlink_not_split_when_visible_text_fits():
    "Regression: hyperlinks whose visible text fits are not wrapped"
    expected = "\n".join(
        [
            "+------------+------+",
            "| h1         | h2   |",
            "+============+======+",
            f"| {LINK} | b    |",
            "+------------+------+",
        ]
    )
    result = tabulate(
        [[LINK, "b"]], headers=["h1", "h2"], tablefmt="grid", maxcolwidths=[10, None]
    )
    assert_equal(expected, result)
    assert "http://example.com" in result
    assert "\x1b]8;;\x1b\\" in result


def test_maxcolwidths_hyperlink_wraps_by_visible_width():
    "Regression: hyperlinks wrap by visible width, escape sequences stay intact"
    link = "\x1b]8;;http://example.com\x1b\\click here now\x1b]8;;\x1b\\"
    result = tabulate(
        [[link, "b"]], headers=["h1", "h2"], tablefmt="grid", maxcolwidths=[10, None]
    )
    # visible text is wrapped, escape sequences are not counted as width
    assert "click here" in result
    assert "now" in result
    # the full hyperlink (URI and closing sequence) survives
    assert "http://example.com" in result
    assert "\x1b]8;;\x1b\\" in result
    # no escape sequence fragments are produced
    assert _strip_ansi(result).count("click here") == 1


@pytest.mark.parametrize("width", [5, 8, 10, 13, 20])
def test_maxcolwidths_hyperlink_visible_text_preserved(width):
    "Regression: stripping ANSI from wrapped hyperlinks yields the visible text"
    result = tabulate([[LINK]], headers=["h"], tablefmt="grid", maxcolwidths=[width])
    assert "http://example.com" in result
    assert "\x1b]8;;\x1b\\" in result
    visible_words = [
        word
        for line in _strip_ansi(result).splitlines()
        for word in line.replace("|", " ").split()
        if word in ("click", "here")
    ]
    assert_equal(["click", "here"], visible_words)


def test_strip_ansi_partial_hyperlink_sequences():
    "Regression: split hyperlink opening/closing sequences are zero-width"
    assert_equal("click", _strip_ansi("\x1b]8;;http://example.com\x1b\\click"))
    assert_equal("here", _strip_ansi("here\x1b]8;;\x1b\\"))
    assert_equal("click here", _strip_ansi(LINK))


def test_maxcolwidths_csi_colors_still_wrap_with_reset():
    "Regression: CSI color sequences still wrap by visible width and get reset"
    data = "This is a \x1b[31mtest string for testing TextWrap\x1b[0m with colors"
    expected = [
        "This is a \x1b[31mtest string for\x1b[0m",
        "\x1b[31mtesting TextWrap\x1b[0m with",
        "colors",
    ]
    result = _CustomTextWrap(width=25).wrap(data)
    assert_equal(expected, result)
