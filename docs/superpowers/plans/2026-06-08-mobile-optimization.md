# Mobile Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `web/index.html` 한 파일만 수정해 스마트폰에서 지도 전체화면 + 바텀 시트 패널 + 별점 탭 선택을 동작하게 만든다.

**Architecture:** 기존 2칸 그리드(지도+패널)는 880px 초과에서 그대로 유지. 880px 이하에서는 CSS로 지도를 전체화면으로 키우고, `.panel`을 `position: fixed` 바텀 시트로 전환한다. JS는 `isMobile()` 헬퍼로 모바일 전용 클래스(`collapsed` / `expanded`)를 제어한다.

**Tech Stack:** 순수 HTML/CSS/JS (프레임워크 없음), 기존 `web/index.html` 수정만.

---

## 파일 구조

- Modify: `outlet_map/web/index.html` — CSS `<style>`, HTML `<aside>` + `<form>`, `<script>` 세 곳
- Modify: `outlet_map/tests/test_web_assets.py` — HTML 구조 검증 테스트 추가

---

## Task 1: HTML 구조 추가 (시트 핸들 + 별점 버튼)

**Files:**
- Modify: `outlet_map/web/index.html`

- [ ] **Step 1: `<aside class="panel">` 맨 위에 시트 핸들 div 추가**

`<aside class="panel">` 바로 다음 줄에 추가:
```html
<aside class="panel">
  <div class="sheet-handle"></div>
  <div id="summary"></div>
```

- [ ] **Step 2: 별점 select 아래에 모바일 별점 버튼 행 추가**

기존 코드:
```html
      <label>별점</label>
      <div class="row">
        <select id="rating">
          <option>1</option><option>2</option><option>3</option>
          <option>4</option><option selected>5</option>
        </select>
        <span class="meta">1~5</span>
      </div>
```

교체 후:
```html
      <label>별점</label>
      <div class="row">
        <select id="rating">
          <option>1</option><option>2</option><option>3</option>
          <option>4</option><option selected>5</option>
        </select>
        <span class="meta">1~5</span>
      </div>
      <div id="starRating" class="star-row">
        <button type="button" class="star-btn" data-val="1">★</button>
        <button type="button" class="star-btn" data-val="2">★</button>
        <button type="button" class="star-btn" data-val="3">★</button>
        <button type="button" class="star-btn" data-val="4">★</button>
        <button type="button" class="star-btn" data-val="5">★</button>
      </div>
```

- [ ] **Step 3: 테스트 작성 (HTML 구조 검증)**

`outlet_map/tests/test_web_assets.py` 파일 끝(`_run()` 함수 위)에 추가:
```python
def test_mobile_html_structure():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "web", "index.html")
    html = open(html_path, encoding="utf-8").read()
    assert 'class="sheet-handle"' in html, "시트 핸들 div 없음"
    assert 'id="starRating"' in html, "별점 버튼 컨테이너 없음"
    assert 'class="star-btn"' in html, "별점 버튼 없음"
    assert 'data-val="5"' in html, "별점 5 버튼 없음"
```

그리고 `_run()` 함수에서 호출:
```python
def _run():
    passed = 0
    test_mobile_html_structure()
    passed += 1
    print("  ok  test_mobile_html_structure")
    test_image_content_type_matches_extension()
    passed += 1
    print("  ok  test_image_content_type_matches_extension")
    print(f"\n{passed}개 테스트 통과 ...")
```

- [ ] **Step 4: 테스트 실행 — 구조 테스트 통과 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 tests/test_web_assets.py
```

예상 출력:
```
  ok  test_mobile_html_structure
  ok  test_image_content_type_matches_extension

2개 테스트 통과 ...
```

- [ ] **Step 5: 커밋**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git add web/index.html tests/test_web_assets.py
git commit -m "feat: add mobile sheet handle and star rating HTML"
```

---

## Task 2: CSS — 데스크톱 기본 스타일 추가

**Files:**
- Modify: `outlet_map/web/index.html` (`<style>` 블록)

`.photo-strip` CSS 블록 바로 뒤(`.modal-bg` 블록 전)에 아래 규칙을 추가한다.

- [ ] **Step 1: `.sheet-handle`, `.star-row`, `.star-btn` CSS 추가**

