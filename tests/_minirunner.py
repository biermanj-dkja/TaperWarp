"""Minimal offline fallback runner for the TaperWarp test suite.

The canonical way to run tests is ``pytest``. This runner exists so the suite
can be executed in fully offline environments where pytest cannot be
installed (the project must remain functional without Internet access). It
implements just the subset of the pytest API used by this suite:
``pytest.raises`` (with ``match``), ``pytest.approx``,
``pytest.mark.parametrize``, and the ``tmp_path`` fixture.

Usage::

    python tests/_minirunner.py
"""

from __future__ import annotations

import inspect
import re
import sys
import tempfile
import traceback
import types
from contextlib import contextmanager
from pathlib import Path


def _install_pytest_shim() -> None:
    if "pytest" in sys.modules:
        return
    shim = types.ModuleType("pytest")

    @contextmanager
    def raises(exc_type, match: str | None = None):
        class Holder:
            value: BaseException | None = None

        holder = Holder()
        try:
            yield holder
        except exc_type as exc:
            holder.value = exc
            if match is not None and not re.search(match, str(exc)):
                raise AssertionError(
                    f"exception message {str(exc)!r} does not match {match!r}"
                ) from exc
        else:
            raise AssertionError(f"expected {exc_type.__name__} to be raised")

    class _Approx:
        def __init__(self, expected: float, rel: float = 1e-6, abs: float = 1e-12):
            self.expected, self.rel, self.abs = expected, rel, abs

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, (int, float)):
                return NotImplemented
            tol = max(self.rel * abs(self.expected), self.abs)
            return abs(other - self.expected) <= tol

    def approx(expected: float, rel: float = 1e-6, abs: float = 1e-12) -> _Approx:
        return _Approx(expected, rel, abs)

    class _Mark:
        @staticmethod
        def parametrize(argnames: str, argvalues):
            names = [n.strip() for n in argnames.split(",")]

            def deco(fn):
                fn._parametrize = (names, list(argvalues))
                return fn

            return deco

    shim.raises = raises  # type: ignore[attr-defined]
    shim.approx = approx  # type: ignore[attr-defined]
    shim.mark = _Mark()  # type: ignore[attr-defined]
    sys.modules["pytest"] = shim


def _iter_tests(module):
    for name, obj in list(vars(module).items()):
        if name.startswith("test_") and callable(obj):
            yield name, None, obj
        elif name.startswith("Test") and inspect.isclass(obj):
            for mname, method in vars(obj).items():
                if mname.startswith("test_") and callable(method):
                    yield f"{name}.{mname}", obj, method


def _call(fn, instance, params):
    sig = inspect.signature(fn)
    kwargs = dict(params)
    if "tmp_path" in sig.parameters:
        with tempfile.TemporaryDirectory() as td:
            kwargs["tmp_path"] = Path(td)
            fn(instance, **kwargs) if instance else fn(**kwargs)
        return
    fn(instance, **kwargs) if instance else fn(**kwargs)


def main() -> int:
    _install_pytest_shim()
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir.parent / "src"))
    sys.path.insert(0, str(tests_dir))

    passed = failed = 0
    failures: list[str] = []
    for test_file in sorted(tests_dir.glob("test_*.py")):
        module = __import__(test_file.stem)
        for name, cls, fn in _iter_tests(module):
            raw = fn.__func__ if isinstance(fn, staticmethod) else fn
            param_spec = getattr(raw, "_parametrize", None)
            variants = (
                [dict(zip(param_spec[0], vals if isinstance(vals, tuple) else (vals,)))
                 for vals in param_spec[1]]
                if param_spec
                else [{}]
            )
            for params in variants:
                label = f"{test_file.stem}::{name}"
                if params:
                    label += f"[{params}]"
                instance = cls() if cls else None
                try:
                    _call(raw, instance, params)
                    passed += 1
                except Exception:
                    failed += 1
                    failures.append(f"{label}\n{traceback.format_exc()}")

    for f in failures:
        print("FAILED:", f, file=sys.stderr)
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
