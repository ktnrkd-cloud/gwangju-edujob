# 광주·전남 기간제 인력풀 채용공고 모음

- **광주**: `giganje.gen.go.kr` 공고를 매일 자동 수집해서 웹사이트에 표시하고,
  **음악 과목 신규 공고**는 이메일로 알려줍니다.
- **전남**: robots.txt가 자동 접근을 막고 있어 자동 수집하지 않고,
  사이트 하단에 관련 게시판 바로가기 링크만 정리해뒀습니다.

## 처음 설정하는 방법 (한 번만)

### 1. GitHub 저장소 만들기
1. github.com 에서 새 저장소 생성 (예: `gwangju-edujob`, Public)
2. 이 폴더의 파일들을 그대로 그 저장소에 업로드 (GitHub 웹의 "Add file → Upload files" 로도 가능)

### 2. GitHub Pages 켜기
1. 저장소 → Settings → Pages
2. Source: `Deploy from a branch` / Branch: `main`, 폴더는 `/ (root)` 선택
3. 저장하면 몇 분 뒤 `https://<본인아이디>.github.io/<저장소이름>/` 로 사이트가 열립니다.

### 3. 이메일 알림용 비밀정보 등록
Gmail 기준입니다 (다른 메일도 SMTP 설정만 바꾸면 되지만 여기선 Gmail 기준으로 작성).

1. 구글 계정에서 **2단계 인증**을 켠다 (이미 켜져 있으면 생략)
2. https://myaccount.google.com/apppasswords 에서 **앱 비밀번호**를 발급 (16자리, 일반 로그인 비밀번호와 다름)
3. 저장소 → Settings → Secrets and variables → Actions → **New repository secret** 으로 아래 3개 등록
   - `GMAIL_ADDRESS` : 보내는 사람 gmail 주소
   - `GMAIL_APP_PASSWORD` : 위에서 발급받은 16자리 앱 비밀번호
   - `ALERT_TO_EMAIL` : 알림 받을 이메일 주소 (본인 메일이면 위와 동일하게 입력해도 됨)

### 4. 첫 실행
- 저장소 → Actions 탭 → `crawl-and-notify` 워크플로 → **Run workflow** 버튼으로 수동 실행
- 이후로는 하루 3번(한국시간 08시/13시/18시) 자동 실행됩니다. `.github/workflows/crawl.yml` 의
  `cron` 값을 바꾸면 주기를 조절할 수 있습니다.

## 첫 실행 후 확인할 것
- `data/postings.json` 에 공고가 잘 들어왔는지 확인
- 만약 비어 있거나 이상하면 `data/debug_dump.html` (해당 커밋에 같이 올라감)을 열어서
  실제 표 구조를 보고 `scripts/crawl.py` 의 `parse_table()` 부분을 그 구조에 맞게 조정해야 합니다.
  (제가 이 코드를 만들 때는 실제 실행 접속 없이 화면에 보이는 내용만 보고 작성해서,
  최초 1회는 확인이 필요합니다 — 문제 있으면 debug_dump.html을 캡처해서 알려주시면 바로 고쳐드릴게요.)

## 알림 대상 과목 바꾸기
`scripts/crawl.py` 의 `SUBJECT_KEYWORDS = ["음악"]` 부분에 과목명을 추가하면 됩니다.
예: `SUBJECT_KEYWORDS = ["음악", "체육"]`
