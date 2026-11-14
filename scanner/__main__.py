"""Quick manual check from the terminal:  python -m scanner path/to/folder"""
import sys

from scanner import calculate_risk_score, count_by_severity, scan_directory


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m scanner <folder>")
        return 1
    findings = scan_directory(sys.argv[1])
    for f in findings:
        print(f"[{f.severity:<8}] {f.rule_code:<8} {f.pillar:<15} "
              f"{f.file_path}:{f.line_number}  {f.masked_evidence}")
    print(f"\n{len(findings)} finding(s)  |  by severity: {count_by_severity(findings)}")
    print(f"Risk score: {calculate_risk_score(findings)}/100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
