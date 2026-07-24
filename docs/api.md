# Python API

Everything the CLI does is available programmatically:

```python
from pathlib import Path

import sharepack

result = sharepack.build(Path("myproject"), Path("demo.html"))
print(result.n_files, "files,", result.size_bytes, "bytes")
for skipped in result.skipped:
    print("skipped:", skipped.path, "—", skipped.reason)
```

Errors are typed: `build` raises {class}`sharepack.ProjectError` for a bad
project path and {class}`sharepack.DetectionError` when no supported
framework is found — both subclasses of {class}`sharepack.SharepackError`.

## sharepack

```{eval-rst}
.. automodule:: sharepack
   :members:
   :imported-members:
```

## sharepack.collect

```{eval-rst}
.. automodule:: sharepack.collect
   :members: collect, CollectionResult, SkippedFile
   :no-index:
```

## sharepack.build

```{eval-rst}
.. automodule:: sharepack.build
   :members: build, BuildResult
   :no-index:
```

## sharepack.adapters

```{eval-rst}
.. automodule:: sharepack.adapters
   :members:

.. automodule:: sharepack.adapters.django
   :members: DjangoAdapter
```
