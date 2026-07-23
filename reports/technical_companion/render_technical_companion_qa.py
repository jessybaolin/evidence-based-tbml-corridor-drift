"""Render each companion page at print dimensions for visual QA."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
HTML_PATH = HERE / "technical_companion_source.html"
OUTPUT_DIR = HERE / "qa_pages"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 900, "height": 1280},
            device_scale_factor=1.4,
        )
        page = context.new_page()
        page.goto(HTML_PATH.as_uri(), wait_until="load")
        page.add_style_tag(
            content="""
            body { margin: 0; background: #dfe5ec; }
            .page {
              width: 182mm;
              height: 271mm;
              min-height: 271mm;
              overflow: hidden;
              margin: 0;
              background: #ffffff;
            }
            """
        )
        page.wait_for_timeout(800)

        pages = page.locator(".page")
        page_count = pages.count()
        if page_count != 38:
            raise RuntimeError(f"Expected 38 pages, found {page_count}")

        for index in range(page_count):
            target = pages.nth(index)
            dimensions = target.evaluate(
                """(element) => ({
                    scrollHeight: element.scrollHeight,
                    clientHeight: element.clientHeight,
                    scrollWidth: element.scrollWidth,
                    clientWidth: element.clientWidth
                })"""
            )
            if dimensions["scrollHeight"] > dimensions["clientHeight"] + 2:
                raise RuntimeError(
                    f"Page {index + 1} has vertical overflow: {dimensions}"
                )
            if dimensions["scrollWidth"] > dimensions["clientWidth"] + 2:
                raise RuntimeError(
                    f"Page {index + 1} has horizontal overflow: {dimensions}"
                )
            target.screenshot(
                path=OUTPUT_DIR / f"page_{index + 1:02d}.png",
                animations="disabled",
            )

        context.close()
        browser.close()

    print(f"Rendered {page_count} pages to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
