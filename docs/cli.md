# CLI reference

```text
sharepack PROJECT [-o OUT] [options]
```

## Arguments

`PROJECT`
: Project root directory. For Django, the directory containing `manage.py`.

## Options

`-o, --out PATH`
: Output HTML file. Default: `demo.html`.

`-q, --quiet`
: Suppress the build report.

`-V, --version`
: Print the sharepack version and exit.

`--open`
: Open the built file in your default browser after writing it.

`--dry-run`
: Print every file that would be bundled (with sizes), everything scrubbed,
  and every file skipped with the reason. Writes nothing.

`--include GLOB`
: Bundle files matching this glob even if their extension is not bundled by
  default. Matched against the file's path relative to the project root,
  e.g. `--include "data/*.csv"`. Repeatable.

`--exclude GLOB`
: Keep files matching this glob out of the bundle. Takes precedence over
  everything else. Repeatable.

`--settings-module DOTTED.PATH`
: Django settings module, for projects where detection from `manage.py`
  fails (custom `DJANGO_SETTINGS_MODULE` logic, split settings, etc.).

`--pyodide-version X.Y.Z`
: Pyodide release the artifact loads from the CDN at view time.

`--django-pin SPEC`
: pip requirement installed in the browser for the framework.
  Default: `django>=4.2,<5.2`.

## Exit status

`0` on success; `1` with a message on stderr when the project path is
invalid or no supported framework is detected.

## Examples

```bash
sharepack myproject -o demo.html --open
sharepack myproject --dry-run
sharepack myproject --include "data/*.csv" --exclude "notebooks/*"
sharepack myproject --settings-module config.settings.dev
sharepack myproject --django-pin "django==5.0.6"
```
