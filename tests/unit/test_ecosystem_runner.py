# SPDX-License-Identifier: MIT
# Copyright (c) 2026 EoS Project

"""The ecosystem runner must find every product and never invent a pass.

Two defects motivate this file:

1. find_repos held a hardcoded list of seven lowercase names
   ("eai", "eni", "eipc", "eboot", "ebuild-tool"). None of those match the
   real directory names on a case-sensitive filesystem, so it discovered
   2 of the 19 repos in the workspace and run_ecosystem_tests silently
   `continue`d past anything not on the list.

2. test_c_repo ended with

       tests_passed = max(tests_passed, tests_run if build_ok else 0)
       tests_failed = max(0, tests_run - tests_passed)
       passed = build_ok and tests_failed == 0

   where tests_run was a count of executables on disk. Any repo that
   compiled reported every test passing and a verdict of PASS, whether or
   not a single test had run.
"""

import os

import pytest

from eosim.integrations import ecosystem as eco
from eosim.integrations.ecosystem import (
    DEPS, ERROR, FAIL, PASS, SKIP,
    EcosystemReport, RepoTestResult,
    _parse_ctest, _parse_pytest,
    detect_kind, detect_kinds, find_repos,
    test_repo as run_one_repo,
)


def _repo(tmp_path, name, *files):
    d = tmp_path / name
    (d / ".git").mkdir(parents=True)
    for f in files:
        (d / f).write_text("", encoding="utf-8")
    return d


class TestDiscovery:
    def test_finds_every_git_directory(self, tmp_path):
        for n in ("eos", "eAI", "eNI", "eIPC", "eBoot", "ebuild", "EoStudio"):
            _repo(tmp_path, n)
        assert set(find_repos(str(tmp_path))) == {
            "eos", "eAI", "eNI", "eIPC", "eBoot", "ebuild", "EoStudio"}

    def test_casing_is_not_assumed(self, tmp_path):
        """The old list looked for 'eai'; the directory is 'eAI'."""
        _repo(tmp_path, "eAI")
        assert "eAI" in find_repos(str(tmp_path))

    def test_non_repo_directories_are_ignored(self, tmp_path):
        _repo(tmp_path, "eos")
        (tmp_path / "scratch").mkdir()
        (tmp_path / "docs").mkdir()
        assert set(find_repos(str(tmp_path))) == {"eos"}

    def test_dot_github_is_not_a_product(self, tmp_path):
        _repo(tmp_path, ".github")
        _repo(tmp_path, "eos")
        assert set(find_repos(str(tmp_path))) == {"eos"}

    def test_missing_workspace_is_empty_not_an_error(self):
        assert find_repos("/nonexistent/path") == {}


class TestKindDetection:
    @pytest.mark.parametrize("marker,kind", [
        ("CMakeLists.txt", "cmake"),
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("go.mod", "go"),
        ("Cargo.toml", "cargo"),
        ("package.json", "node"),
        ("Makefile", "make"),
    ])
    def test_detects_from_files_present(self, tmp_path, marker, kind):
        d = _repo(tmp_path, "r", marker)
        assert detect_kind(str(d)) == kind

    def test_cmake_wins_over_a_wrapper_makefile(self, tmp_path):
        """A CMake project often ships a convenience Makefile; ctest is the
        runner that knows about its tests."""
        d = _repo(tmp_path, "r", "CMakeLists.txt", "Makefile")
        assert detect_kind(str(d)) == "cmake"

    def test_unknown_when_nothing_is_recognised(self, tmp_path):
        assert detect_kind(str(_repo(tmp_path, "r"))) == "unknown"


class TestNoFabricatedPasses:
    """Nothing may report PASS unless a suite ran and reported no failures."""

    def test_unknown_project_is_skipped_not_passed(self, tmp_path):
        d = _repo(tmp_path, "mystery")
        r = run_one_repo("mystery", str(d))
        assert r.status == SKIP
        assert r.passed is False

    def test_python_repo_without_tests_is_skipped_not_passed(self, tmp_path):
        d = _repo(tmp_path, "p", "pyproject.toml")
        r = run_one_repo("p", str(d))
        assert r.status == SKIP
        assert r.passed is False
        assert "no tests" in r.reason

    def test_missing_toolchain_is_skipped_not_passed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(eco.shutil, "which", lambda _n: None)
        d = _repo(tmp_path, "g", "go.mod")
        r = run_one_repo("g", str(d))
        assert r.status == SKIP
        assert r.passed is False

    def test_passed_is_derived_from_status_only(self):
        """The old code could set build_ok and a pass count independently of
        whether anything ran; `passed` now has one source of truth."""
        r = RepoTestResult(repo="x", build_ok=True, tests_run=99, tests_passed=99)
        assert r.passed is False          # status is still the default SKIP
        r.status = PASS
        assert r.passed is True


