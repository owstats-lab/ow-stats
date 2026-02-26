"""
OWtics.GG 영웅 통계 스크래퍼 v6
- 티어 필터: <select> 드롭다운 제어 방식
- 영웅 이름: .font-medium div, 역할: .text-xs.text-mute div 분리 파싱
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://owtics.gg/ko-KR/hero"

REGIONS = ["아시아", "미국", "유럽", "중국"]
REGION_MAP = {"아시아": "ASIA", "미국": "US", "유럽": "EU", "중국": "CN"}

TIERS = ["ALL", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "GRANDMASTER"]
TIER_LABEL = {"ALL": "전체", "BRONZE": "브론즈", "SILVER": "실버", "GOLD": "골드",
              "PLATINUM": "플래티넘", "DIAMOND": "다이아몬드", "MASTER": "마스터",
              "GRANDMASTER": "그랜드마스터"}

def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=ko-KR")
    return webdriver.Chrome(options=opts)

def wait_table(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )
    time.sleep(0.8)

def get_tier_select(driver):
    """티어 select 요소 반환 (value="ALL" 옵션 포함한 select)"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        options = s.find_elements(By.TAG_NAME, "option")
        values = [o.get_attribute("value") for o in options]
        if "ALL" in values and "BRONZE" in values:
            return s
    return None

def get_region_buttons(driver):
    """지역 버튼 목록 반환"""
    buttons = driver.find_elements(By.CSS_SELECTOR, "button")
    region_btns = {}
    for btn in buttons:
        text = btn.text.strip()
        if text in REGIONS:
            region_btns[text] = btn
    return region_btns

def click_region(driver, region_name):
    btns = get_region_buttons(driver)
    if region_name in btns:
        btns[region_name].click()
        time.sleep(1.5)
        wait_table(driver)
        return True
    return False

def set_tier(driver, tier_value):
    sel = get_tier_select(driver)
    if sel is None:
        print("  [ERROR] 티어 select를 찾을 수 없음")
        return False
    s = Select(sel)
    s.select_by_value(tier_value)
    time.sleep(1.5)
    wait_table(driver)
    return True

def parse_table(driver):
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    data = []
    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 3:
            continue
        # 영웅명: .font-medium 클래스 div
        try:
            name_el = tds[0].find_element(By.CSS_SELECTOR, "div.font-medium")
            hero_name = name_el.text.strip()
        except:
            continue
        if not hero_name:
            continue
        # 역할: .text-xs.text-mute 클래스 div
        try:
            role_el = tds[0].find_element(By.CSS_SELECTOR, "div.text-xs.text-mute")
            role_text = role_el.text.strip()  # e.g. "지원 · 전술가"
        except:
            role_text = ""
        # 픽률
        pick_str = tds[1].text.strip().replace("%", "").replace("--", "")
        pick = float(pick_str) if pick_str else None
        # 승률
        win_str = tds[2].text.strip().replace("%", "").replace("--", "")
        win = float(win_str) if win_str else None

        data.append({
            "hero": hero_name,
            "role": role_text,
            "pick_rate": pick,
            "win_rate": win,
        })
    return data

def scrape():
    driver = make_driver(headless=True)
    driver.get(BASE_URL)
    wait_table(driver)
    # 경쟁전 버튼 클릭 (기본이 경쟁전이면 skip)
    try:
        comp_btn = driver.find_element(By.XPATH, "//button[text()='경쟁전']")
        comp_btn.click()
        time.sleep(1)
    except:
        pass

    all_records = []
    total = len(REGIONS) * len(TIERS)
    count = 0

    for region in REGIONS:
        print(f"\n[지역] {region}")
        ok = click_region(driver, region)
        if not ok:
            print(f"  지역 버튼 없음: {region}, skip")
            continue

        for tier in TIERS:
            count += 1
            print(f"  [{count}/{total}] {TIER_LABEL[tier]}", end=" ... ")
            ok = set_tier(driver, tier)
            if not ok:
                print("SKIP")
                continue
            rows = parse_table(driver)
            print(f"{len(rows)}명")
            for r in rows:
                all_records.append({
                    "region": REGION_MAP[region],
                    "tier": tier,
                    **r,
                })

    driver.quit()
    return all_records

def main():
    print("=== OWtics 스크래퍼 v6 시작 ===")
    records = scrape()
    print(f"\n총 수집: {len(records)}행")

    if not records:
        print("데이터 없음. 종료.")
        return

    df = pd.DataFrame(records)
    out = "ow_hero_stats_v6.xlsx"
    df.to_excel(out, index=False)
    print(f"저장: {out}")
    print(df.head(10).to_string())

if __name__ == "__main__":
    main()
