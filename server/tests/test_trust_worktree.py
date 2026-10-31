import subprocess

from trellis_mcp.trust import trust_roots


def _git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.invalid", *args], cwd=cwd, check=True, capture_output=True)


def test_linked_worktree_also_trusts_main_checkout(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    _git("init", "-q", cwd=main)
    _git("commit", "-q", "--allow-empty", "-m", "i", cwd=main)
    _git("worktree", "add", "-q", str(tmp_path / "linked"), cwd=main)
    roots = trust_roots(tmp_path / "linked")
    assert (tmp_path / "linked").resolve() in roots
    assert main.resolve() in roots


def test_normal_checkout_trusts_only_itself(tmp_path):
    _git("init", "-q", cwd=tmp_path)
    assert trust_roots(tmp_path) == [tmp_path.resolve()]
