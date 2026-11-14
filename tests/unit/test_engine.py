from scanner import scan_directory
from scanner.rules import ALL_RULES
from scanner.sitf import SITF_MAP, PILLARS


def test_at_least_ten_rules_and_every_rule_is_mapped_to_sitf():
    codes = {r.code for r in ALL_RULES} | {"EP-001"}
    assert len(codes) >= 10
    assert codes <= set(SITF_MAP)
    assert {pillar for pillar, _ in SITF_MAP.values()} == set(PILLARS)  # all 5 pillars covered


def test_scan_directory_finds_issues_with_relative_paths(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "settings.py").write_text('consumer_secret = "abc123XYZ789secretKEY"\nDEBUG = True\n')
    findings = scan_directory(str(tmp_path))
    by_code = {f.rule_code: f for f in findings}
    assert by_code["VCS-001"].file_path == "app/settings.py"
    assert by_code["PROD-001"].line_number == 2


def test_env_not_ignored_is_flagged(tmp_path):
    (tmp_path / ".env").write_text("TOKEN=abc\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    codes = [f.rule_code for f in scan_directory(str(tmp_path))]
    assert "EP-001" in codes


def test_env_ignored_is_not_flagged(tmp_path):
    (tmp_path / ".env").write_text("TOKEN=abc\n")
    (tmp_path / ".gitignore").write_text("# secrets\n.env\n")
    codes = [f.rule_code for f in scan_directory(str(tmp_path))]
    assert "EP-001" not in codes


def test_git_folder_and_binary_files_are_skipped(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.py").write_text('consumer_secret = "abc123XYZ789secretKEY"\n')
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\x00\x00consumer_secret")
    assert scan_directory(str(tmp_path)) == []
