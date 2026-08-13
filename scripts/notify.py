"""
data/new_alerts.json 에 담긴 '음악 과목 신규 공고'를 이메일로 발송한다.
crawl.py 실행 직후에 이어서 실행된다.

필요한 환경변수(GitHub Actions Secrets로 등록):
  GMAIL_ADDRESS      : 보내는 사람 gmail 주소 (예: xxx@gmail.com)
  GMAIL_APP_PASSWORD : 구글 앱 비밀번호 (일반 로그인 비밀번호 아님, 16자리)
  ALERT_TO_EMAIL     : 알림 받을 이메일 주소 (본인 메일이면 GMAIL_ADDRESS와 같아도 됨)

알림 대상이 없으면 아무것도 하지 않고 조용히 종료한다.
"""
import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALERT_FILE = DATA_DIR / "new_alerts.json"


def build_body(alerts: list[dict]) -> str:
    lines = ["새로 올라온 음악 과목 기간제 채용 공고입니다.\n"]
    for a in alerts:
        lines.append(f"- [{a['board']}] {a['school']}  (접수마감: {a['deadline']}, 상태: {a['status']})")
        if a.get("link"):
            lines.append(f"  바로가기: {a['link']}")
    lines.append("\n※ 자동 수집 결과이므로 지원 전 반드시 원문 공고에서 마감일/제출서류를 확인하세요.")
    return "\n".join(lines)


def main():
    if not ALERT_FILE.exists():
        print("알림 파일이 없습니다. 종료.")
        return

    alerts = json.loads(ALERT_FILE.read_text(encoding="utf-8"))
    if not alerts:
        print("신규 음악 공고 없음. 이메일 발송 안 함.")
        return

    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_email = os.environ.get("ALERT_TO_EMAIL", gmail_address)

    msg = MIMEText(build_body(alerts))
    msg["Subject"] = f"[광주 기간제 인력풀] 음악 신규 공고 {len(alerts)}건"
    msg["From"] = gmail_address
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [to_email], msg.as_string())

    print(f"이메일 발송 완료: {len(alerts)}건")


if __name__ == "__main__":
    main()
