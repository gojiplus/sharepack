"""Sphinx configuration — fleet standard via py-canon."""

from pathlib import Path

from py_canon.sphinx import configure

import sharepack

configure(globals())

# Build the live demos from the fixture apps so the docs site ships working
# artifacts, produced by the exact code being documented.
_generated = Path(__file__).parent / "_generated"
_generated.mkdir(exist_ok=True)
_fixtures = Path(__file__).parents[1] / "tests"
for _fixture, _out in (
    ("fixtures_tasktrack", "demo.html"),
    ("fixtures_flaskapp", "flask-demo.html"),
    ("fixtures_fastapiapp", "fastapi-demo.html"),
):
    sharepack.build(_fixtures / _fixture, _generated / _out)
html_extra_path = ["_generated"]
