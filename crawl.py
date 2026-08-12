"""
광주광역시교육청 중등 기간제교사 인력풀(giganje.gen.go.kr) 채용공고 크롤러

동작:
1. 아래 TARGET_BOARDS에 정의된 게시판(공개 경쟁채용공고 / 인력풀등재자대상 경쟁채용공고)을
   각각 열어 표(과목·학교명·접수종료일·공고상태)를 파싱한다.
2. 결과를 data/postings.json 에 저장한다 (사이트가 읽는 파일).
3. 이전 실행 결과(data/postings.json)와 비교해서 "새로 생긴 공고"를 찾는다.
4. 새 공고 중 과목명에 SUBJECT_KEYWORDS(기본: 음악)가 포함된 것이 있으면
   notify.py 를 통해 이메일로 알린다.

주의:
- giganje.gen.go.kr 의 실제 HTML 마크업(태그 구조/클래스명)은 이 스크립트를 작성한
  시점에 실제 접속 없이 렌더링된 내용만 보고 추정한 것이라, 최초 1~2회 GitHub Actions
  실행 후 결과가 비어 있거나 이상하면 debug_dump.html 을 열어 표 구조를 확인하고
  parse_table() 의 선택자를 맞춰줘야 한다. (아래 parse_table 안에 상세 주석 있음)
"""
import json
import hashlib
import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://giganje.gen.go.kr"

# 크롤링 대상 게시판. 필요하면 여기 목록만 추가/수정하면 됨.
TARGET_BOARDS = [
    {
        "name": "공개 경쟁채용공고",
        "url": f"{BASE}/site/period/index.php?siteNo=05&s_SD_NEWDIV=04&m_code=in501010&m_sub=in501010",
    },
    {
        "name": "인력풀등재자대상 경쟁채용공고",
        "url": f"{BASE}/site/period/index.php?siteNo=05&s_SD_NEWDIV=02&m_code=in501010&m_sub=in501011",
    },
]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "postings.json"
DEBUG_FILE = DATA_DIR / "debug_dump.html"

SUBJECT_KEYWORDS = ["음악"]  # 알림을 받을 과목 키워드. 여러 개 넣으면 OR 조건.

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gwangju-edujob-watcher/1.0; +https://github.com/)"
}


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def parse_table(soup: BeautifulSoup, board_name: str) -> list[dict]:
    """
    표 구조: 실제 페이지에서 눈으로 확인된 컬럼은
    [과목, 학교명, 접수종료일, 공고상태] 4개.
    사이트가 <table> 하나로 렌더링되는 것으로 보이므로 우선 모든 table의
    tbody > tr 을 훑어서 td 4~5개짜리 행을 공고로 간주한다.

    만약 실제 배포 후 결과가 비면:
      1) data/debug_dump.html 을 로컬에서 열어 표의 실제 태그를 확인
      2) 아래 soup.select(...) 부분을 실제 클래스/구조에 맞게 수정
    """
    postings = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td"])]
            if len(cells) < 3:
                continue
            # 헤더 행(과목/학교명/...) 스킵
            if cells[0] in ("과목", "No", "번호"):
                continue

            subject = cells[0]
            school = cells[1] if len(cells) > 1 else ""
            deadline = cells[2] if len(cells) > 2 else ""
            status = cells[3] if len(cells) > 3 else ""

            # 상세 페이지 링크가 있으면 같이 저장 (없으면 게시판 URL로 대체)
            link_tag = row.find("a")
            link = BASE + link_tag["href"] if (link_tag and link_tag.get("href", "").startswith("/")) else (
                link_tag["href"] if link_tag and link_tag.get("href") else None
            )

            uid_src = f"{board_name}|{subject}|{school}|{deadline}"
            uid = hashlib.sha1(uid_src.encode("utf-8")).hexdigest()[:12]

            postings.append({
                "id": uid,
                "board": board_name,
                "subject": subject,
                "school": school,
                "deadline": deadline,
                "status": status,
                "link": link,
            })
    return postings


def load_previous() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"postings": []}


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    previous = load_previous()
    previous_ids = {p["id"] for p in previous.get("postings", [])}

    all_postings = []
    for board in TARGET_BOARDS:
        soup = fetch(board["url"])
        # 최초 실행 시 구조 확인용 디버그 덤프 (최근 1개 게시판만 저장해도 충분)
        DEBUG_FILE.write_text(str(soup), encoding="utf-8")
        all_postings.extend(parse_table(soup, board["name"]))

    new_postings = [p for p in all_postings if p["id"] not in previous_ids]

    result = {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "postings": all_postings,
    }
    DATA_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 새 공고 중 음악 과목만 골라 알림 큐에 기록
    alert_targets = [
        p for p in new_postings
        if any(kw in p["subject"] for kw in SUBJECT_KEYWORDS)
    ]
    alert_file = DATA_DIR / "new_alerts.json"
    alert_file.write_text(json.dumps(alert_targets, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"전체 공고 {len(all_postings)}건, 신규 {len(new_postings)}건, "
          f"음악 알림 대상 {len(alert_targets)}건")


if __name__ == "__main__":
    main()
