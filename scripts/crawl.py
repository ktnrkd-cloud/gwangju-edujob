"""
광주광역시교육청 중등 기간제교사 인력풀(giganje.gen.go.kr) 채용공고 크롤러

동작:
1. 아래 TARGET_BOARDS에 정의된 게시판(공개 경쟁채용공고 / 인력풀등재자대상 경쟁채용공고)을
   각각 열어 표(과목·학교명·접수종료일·공고상태)를 파싱한다.
2. 결과를 data/postings.json 에 저장한다 (사이트가 읽는 파일).
3. 이전 실행 결과(data/postings.json)와 비교해서 "새로 생긴 공고"를 찾는다.
4. 새 공고 중 과목명에 SUBJECT_KEYWORDS(기본: 음악)가 포함된 것이 있으면
   notify.py 를 통해 이메일로 알린다.
"""
import json
import hashlib
import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://giganje.gen.go.kr"

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

SUBJECT_KEYWORDS = ["음악"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gwangju-edujob-watcher/1.0; +https://github.com/)"
}


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def parse_table(soup: BeautifulSoup, board_name: str) -> list[dict]:
    postings = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td"])]
            if len(cells) < 3:
                continue
            if cells[0] in ("과목", "No", "번호"):
                continue

            subject = cells[0]
            school = cells[1] if len(cells) > 1 else ""
            deadline = cells[2] if len(cells) > 2 else ""
            status = cells[3] if len(cells) > 3 else ""

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
        DEBUG_FILE.write_text(str(soup), encoding="utf-8")
        all_postings.extend(parse_table(soup, board["name"]))

    new_postings = [p for p in all_postings if p["id"] not in previous_ids]

    result = {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "postings": all_postings,
    }
    DATA_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    alert_targets = [
        p for p in new_postings
        if any(kw in p["subject"] for kw in SUBJECT_KEYWORDS)
    ]
    alert_file = DATA_DIR / "new_alerts.json"
    alert_file.write_text(json.dumps(alert_targets, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"전체 공고 {len(all_postings)}건, 신규 {len(new_postings)}건, 음악 알림 대상 {len(alert_targets)}건")


if __name__ == "__main__":
    main()
