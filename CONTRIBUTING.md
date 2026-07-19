# Contributing to TaperWarp

Thanks for helping! Please read `PROJECT_GUIDELINES.md` (binding engineering
guidelines) and `docs/developer_guide.md` (workflow) before opening a PR.

The short version:

- The geometry engine comes first and must stay analytically correct;
  `docs/math.md` is the source of truth for every formula.
- No heuristic warping, no network access, no unapproved dependencies.
- Add tests with every change; CI (Ruff, Black, mypy, pytest on
  Linux/Windows/macOS) must pass before merge.
- Use Conventional Commits and the pull request template.

By contributing you agree your work is licensed under the MIT License.
