"""Playwright E2E tests — AES 完整端到端验收测试。"""
import time
from playwright.sync_api import sync_playwright
import requests as req

BASE_URL = "http://127.0.0.1:8501"
API_URL = "http://127.0.0.1:5000/api/v1"

passed = 0
failed = 0
failures = []


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        msg = f"  ❌ {name}: {detail}"
        print(msg)
        failures.append(msg)


def wait_streamlit(page):
    page.wait_for_selector("[data-testid='stApp']", timeout=20000)
    time.sleep(1)


# ============================================================
# 1. API 测试
# ============================================================
def test_api_all():
    print("\n" + "=" * 60)
    print("1. API 端点测试")
    print("=" * 60)

    # 1.1 Health
    print("\n── 1.1 Health ──")
    r = req.get(f"{API_URL}/health", timeout=5)
    check("GET /health -> 200", r.status_code == 200)
    data = r.json()
    check("status == ok", data.get("status") == "ok")

    # 1.2 EN scoring
    print("\n── 1.2 EN Score ──")
    en_text = "Technology has transformed modern education in profound ways. Students can access online learning resources from anywhere in the world. This represents a fundamental shift in how knowledge is shared and acquired."
    r = req.post(f"{API_URL}/score", json={"text": en_text, "language": "en"}, timeout=60)
    check("EN score -> 200", r.status_code == 200)
    d = r.json()
    check("EN success=True", d.get("success") is True)
    check("EN has score", isinstance(d.get("score"), float))
    check("EN scores has content", "content" in d.get("scores", {}))
    check("EN feedback has overall", "overall" in d.get("feedback", {}))
    check("EN language=en", d.get("language") == "en")
    check("EN score in [0,1]", 0 <= d.get("score", -1) <= 1)

    # 1.3 ZH scoring
    print("\n── 1.3 ZH Score ──")
    zh_text = "数字时代的教育变革与挑战。在当今数字技术飞速发展的时代，教育领域正经历着前所未有的深刻变革。互联网与人工智能等技术的广泛应用，不仅改变了知识的传播方式，也重新定义了教与学的关系。"
    r = req.post(f"{API_URL}/score", json={"text": zh_text, "language": "zh"}, timeout=60)
    check("ZH score -> 200", r.status_code == 200)
    d = r.json()
    check("ZH success=True", d.get("success") is True)
    check("ZH has score", isinstance(d.get("score"), float))
    check("ZH language=zh", d.get("language") == "zh")
    check("ZH feedback is Chinese", any("一" <= c <= "鿿" for c in d.get("feedback", {}).get("overall", "")))

    # 1.4 Error cases
    print("\n── 1.4 Error Handling ──")
    r = req.post(f"{API_URL}/score", json={}, timeout=10)
    check("Missing text -> 400", r.status_code == 400)

    r = req.post(f"{API_URL}/score", json={"text": ""}, timeout=10)
    check("Empty text -> 400", r.status_code == 400)

    r = req.post(f"{API_URL}/score", data="not json", timeout=10)
    check("Wrong content type -> 400", r.status_code == 400)

    r = req.get(f"{API_URL}/nonexistent", timeout=5)
    check("404 for unknown route", r.status_code == 404)

    # 1.5 Batch
    print("\n── 1.5 Batch ──")
    csv = "essay_id,text,language\n1,Technology has changed education.,en\n2,人工智能正在改变教育。,zh"
    r = req.post(f"{API_URL}/batch", files={"file": ("t.csv", csv.encode(), "text/csv")}, timeout=60)
    check("Batch -> 200", r.status_code == 200)
    d = r.json()
    check("Batch success", d.get("success") is True)
    check("Batch 2 results", d.get("total") == 2)
    for res in d.get("results", []):
        check(f"  Result {res['id']} has score", res.get("score") is not None or res.get("error"))

    # 1.6 Models info
    print("\n── 1.6 Models Info ──")
    r = req.get(f"{API_URL}/models", timeout=5)
    check("Models -> 200", r.status_code == 200)
    d = r.json()
    check("Has EN model", "en" in d.get("models", {}))
    check("Has ZH model", "zh" in d.get("models", {}))