`<style>` 안에서 다음 위치를 찾는다:
```css
  .modal-bg {
```

그 바로 앞에 삽입:
```css
  /* --- 모바일 전용 컴포넌트 (데스크톱에서는 숨김) --- */
  .sheet-handle {
    display: none;
    width: 40px; height: 4px;
    background: #ddd; border-radius: 2px;
    margin: 0 auto 12px;
    cursor: pointer;
    flex-shrink: 0;
  }
  .star-row {
    display: none;
    gap: 2px;
    align-items: center;
  }
  .star-btn {
    border: none; background: none;
    font-size: 28px; color: #ddd;
    padding: 2px 4px; cursor: pointer;
    line-height: 1;
    transition: color .1s;
  }
  .star-btn.on { color: var(--accent); }

```

- [ ] **Step 2: 테스트 실행 — 기존 테스트 여전히 통과 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 tests/test_web_assets.py
```

예상 출력: `2개 테스트 통과 ...`

- [ ] **Step 3: 커밋**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git add web/index.html
git commit -m "feat: add base CSS for sheet-handle and star-btn (hidden on desktop)"
```

---

## Task 3: CSS — 미디어 쿼리 교체

**Files:**
- Modify: `outlet_map/web/index.html` (`<style>` 끝 부분의 `@media` 블록)

- [ ] **Step 1: 기존 `@media (max-width: 880px)` 블록 전체를 교체**

현재 블록(파일 끝부분):
```css
  @media (max-width: 880px) {
    header { align-items: flex-start; flex-direction: column; }
    .search { margin-left: 0; width: 100%; }
    .search input { flex: 1; min-width: 0; }
    main {
      grid-template-columns: 1fr;
      height: auto;
      min-height: calc(100vh - 65px);
    }
    .map {
      width: 100%;
    }
    .panel {
      overflow: visible;
    }
  }
```

교체 후:
```css
  @media (max-width: 880px) {
    /* ── 헤더 슬림화 ── */
    header {
      flex-wrap: nowrap;
      height: 48px;
      padding: 0 10px;
      gap: 8px;
      overflow: hidden;
    }
    .brand img, .brand-subtitle { display: none; }
    .brand { min-width: auto; gap: 0; }
    .brand-title { font-size: 13px; }
    #tabs { flex-wrap: nowrap; gap: 4px; overflow-x: auto; scrollbar-width: none; }
    .tab { padding: 5px 8px; font-size: 12px; white-space: nowrap; }
    label.sync { font-size: 11px; white-space: nowrap; flex-shrink: 0; }
    .search { gap: 4px; flex-shrink: 0; }
    .search input { min-width: 80px; font-size: 13px; padding: 5px 8px; }
    .search button { padding: 5px 8px; font-size: 12px; }
    #syncInfo { display: none; }

    /* ── 지도 전체화면 ── */
    main { display: block; height: calc(100vh - 48px); padding: 0; }
    .map-stage { display: flex; flex-direction: column; height: 100%; }
    .room-heading { display: none; }
    .map-shell { flex: 1; min-height: 0; display: block; }
    .map {
      width: 100%; height: 100%;
      border-radius: 0;
      border-left: none; border-right: none;
      aspect-ratio: unset;
    }

    /* ── 마커 터치 영역 확대 ── */
    .dot { width: 28px; height: 28px; }
    .marker.selected .dot { width: 34px; height: 34px; }

    /* ── 바텀 시트 ── */
    .sheet-handle { display: block; }
    .panel {
      position: fixed;
      bottom: 0; left: 0; right: 0;
      width: auto;
      max-height: 65vh;
      border-radius: 16px 16px 0 0;
      border: none;
      box-shadow: 0 -4px 24px rgba(32,33,36,.18);
      transform: translateY(100%);
      transition: transform .28s ease, max-height .28s ease;
      overflow-y: hidden;
      z-index: 100;
      padding: 8px 16px 24px;
    }
    .panel.collapsed {
      transform: translateY(0);
      max-height: 148px;
      overflow: hidden;
      cursor: pointer;
    }
    .panel.expanded {
      transform: translateY(0);
      max-height: 65vh;
      overflow-y: auto;
      cursor: default;
    }

    /* ── 별점 탭 ── */
    #starRating { display: flex !important; }
    #rating, #rating + .meta { display: none; }
  }
```