class TestResultParsing:
    def test_ctest_summary_is_read_not_guessed(self):
        out = "100% tests passed, 0 tests failed out of 24"
        assert _parse_ctest(out) == (24, 0, 24)

    def test_ctest_failures_are_counted(self):
        out = "91% tests passed, 2 tests failed out of 23"
        assert _parse_ctest(out) == (21, 2, 23)

    def test_ctest_without_a_summary_is_not_a_pass(self):
        assert _parse_ctest("ninja: no work to do") is None

    def test_pytest_counts_are_read(self):
        assert _parse_pytest("288 passed in 2.21s") == (288, 0, 0)

    def test_failures_and_errors_are_kept_apart(self):
        """A broken assertion and an uninstalled dependency are different
        problems, and only one of them is the repo's fault."""
        assert _parse_pytest("3 failed, 256 passed, 1 error in 2.3s") == (256, 3, 1)

    def test_pytest_collection_error_is_counted(self):
        """An uncollectable suite must never read as zero problems."""
        assert _parse_pytest(
            "!!! Interrupted: 1 error during collection !!!") == (0, 0, 1)

    def test_pytest_silence_yields_no_counts(self):
        """A crash with no summary at all is handled by the caller, which
        turns it into SKIP or FAIL based on the exit code -- never a pass."""
        assert _parse_pytest("Segmentation fault") is None


class TestMultipleBuildSystems:
    """A repo with two build systems must have both exercised: ebuild is a
    Python CLI whose CMakeLists integrates sibling repos, and a broken CMake
    build there stayed invisible behind a green Python suite."""

    def test_both_are_detected(self, tmp_path):
        d = _repo(tmp_path, "ebuild", "CMakeLists.txt", "pyproject.toml")
        assert detect_kinds(str(d)) == ["cmake", "python"]

    def test_primary_kind_is_the_first(self, tmp_path):
        d = _repo(tmp_path, "ebuild", "CMakeLists.txt", "pyproject.toml")
        assert detect_kind(str(d)) == "cmake"

    def test_a_make_wrapper_is_not_a_second_system(self, tmp_path):
        """Makefile is only a fallback; a CMake project's Makefile is a
        convenience wrapper, not a separate suite to run."""
        d = _repo(tmp_path, "r", "CMakeLists.txt", "Makefile")
        assert detect_kinds(str(d)) == ["cmake"]


class TestDependencyGapsAreNotFailures:
    def test_missing_modules_are_extracted(self, tmp_path):
        from eosim.integrations.ecosystem import _missing_modules
        out = ("ModuleNotFoundError: No module named 'fastapi'\n"
               "ModuleNotFoundError: No module named 'fastapi.routing'\n"
               "ModuleNotFoundError: No module named 'httpx'\n")
        assert _missing_modules(out) == ["fastapi", "httpx"]

    def test_deps_is_not_a_pass(self):
        r = RepoTestResult(repo="eDB", status=DEPS, tests_passed=23)
        assert r.passed is False

    def test_deps_repos_are_not_counted_as_passed(self):
        rep = EcosystemReport(repos_tested=1, repos_skipped=1)
        assert "NOTHING WAS TESTED" in rep.summary()


class TestReportVerdict:
    def test_all_skipped_does_not_read_as_success(self):
        rep = EcosystemReport(repos_tested=3, repos_skipped=3)
        assert "NOTHING WAS TESTED" in rep.summary()

    def test_skips_are_surfaced_alongside_passes(self):
        rep = EcosystemReport(repos_tested=3, repos_passed=2, repos_skipped=1)
        assert "1 repo(s) skipped" in rep.summary()

    def test_any_failure_dominates(self):
        rep = EcosystemReport(repos_tested=3, repos_passed=2, repos_failed=1)
        assert "FAILURES DETECTED" in rep.summary()

    def test_clean_run_says_so(self):
        rep = EcosystemReport(repos_tested=2, repos_passed=2)
        assert "ALL PASSED" in rep.summary()

    def test_failures_are_listed_first(self):
        rep = EcosystemReport(results=[
            RepoTestResult(repo="aaa", status=PASS),
            RepoTestResult(repo="zzz", status=FAIL),
        ])
        body = rep.summary()
        assert body.index("zzz") < body.index("aaa")
