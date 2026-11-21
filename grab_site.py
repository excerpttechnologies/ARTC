import asyncio
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


BASE_URL = "https://artechnocraft.com"
ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
FILES_DIR = SITE_DIR / "files"
CLONE_DIR = ROOT / "clone"
ROUTES = [
    "/",
    "/about",
    "/about1",
    "/about3",
    "/product",
    "/Rapid",
    "/mould",
    "/mmanu",
    "/mtq",
    "/mp",
    "/Gallry",
    "/products",
    "/inf",
    "/Client",
    "/Contact",
]


def route_filename(route: str) -> str:
    if route == "/":
        return "index.html"
    return f"{route.lstrip('/')}.html"


def response_filename(url: str) -> Path:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        path = "index"
    if parsed.netloc.lower() != urlparse(BASE_URL).netloc.lower():
        path = f"external/{parsed.netloc}/{path}"
    if parsed.query:
        suffix = hashlib.sha256(parsed.query.encode()).hexdigest()[:10]
        target = Path(path)
        path = str(target.with_name(f"{target.stem}-{suffix}{target.suffix}"))
    return FILES_DIR / path


def localize_html(html: str) -> str:
    route_map = {route: route_filename(route) for route in ROUTES}

    def replace_link(match: re.Match[str]) -> str:
        prefix, quote, link = match.groups()
        parsed = urlparse(link)
        if parsed.netloc and parsed.netloc.lower() not in {
            urlparse(BASE_URL).netloc.lower(),
            "www.artechnocraft.com",
        }:
            target = response_filename(link).relative_to(FILES_DIR).as_posix()
            return f'{prefix}{quote}/files/{target}{quote}'
        path = parsed.path
        if link.startswith("/") and path in route_map:
            return f'{prefix}{quote}{route_map[path]}{quote}'
        if parsed.netloc and parsed.path in route_map:
            return f'{prefix}{quote}{route_map[parsed.path]}{quote}'
        if parsed.netloc and parsed.netloc.lower() in {
            urlparse(BASE_URL).netloc.lower(),
            "www.artechnocraft.com",
        }:
            local_path = parsed.path
            if parsed.query:
                local_path += f"?{parsed.query}"
            return f'{prefix}{quote}{local_path}{quote}'
        return match.group(0)

    html = re.sub(
        r'(\b(?:href|src|poster)\s*=\s*)(["\'])(.*?)\2',
        replace_link,
        html,
    )
    return html


async def main() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    CLONE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded: set[str] = set()
    failed_downloads: list[dict[str, object]] = []
    route_results: list[dict[str, object]] = []
    save_tasks: set[asyncio.Task] = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1366, "height": 900})

        async def save_response(response) -> None:
            url = response.url
            if url in downloaded:
                return
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return
            downloaded.add(url)
            try:
                body = await response.body()
                target = response_filename(url)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
                if response.status >= 400:
                    failed_downloads.append(
                        {"url": url, "status": response.status, "saved": str(target)}
                    )
            except Exception as error:
                failed_downloads.append(
                    {"url": url, "status": response.status, "error": str(error)}
                )

        def track_response(response) -> None:
            task = asyncio.create_task(save_response(response))
            save_tasks.add(task)
            task.add_done_callback(save_tasks.discard)

        page.on("response", track_response)

        async def load_root() -> None:
            await page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=90000)
            try:
                await page.wait_for_load_state("networkidle", timeout=45000)
            except Exception:
                pass
            await page.locator("body").wait_for()

        for route in ROUTES:
            try:
                await load_root()
                if route != "/":
                    link = page.locator(f'a[href="{route}"]').first
                    if await link.count() == 0:
                        route_results.append(
                            {"route": route, "status": "missing app link"}
                        )
                        continue
                    await link.evaluate("(element) => element.click()")
                    try:
                        await page.wait_for_url(f"**{route}", timeout=20000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(1200)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass

                current_route = urlparse(page.url).path.rstrip("/") or "/"
                if current_route != route:
                    route_results.append(
                        {
                            "route": route,
                            "status": "navigation did not reach requested route",
                            "actual": current_route,
                        }
                    )
                    continue

                height = await page.locator("body").evaluate(
                    "(element) => element.scrollHeight"
                )
                for y in range(0, height, 700):
                    await page.evaluate(f"window.scrollTo(0, {y})")
                    await page.wait_for_timeout(90)
                await page.wait_for_timeout(500)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(250)

                filename = route_filename(route)
                html = await page.content()
                (SITE_DIR / filename).write_text(html, encoding="utf-8")
                await page.screenshot(
                    path=str(SITE_DIR / filename.replace(".html", ".png")),
                    full_page=True,
                )
                await page.set_viewport_size({"width": 390, "height": 844})
                await page.screenshot(
                    path=str(
                        SITE_DIR / filename.replace(".html", "-mobile.png")
                    ),
                    full_page=True,
                )
                await page.set_viewport_size({"width": 1366, "height": 900})
                route_results.append(
                    {
                        "route": route,
                        "status": "captured",
                        "title": await page.title(),
                        "html": filename,
                    }
                )
            except Exception as error:
                route_results.append(
                    {"route": route, "status": "capture failed", "error": str(error)}
                )

        await load_root()
        for label, index in [
            ("about-dropdown", 0),
            ("functions-dropdown", 1),
        ]:
            try:
                await page.locator(".navigation").evaluate(
                    "(element) => { element.style.left = '0px'; }"
                )
                item = page.locator(".navigation > li").nth(index)
                await item.hover(timeout=5000)
                await page.wait_for_timeout(400)
                await page.screenshot(
                    path=str(SITE_DIR / f"{label}.png"), full_page=True
                )
            except Exception as error:
                failed_downloads.append(
                    {"url": label, "error": f"dropdown screenshot: {error}"}
                )
        if save_tasks:
            await asyncio.gather(*save_tasks)
        await browser.close()

    for route in ROUTES:
        captured = SITE_DIR / route_filename(route)
        if captured.exists():
            target = CLONE_DIR / route_filename(route)
            target.write_text(
                localize_html(captured.read_text(encoding="utf-8")),
                encoding="utf-8",
            )

    for item in FILES_DIR.iterdir():
        target = CLONE_DIR / item.name
        if item.is_dir():
            import shutil

            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_bytes()
            if item.suffix.lower() == ".css":
                css = content.decode("utf-8", errors="replace")

                def localize_css_url(match: re.Match[str]) -> str:
                    url = match.group(0)
                    target_path = response_filename(url).relative_to(
                        FILES_DIR
                    ).as_posix()
                    if (FILES_DIR / target_path).exists():
                        return f"/files/{target_path}"
                    return url

                css = re.sub(
                    r'https?://[^)"\'\s]+',
                    localize_css_url,
                    css,
                )
                content = css.encode("utf-8")
            target.write_bytes(content)

    report = {
        "routes": route_results,
        "downloads_failed": failed_downloads,
        "downloaded_responses": len(downloaded),
        "files_directory": str(FILES_DIR),
        "clone_directory": str(CLONE_DIR),
    }
    (SITE_DIR / "capture-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