- [ ] **Step 2: 테스트 실행 — 통과 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 tests/test_web_assets.py
```

예상 출력: `2개 테스트 통과 ...`

- [ ] **Step 3: 커밋**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git add web/index.html
git commit -m "feat: mobile CSS — full-screen map, bottom sheet panel, larger markers"
```

---

## Task 4: JS — 바텀 시트 동작

**Files:**
- Modify: `outlet_map/web/index.html` (`<script>` 블록)

- [ ] **Step 1: `isMobile()` 헬퍼 추가**

`<script>` 블록 첫 줄(`const STATE_URL = ...` 위)에 추가:
```javascript
const isMobile = () => window.matchMedia('(max-width: 880px)').matches;
```

- [ ] **Step 2: `renderPanel()` 함수에 시트 상태 관리 추가**

현재 `renderPanel()` 함수 전체:
```javascript
function renderPanel() {
  const sum = document.getElementById('summary');
  const form = document.getElementById('form');
  const d = curDevice();
  if (!d) {
    sum.innerHTML = `<img class="hero-photo" src="${imageUrl('room_8706_door.jpeg')}" alt="8706 강의실 표지">
      <h2>위치를 선택하세요</h2>
      <p class="meta">도면의 마커를 누르면 해당 위치 사진과 상태가 표시됩니다.</p>`;
    form.classList.add('disabled');
    renderPhotoStrip();
    return;
  }

  form.classList.remove('disabled');
  const photo = d.photo || 'room_8706_door.jpeg';
  const status = d.status || '미평가';
  const statusColor = d.color;
  let html = `<img class="hero-photo" src="${imageUrl(photo)}" alt="${d.name} 참고 사진">
    <h2>${d.name}</h2>
    <div class="meta">${d.type} · 도면 좌표 ${Math.round(d.x * 100)}%, ${Math.round(d.y * 100)}%</div>
    <div class="status" style="color:${statusColor}">● ${status}</div>
    <div class="stars">${stars(d.avg)}</div>
    <div class="meta">평가 ${d.count}건</div>`;
  const cmts = d.recent.filter(e => e.comment);
  if (cmts.length) {
    html += '<div class="recent"><b>최근 한줄평</b>';
    cmts.forEach(e => html += `<div>${e.comment}</div>`);
    html += '</div>';
  }
  sum.innerHTML = html;
  renderPhotoStrip(photo);
}
```

교체 후:
```javascript
function renderPanel() {
  const panel = document.querySelector('.panel');
  const sum = document.getElementById('summary');
  const form = document.getElementById('form');
  const d = curDevice();
  if (!d) {
    sum.innerHTML = `<img class="hero-photo" src="${imageUrl('room_8706_door.jpeg')}" alt="8706 강의실 표지">
      <h2>위치를 선택하세요</h2>
      <p class="meta">도면의 마커를 누르면 해당 위치 사진과 상태가 표시됩니다.</p>`;
    form.classList.add('disabled');
    renderPhotoStrip();
    if (isMobile()) panel.classList.remove('collapsed', 'expanded');
    return;
  }

  form.classList.remove('disabled');
  const photo = d.photo || 'room_8706_door.jpeg';
  const status = d.status || '미평가';
  const statusColor = d.color;
  let html = `<img class="hero-photo" src="${imageUrl(photo)}" alt="${d.name} 참고 사진">
    <h2>${d.name}</h2>
    <div class="meta">${d.type} · 도면 좌표 ${Math.round(d.x * 100)}%, ${Math.round(d.y * 100)}%</div>
    <div class="status" style="color:${statusColor}">● ${status}</div>
    <div class="stars">${stars(d.avg)}</div>
    <div class="meta">평가 ${d.count}건</div>`;
  const cmts = d.recent.filter(e => e.comment);
  if (cmts.length) {
    html += '<div class="recent"><b>최근 한줄평</b>';
    cmts.forEach(e => html += `<div>${e.comment}</div>`);
    html += '</div>';
  }
  sum.innerHTML = html;
  renderPhotoStrip(photo);
  if (isMobile()) {
    panel.classList.remove('expanded');
    panel.classList.add('collapsed');
  }
}
```

