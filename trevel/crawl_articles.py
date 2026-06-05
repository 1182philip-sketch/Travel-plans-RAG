"""
한국관광공사 경기도 여행기사 크롤러
실행: python crawl_articles.py
결과: gyeonggi_articles.txt (RAG에 넣을 텍스트 파일)
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os

# ── 설정 ──────────────────────────────────────
CSV_FILE = "data/한국관광공사_여행기사목록_20251107.csv"
OUTPUT_FILE = "data/gyeonggi_articles.txt"
DELAY = 1.5  # 요청 간격 (초) - 너무 빠르면 차단됨

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://korean.visitkorea.or.kr",
}

# 본문 추출 시도할 CSS 선택자 목록
CONTENT_SELECTORS = [
    ".detail_view_cont",
    ".view_cont",
    ".article_body",
    ".cont_view",
    "#content",
    ".detail_content",
    "article",
    ".view_content",
    ".story_view",
    ".board_view",
]

# ── 함수 ──────────────────────────────────────
def fetch_article(url, title, category, region):
    """기사 URL에서 본문 텍스트 추출"""
    try:
        session = requests.Session()
        res = session.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        res.encoding = "utf-8"

        soup = BeautifulSoup(res.text, "html.parser")

        # 불필요한 태그 제거
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 본문 탐색
        body_text = ""
        for selector in CONTENT_SELECTORS:
            found = soup.select(selector)
            if found:
                body_text = found[0].get_text(separator="\n", strip=True)
                if len(body_text) > 200:  # 200자 이상이면 본문으로 인정
                    break

        # 선택자로 못 찾으면 전체 body에서 추출
        if len(body_text) < 200:
            body = soup.find("body")
            if body:
                body_text = body.get_text(separator="\n", strip=True)

        # 너무 짧으면 실패 처리
        if len(body_text) < 100:
            return None

        # 정리: 빈 줄 압축
        lines = [l.strip() for l in body_text.splitlines() if l.strip()]
        clean_text = "\n".join(lines)

        return clean_text[:3000]  # 최대 3000자

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return None


def main():
    # CSV 로드
    try:
        df = pd.read_csv(CSV_FILE, encoding="euc-kr")
    except:
        df = pd.read_csv(CSV_FILE, encoding="cp949")

    # 경기도 필터링
    gg = df[df["지역명"] == "경기도"].reset_index(drop=True)
    print(f"✅ 경기도 기사 총 {len(gg)}건 크롤링 시작\n")

    results = []
    success, fail = 0, 0

    for i, row in gg.iterrows():
        title = row["콘텐츠명"]
        category = row["콘텐츠분류명"] if pd.notna(row["콘텐츠분류명"]) else "기타"
        region = row["시군구명"] if pd.notna(row["시군구명"]) else "경기도"
        url = row["기사상세정보URL"]

        print(f"[{i+1}/{len(gg)}] {title[:30]}...")

        body = fetch_article(url, title, category, region)

        if body:
            # RAG에 넣기 좋은 형식으로 구성
            article_text = f"""
[여행기사]
제목: {title}
분류: {category}
지역: 경기도 {region}
출처: {url}

{body}

{'='*60}
"""
            results.append(article_text)
            success += 1
            print(f"  ✅ 성공 ({len(body)}자)")
        else:
            # 본문 크롤링 실패 시 제목만이라도 저장
            article_text = f"""
[여행기사]
제목: {title}
분류: {category}
지역: 경기도 {region}
출처: {url}
내용: 본문을 가져오지 못했습니다. 위 URL에서 직접 확인하세요.

{'='*60}
"""
            results.append(article_text)
            fail += 1
            print(f"  ⚠️  본문 추출 실패 (제목만 저장)")

        time.sleep(DELAY)

    # 파일 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# 한국관광공사 경기도 여행기사 모음\n")
        f.write(f"# 총 {len(results)}건 (성공: {success}, 실패: {fail})\n\n")
        f.writelines(results)

    print(f"\n🎉 완료! 저장 위치: {OUTPUT_FILE}")
    print(f"   성공: {success}건 / 실패: {fail}건")
    print(f"\n다음 단계: gyeonggi_articles.txt 를 여행가이드.pdf 와 함께 RAG에 넣으면 됩니다!")


if __name__ == "__main__":
    main()
