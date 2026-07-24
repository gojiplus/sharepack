"""Sphinx configuration — fleet standard via py-canon."""

from pathlib import Path

from py_canon.sphinx import configure

import sharepack

configure(globals())

# Build the live demo from the fixture app so the docs site ships a working
# artifact at /demo.html, produced by the exact code being documented.
_generated = Path(__file__).parent / "_generated"
_generated.mkdir(exist_ok=True)
sharepack.build(
    Path(__file__).parents[1] / "tests" / "fixtures_tasktrack",
    _generated / "demo.html",
)
html_extra_path = ["_generated"]