- [ ] **Step 3: 핸들 클릭 + collapsed 패널 탭 시 expand 리스너 추가**

`loadState();` 줄 바로 위(`setInterval` 위)에 추가:
```javascript
// 바텀 시트 토글
document.querySelector('.sheet-handle').addEventListener('click', (e) => {
  e.stopPropagation();
  if (!isMobile()) return;
  const panel = document.querySelector('.panel');
  if (panel.classList.contains('collapsed')) {
    panel.classList.replace('collapsed', 'expanded');
  } else if (panel.classList.contains('expanded')) {
    panel.classList.replace('expanded', 'collapsed');
  }
});

document.querySelector('.panel').addEventListener('click', () => {
  if (!isMobile()) return;
  const panel = document.querySelector('.panel');
  if (panel.classList.contains('collapsed')) {
    panel.classList.replace('collapsed', 'expanded');
  }
});
```

- [ ] **Step 4: 테스트 실행**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 tests/test_web_assets.py
```

예상 출력: `2개 테스트 통과 ...`

- [ ] **Step 5: 서버 실행 후 브라우저 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 web_server.py
```

Chrome DevTools → Toggle Device Toolbar (Cmd+Shift+M) → iPhone SE (375×667):
- 지도가 전체화면을 채우는지 확인
- 마커를 탭하면 아래에서 시트가 올라오는지 확인
- 핸들을 탭하면 expanded ↔ collapsed 토글 확인

- [ ] **Step 6: 커밋**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git add web/index.html
git commit -m "feat: bottom sheet JS — collapsed/expanded toggle on mobile"
```

---

## Task 5: JS — 별점 탭 선택

**Files:**
- Modify: `outlet_map/web/index.html` (`<script>` 블록)

- [ ] **Step 1: 별점 렌더 함수 추가**

`isMobile` 선언 바로 아래에 추가:
```javascript
function updateStarDisplay(val) {
  document.querySelectorAll('.star-btn').forEach(btn => {
    btn.classList.toggle('on', parseInt(btn.dataset.val, 10) <= val);
  });
}

function initStarRating() {
  updateStarDisplay(5); // select 기본값 5에 맞춤
  document.querySelectorAll('.star-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation(); // 바텀시트 collapse 방지
      const val = parseInt(btn.dataset.val, 10);
      document.getElementById('rating').value = val;
      updateStarDisplay(val);
    });
  });
}
```

- [ ] **Step 2: `loadState();` 위에 `initStarRating()` 호출 추가**

```javascript
initStarRating();
loadState();
setInterval(loadState, 3000);
```

- [ ] **Step 3: 테스트 실행**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
/opt/homebrew/bin/python3.14 tests/test_web_assets.py
```

예상 출력: `2개 테스트 통과 ...`

- [ ] **Step 4: 서버 실행 후 브라우저 모바일 에뮬레이션으로 확인**

```bash
/opt/homebrew/bin/python3.14 web_server.py
```

Chrome DevTools → iPhone SE:
1. 마커 탭 → 시트 올라옴 → 탭해서 expand
2. 별점 ★ 탭 → 선택한 숫자까지 노란색으로 채워지는지 확인
3. "평가 등록" 클릭 → 올바른 rating 값으로 POST 되는지 확인 (DevTools Network 탭)
4. 데스크톱 너비로 돌리면 select 드롭다운 다시 나타나는지 확인

- [ ] **Step 5: 커밋**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git add web/index.html
git commit -m "feat: star tap rating for mobile — syncs with existing select"
```

---

## 완료 기준 체크리스트

- [ ] 데스크톱(1280px): 기존 2칸 그리드 그대로
- [ ] 모바일(375px): 지도 전체화면, 헤더 48px
- [ ] 마커 탭 → 바텀 시트 슬라이드업
- [ ] 핸들/시트 탭 → expanded ↔ collapsed
- [ ] ★ 탭 선택 → 평가 등록 시 rating 전송 정확
- [ ] READ_ONLY 모드: 평가 폼 숨김 유지
- [ ] 편집 모드: 지도 탭 → 새 기기 등록 모달 정상 동작
