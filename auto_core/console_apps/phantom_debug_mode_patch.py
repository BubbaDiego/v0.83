def dump_visible_buttons(page):
    try:
        buttons = page.locator("button")
        count = buttons.count()
        print(f"[DEBUG] Found {count} <button> elements.")

        with open("button_dump.txt", "w", encoding="utf-8") as f:
            for i in range(count):
                try:
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        label = btn.inner_text().strip()
                        html = btn.evaluate("el => el.outerHTML")
                        print(f"[DEBUG] Button[{i}]: '{label}' → {html[:120]}...")
                        f.write(f"[{i}] {label}\n")
                except Exception as e:
                    print(f"[DEBUG] Button[{i}] error: {e}")
    except Exception as sweep_fail:
        print(f"[DEBUG] DOM sweep failed entirely: {sweep_fail}")