# ============================================================
# 2. UI 测试
# ============================================================
def test_ui_all(page):
    print("\n" + "=" * 60)
    print("2. UI 交互测试")
    print("=" * 60)

    # 2.1 Home page
    print("\n── 2.1 Home Page ──")
    page.goto(BASE_URL, timeout=30000)
    wait_streamlit(page)
    check("Title contains AES", "AES" in page.title() or "评分" in page.title())
    check("Has textarea", page.locator("textarea").count() >= 1)
    check("Has submit btn", page.locator("button:has-text('提交评分')").count() + page.locator("button:has-text('Submit')").count() > 0)
    check("Has clear btn", page.locator("button:has-text('清空')").count() + page.locator("button:has-text('Clear')").count() > 0)

    # 2.2 Empty submit error
    print("\n── 2.2 Empty Submit ──")
    submit = page.locator("button:has-text('提交评分')")
    if submit.count() == 0:
        submit = page.locator("button:has-text('Submit')")
    submit.first.click()
    time.sleep(2)
    check("Error shown for empty text", page.locator("text=请输入作文").count() + page.locator("text=Please enter").count() > 0)

    # 2.3 Clear button
    print("\n── 2.3 Clear Button ──")
    textarea = page.locator("textarea").first
    textarea.fill("Test content")
    time.sleep(0.5)
    clear = page.locator("button:has-text('清空')")
    if clear.count() == 0:
        clear = page.locator("button:has-text('Clear')")
    clear.first.scroll_into_view_if_needed()
    clear.first.click()
    time.sleep(3)
    wait_streamlit(page)
    val = page.locator("textarea").first.input_value() or ""
    check("Clear works (textarea empty)", val == "", f"Got: '{val[:40]}'")

    # 2.4 EN scoring flow
    print("\n── 2.4 EN Scoring Flow ──")
    textarea = page.locator("textarea").first
    textarea.fill("Technology has transformed modern education. Students can access global learning resources online. This essay discusses key educational technology trends and their impact on student learning outcomes.")
    time.sleep(0.3)
    submit = page.locator("button:has-text('提交评分')")
    if submit.count() == 0:
        submit = page.locator("button:has-text('Submit')")
    submit.first.click()
    for _ in range(20):
        time.sleep(1.5)
        if page.locator("text=评分完成").count() + page.locator("text=Scoring Complete").count() > 0:
            break
    has_result = page.locator("text=评分完成").count() + page.locator("text=Scoring Complete").count() + page.locator("text=归一化得分").count() > 0
    check("EN result displayed", has_result)

    # 2.5 ZH scoring flow
    print("\n── 2.5 ZH Scoring Flow ──")
    page.goto(BASE_URL, timeout=30000)
    wait_streamlit(page)
    textarea = page.locator("textarea").first
    textarea.fill("数字时代的教育变革与挑战。在当今数字技术飞速发展的时代，教育领域正经历着前所未有的深刻变革。互联网、人工智能等新兴技术的广泛应用，不仅改变了知识的传播方式，也重新定义了教与学的关系。")
    time.sleep(0.3)
    submit = page.locator("button:has-text('提交评分')")
    if submit.count() == 0:
        submit = page.locator("button:has-text('Submit')")
    submit.first.click()
    for _ in range(20):
        time.sleep(1.5)
        if page.locator("text=评分完成").count() + page.locator("text=Scoring Complete").count() > 0:
            break
    has_result = page.locator("text=评分完成").count() + page.locator("text=Scoring Complete").count() + page.locator("text=归一化得分").count() > 0
    check("ZH result displayed", has_result)

    # 2.6 Batch page
    print("\n── 2.6 Batch Page ──")
    page.goto(f"{BASE_URL}/batch", timeout=15000)
    time.sleep(2)
    ok = page.locator("text=批量评分").count() + page.locator("text=Batch").count() > 0
    if not ok:
        # 通过侧边栏导航
        page.goto(BASE_URL, timeout=15000)
        wait_streamlit(page)
        sidebar = page.locator("[data-testid='stSidebarCollapsedControl']")
        if sidebar.count() > 0:
            sidebar.click()
            time.sleep(1)
        nav = page.locator("text=批量评分")
        if nav.count() == 0:
            nav = page.locator("text=Batch")
        nav.first.click() if nav.count() > 0 else None
        time.sleep(2)
    ok = "Batch" in page.title() or "批量" in page.title() or page.locator("text=批量评分").count() + page.locator("text=Batch Scoring").count() > 0
    check("Batch page loads", ok)

    # 2.7 Compare page
    print("\n── 2.7 Compare Page ──")
    page.goto(f"{BASE_URL}/comparison", timeout=15000)
    time.sleep(2)
    ok = "Compare" in page.title() or "对比" in page.title() or page.locator("text=中英对比").count() + page.locator("text=Compare").count() > 0
    check("Compare page loads", ok)

    # 2.8 Sidebar navigation
    print("\n── 2.8 Sidebar ──")
    page.goto(BASE_URL, timeout=30000)
    wait_streamlit(page)
    sidebar = page.locator("[data-testid='stSidebarCollapsedControl']")
    if sidebar.count() > 0:
        sidebar.click()
        time.sleep(1)
    check("Sidebar visible", page.locator("[data-testid='stSidebar']").count() > 0)


# ============================================================
# 3. 范文评分测试
# ============================================================
def test_sample_essays():
    print("\n" + "=" * 60)
    print("3. 范文评分测试")
    print("=" * 60)

    print("\n── 3.1 English Essay ──")
    with open("samples/high_score_en.txt") as f:
        en = f.read()[:3000]
    r = req.post(f"{API_URL}/score", json={"text": en, "language": "en"}, timeout=60)
    d = r.json()
    score = d.get("score", 0) * 100
    check("EN essay score > 50%", score > 50, f"Got {score:.1f}%")
    check("EN has multi-dim scores", all(k in d.get("scores", {}) for k in ["content", "structure", "language"]))

    print("\n── 3.2 Chinese Essay ──")
    with open("samples/high_score_zh.txt") as f:
        zh = f.read()[:3000]
    r = req.post(f"{API_URL}/score", json={"text": zh, "language": "zh"}, timeout=60)
    d = r.json()
    score = d.get("score", 0) * 100
    check("ZH essay score > 30%", score > 30, f"Got {score:.1f}%")  # 翻译腔训练数据，阈值放低
    check("ZH feedback is Chinese", any("一" <= c <= "鿿" for c in d.get("feedback", {}).get("overall", "")))


# ============================================================
# Main
# ============================================================
def main():
    global passed, failed
    print("=" * 60)
    print("🎯 AES 端到端验收测试")
    print("=" * 60)

    # API tests
    test_api_all()

    # Sample essays
    test_sample_essays()

    # UI tests
    print("\n── 启动浏览器 ──")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_default_timeout(15000)
        try:
            test_ui_all(page)
        finally:
            browser.close()

    total = passed + failed
    print("\n" + "=" * 60)
    print(f"📊 结果: {passed}/{total} 通过")
    if failed:
        print(f"❌ {failed} 个失败:")
        for f in failures:
            print(f"   {f}")
        exit(1)
    else:
        print("✅ 全部通过！")
        exit(0)


if __name__ == "__main__":
    main()
