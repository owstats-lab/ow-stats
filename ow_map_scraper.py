"""
OWtics.GG 영웅별 맵 통계 스크래퍼
- 수집 데이터: region, hero, map_name, map_type, win_rate, pick_rate
- 지역: 아시아 / 미국 / 유럽
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://owtics.gg/ko-KR/hero"
REGIONS = ["아시아", "미국", "유럽"]
REGION_MAP = {"아시아": "ASIA", "미국": "US", "유럽": "EU"}


def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=ko-KR")
    return webdriver.Chrome(options=opts)


def get_hero_slugs(driver):
    """영웅 목록 페이지에서 모든 영웅 slug 수집"""
    driver.get(BASE_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )
    time.sleep(1)

    slugs = []
    # 영웅 링크에서 slug 추출: /ko-KR/hero/{slug}
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/hero/']")
    for link in links:
        href = link.get_attribute("href") or ""
        parts = href.rstrip("/").split("/hero/")
        if len(parts) == 2 and parts[1] and parts[1] != "":
            slug = parts[1]
            if slug not in slugs and not slug.startswith("http"):
                slugs.append(slug)

    print(f"  영웅 {len(slugs)}개 발견: {slugs[:5]}...")
    return slugs


def click_region(driver, region_name):
    """지역 버튼 클릭 (맵 통계 섹션 내 버튼)"""
    # 맵 통계 섹션의 지역 버튼만 클릭 (첫 번째 지역 버튼 그룹)
    btns = driver.find_elements(By.CSS_SELECTOR, "button")
    for btn in btns:
        if btn.text.strip() == region_name:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5)
            return True
    return False


def expand_map_table(driver):
    """'+N개 맵 더 보기' 버튼 클릭해서 전체 맵 표시"""
    try:
        more_btn = driver.find_element(
            By.XPATH, "//button[contains(., '맵 더 보기')]"
        )
        driver.execute_script("arguments[0].click();", more_btn)
        time.sleep(1)
    except Exception:
        pass  # 버튼 없으면 이미 전체 표시 중


def parse_map_table(driver):
    """맵 테이블 파싱"""
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    data = []
    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if not tds:
            continue
        # 더보기 버튼 행 스킵
        if len(tds) == 1:
            continue
        try:
            # 맵 이름
            map_name = tds[0].find_element(
                By.CSS_SELECTOR, "span.truncate"
            ).text.strip()
            if not map_name:
                continue
            # 맵 타입 (두 번째 span.text-mute)
            mute_spans = tds[0].find_elements(By.CSS_SELECTOR, "span.text-mute")
            map_type = mute_spans[-1].text.strip() if mute_spans else ""

            # 승률 (font-bold)
            win_el = row.find_elements(By.CSS_SELECTOR, "span.font-bold.tabular-nums")
            win_rate = float(win_el[0].text.replace("%", "")) if win_el else None

            # 픽률 (text-xs.text-mute.tabular-nums)
            pick_els = row.find_elements(
                By.CSS_SELECTOR, "td span.text-xs.text-mute.tabular-nums"
            )
            pick_rate = float(pick_els[0].text.replace("%", "")) if pick_els else None

            data.append({
                "map_name": map_name,
                "map_type": map_type,
                "win_rate": win_rate,
                "pick_rate": pick_rate,
            })
        except Exception:
            continue
    return data


def scrape_hero_maps(driver, slug):
    """영웅 개별 페이지에서 지역별 맵 통계 수집"""
    url = f"{BASE_URL}/{slug}"
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(1)
    except Exception:
        print(f"    [SKIP] {slug} - 테이블 로딩 실패")
        return []

    records = []
    for region in REGIONS:
        # 지역 클릭
        click_region(driver, region)
        # 더보기 버튼 클릭
        expand_map_table(driver)
        # 파싱
        rows = parse_map_table(driver)
        for r in rows:
            records.append({
                "region": REGION_MAP[region],
                "hero": slug,
                **r,
            })
        print(f"    {region}: {len(rows)}개 맵")

    return records


def main():
    print("=== OWtics 영웅별 맵 통계 스크래퍼 시작 ===")
    driver = make_driver(headless=True)

    # 1. 영웅 slug 목록 수집
    print("\n[1] 영웅 목록 수집 중...")
    slugs = get_hero_slugs(driver)

    if not slugs:
        print("영웅 목록 수집 실패. 종료.")
        driver.quit()
        return

    # 2. 각 영웅 맵 통계 수집
    all_records = []
    total = len(slugs)
    for i, slug in enumerate(slugs, 1):
        print(f"\n[{i}/{total}] {slug}")
        records = scrape_hero_maps(driver, slug)
        all_records.extend(records)
        print(f"  → 누적 {len(all_records)}행")

    driver.quit()

    # 3. 저장
    print(f"\n총 수집: {len(all_records)}행")
    if not all_records:
        print("데이터 없음.")
        return

    df = pd.DataFrame(all_records)
    out = "ow_hero_map_stats.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"저장: {out}")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()
