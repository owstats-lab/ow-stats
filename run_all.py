"""
run_all.py - OWtics 전체 파이프라인 실행기
실행 순서:
  1. ow_stats_scraper_v6.py   → ow_hero_stats_v6.xlsx
  2. ow_map_scraper.py        → ow_hero_map_stats.csv
  3. generate_html.py         → index.html
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def run_step(label: str, script: str) -> bool:
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {label}")
    print(f"{'='*50}")

    if not Path(script).exists():
        print(f"[SKIP] {script} 파일 없음")
        return False

    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        capture_output=False,  # 실시간 출력
        text=True,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n[ERROR] {script} 실패 (종료코드 {result.returncode})")
        return False

    print(f"\n✓ 완료 ({elapsed:.0f}초)")
    return True


def main():
    start_all = time.time()
    print(f"\n{'#'*50}")
    print(f"  OWtics 자동화 파이프라인")
    print(f"  시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*50}")

    results = {}

    # 스크래퍼 실행 (순서대로, 오류가 나도 다음 단계 진행)
    results["stats"] = run_step("영웅 통계 스크래핑", "ow_stats_scraper_v6.py")
    results["maps"] = run_step("맵 통계 스크래핑", "ow_map_scraper.py")
    results["html"] = run_step("HTML 대시보드 생성", "generate_html.py")

    # 결과 요약
    elapsed_all = time.time() - start_all
    print(f"\n{'='*50}")
    print(f"  파이프라인 완료 ({elapsed_all:.0f}초)")
    for step, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"  {icon} {step}")
    print(f"{'='*50}\n")

    if results["html"]:
        print("→ index.html 이 업데이트되었습니다.")
        html_path = Path("index.html").resolve()
        print(f"  경로: {html_path}")


if __name__ == "__main__":
    main()
