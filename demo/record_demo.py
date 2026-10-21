#!/usr/bin/env python3
"""
Tenkemakker: automatic demo run + screencast.

Plays the whole demo in a real browser with calm pacing and on-screen captions,
and records it as a video. Use it to rehearse, as a backup video if the live demo
fails, or to show the run on a projector without finger slips.

One-time setup (on the laptop that runs it):
    pip install playwright
    playwright install chromium

First time against the hosted site, log in once (opens a browser window,
type your email and the one-time code; the login is remembered for 24 h):
    python3 demo/record_demo.py --login

Record:
    python3 demo/record_demo.py                         # desktop, Norwegian
    python3 demo/record_demo.py --device phone --lang en
    python3 demo/record_demo.py --show                  # watch it live (headed), still records
    python3 demo/record_demo.py --url file:///path/to/index.html   # local file, no login

Output: demo/out/tenkemakker-<device>-<lang>.webm (and .mp4 if ffmpeg is installed).
All data shown is fictional.
"""
import argparse, os, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

HERE = Path(__file__).resolve().parent
PROFILE = HERE / ".profile"          # remembers the Cloudflare Access login (git-ignored)
OUT = HERE / "out"

T = {  # captions and typed text, per language
  "nb": {
    "intro": "Ida, 13 år. Matteleksa – med en KI som ikke gir svaret.",
    "stuck": "Hun står fast og ber om hjelp. Makker svarer med et spørsmål.",
    "dunno": "«Vet ikke» – ett trykk, ingen skriving.",
    "wrong": "Hun prøver 3/7. Feil koster ingenting.",
    "right": "11/12 – riktig, med bare ett hint.",
    "teach": "Rollebytte: Makker har misforstått. Ida må forklare.",
    "explain": "bitene må være like store, så jeg gjør begge om til tolvdeler: 8/12 + 3/12",
    "explain2": "du må finne en fellesnevner, tolv, før du legger sammen",
    "class": "Klassen: mot hverandre – eller sammen mot et felles mål.",
    "topic": "Øv på hva som helst: Ida velger et tema, KI lager oppgaven.",
    "topicText": "sannsynlighet med terning",
    "lab": "Brøkverkstedet: samme mengde, nye måter å se den på.",
    "parent": "Forelderen ser mønsteret – og får et spørsmål til middagen.",
    "teacher": "Læreren ser hva hele klassen misforstår, og hvem som trenger hjelp nå.",
    "vision": "2030: samme ettermiddag, to ganger. Og hele Oslo.",
    "end": "Tenkemakker – KI som får barn til å tenke selv.",
  },
  "en": {
    "intro": "Ida, 13. Maths homework – with an AI that won't give the answer.",
    "stuck": "She's stuck and asks for help. Makker answers with a question.",
    "dunno": "“Don't know” – one tap, no typing.",
    "wrong": "She tries 3/7. Mistakes cost nothing.",
    "right": "11/12 – correct, with just one hint.",
    "teach": "Role swap: Makker got it wrong. Ida has to explain.",
    "explain": "the pieces need to be the same size, so I turn both into twelfths: 8/12 + 3/12",
    "explain2": "you need a common denominator, twelve, before you add them",
    "class": "The class: head to head – or together towards a shared goal.",
    "topic": "Practise anything: Ida picks a topic, AI makes the task.",
    "topicText": "probability with a dice",
    "lab": "The fraction lab: same amount, new ways to see it.",
    "parent": "The parent sees the pattern – and gets a question for dinner.",
    "teacher": "The teacher sees what the whole class gets wrong, and who needs help now.",
    "vision": "2030: the same afternoon, twice. And all of Oslo.",
    "end": "Tenkemakker – AI that makes kids think for themselves.",
  },
}

CAPTION_JS = """
(text) => {
  let el = document.getElementById('__demo_caption');
  if (!el) {
    el = document.createElement('div'); el.id = '__demo_caption';
    el.style.cssText = 'position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:99999;'
      + 'max-width:min(92vw,760px);background:rgba(30,23,72,.92);color:#fff;padding:12px 20px;border-radius:16px;'
      + 'font:700 clamp(15px,2.2vw,22px)/1.3 system-ui,sans-serif;text-align:center;box-shadow:0 8px 30px rgba(0,0,0,.3);'
      + 'pointer-events:none;transition:opacity .3s';
    document.body.appendChild(el);
  }
  el.style.opacity = text ? '1' : '0';
  if (text) el.textContent = text;
}
"""


class Demo:
    def __init__(self, page, lang, phone, pace):
        self.p, self.t, self.phone, self.pace = page, T[lang], phone, pace

    def wait(self, s):
        self.p.wait_for_timeout(int(s * 1000 * self.pace))

    def caption(self, key, hold=2.2):
        self.p.evaluate(CAPTION_JS, self.t[key] if key else "")
        if key:
            self.wait(hold)

    def makker_count(self):
        return self.p.locator("#chat .msg.m:not(.thinking)").count()

    def wait_makker(self, before, timeout=30):
        """Wait until Makker has written a new message (real AI can take a few seconds)."""
        end = time.time() + timeout
        while time.time() < end:
            if self.makker_count() > before and self.p.locator("#chat .thinking").count() == 0:
                self.wait(1.6)
                return True
            self.p.wait_for_timeout(250)
        return False

    def click(self, sel):
        loc = self.p.locator(sel).first
        loc.scroll_into_view_if_needed()
        self.wait(0.4)
        loc.click()

    def type(self, sel, text, delay=55):
        loc = self.p.locator(sel).first
        loc.scroll_into_view_if_needed()
        loc.click()
        loc.fill("")
        loc.type(text, delay=int(delay * self.pace))

    def nav(self, view):
        if self.phone:
            self.click(f".bottomnav button[data-v={view}]")
        else:
            tab = {"elev": "#tab-elev", "forelder": "#tab-forelder", "laerer": "#tab-laerer", "brok": "#tab-brok"}.get(view)
            if tab:
                self.click(tab)
            elif view == "klasse":
                self.click("#tab-elev")
                self.p.locator("#lower").scroll_into_view_if_needed()
        self.p.evaluate("window.scrollTo({top:0,behavior:'instant'})") if view != "klasse" else None
        self.wait(0.8)

    def run(self):
        p = self.p
        self.caption("intro", 3)

        # 1. Stuck → hint → answer the hint with one tap
        before = self.makker_count()
        self.click("#stuck")
        self.wait_makker(before)
        self.caption("stuck")
        self.caption("dunno", 1.4)
        before = self.makker_count()
        self.click("#chips button")
        self.wait_makker(before)

        # 2. Wrong answer, then right answer
        self.caption("wrong", 1.2)
        self.type("#answer", "3/7", 120)
        self.click("#answer-form button[type=submit]")
        self.wait(1.8)
        self.caption("right", 1.0)
        self.type("#answer", "11/12", 120)
        before = self.makker_count()
        self.click("#answer-form button[type=submit]")
        self.wait(2.5)  # confetti + points

        # 3. Teach Makker
        self.wait_makker(before)
        self.caption("teach", 2.0)
        for text in (self.t["explain"], self.t["explain2"]):
            if not p.locator("#teach").is_visible():
                break
            self.type("#explain", text, 45)
            before = self.makker_count()
            self.click("#send")
            self.wait_makker(before)
            self.wait(1.2)
        self.wait(1.5)

        # 4. Class board, both modes
        self.caption("class", 0.5)
        self.nav("klasse")
        self.wait(1.8)
        self.click("#m-tog")
        self.wait(2.2)
        self.click("#m-vs")
        self.wait(1.2)

        # 5. Endless tasks
        self.nav("elev")
        self.caption("topic", 0.8)
        if not p.locator("#topic-form").is_visible():
            self.click(".new-topic")
        self.type("#topic", self.t["topicText"], 70)
        self.click("#make-task")
        try:
            p.wait_for_function("() => document.querySelector('#topic-form').hidden", timeout=30000)
        except PWTimeout:
            pass
        self.wait(3)
        self.click("#stuck")
        self.wait(2.5)

        # 6. Fraction lab
        self.caption("lab", 0.5)
        self.nav("brok")
        self.wait(1.5)
        if p.locator("#f-answer").count():
            self.type("#f-answer", "11/12", 120)
            self.click("#f-answer-form button[type=submit]")
            self.wait(2.5)

        # 7. Parent and teacher
        self.caption("parent", 0.5)
        self.nav("forelder")
        self.wait(2.5)
        p.mouse.wheel(0, 500); self.wait(2)
        self.caption("teacher", 0.5)
        self.nav("laerer")
        self.wait(2.5)
        p.mouse.wheel(0, 600); self.wait(2.5)

        # 8. 2030
        self.caption("vision", 0.5)
        p.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        self.click(".vision-link")
        p.wait_for_load_state("domcontentloaded")
        self.p.evaluate(CAPTION_JS, self.t["vision"])
        self.wait(2.5)
        for _ in range(4):
            p.keyboard.press("ArrowRight")
            self.wait(2.2)
        sliders = p.locator("input[type=range]")
        if sliders.count():
            sliders.first.scroll_into_view_if_needed()
            self.wait(1)
            sliders.first.focus()
            for _ in range(12):
                p.keyboard.press("ArrowRight")
                self.wait(0.15)
            self.wait(2.5)
        self.p.evaluate(CAPTION_JS, self.t["end"])
        self.wait(3.5)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://tenkemakker.ethlo.com/")
    ap.add_argument("--device", choices=["desktop", "phone"], default="desktop")
    ap.add_argument("--lang", choices=["nb", "en"], default="nb")
    ap.add_argument("--pace", type=float, default=1.0, help="1.0 = normal, 1.5 = slower, 0.6 = faster")
    ap.add_argument("--show", action="store_true", help="show the browser while recording")
    ap.add_argument("--login", action="store_true", help="open a browser to log in once, then exit")
    a = ap.parse_args()

    phone = a.device == "phone"
    size = {"width": 390, "height": 844} if phone else {"width": 1280, "height": 720}
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_raw"; shutil.rmtree(tmp, ignore_errors=True)

    with sync_playwright() as pw:
        if a.login:
            ctx = pw.chromium.launch_persistent_context(str(PROFILE), headless=False, viewport=size)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(a.url)
            input("\nLog in in the browser window (email + one-time code).\nWhen you see Tenkemakker, press Enter here … ")
            ctx.close()
            print("Login saved. Now run without --login to record.")
            return

        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE), headless=not a.show, viewport=size,
            device_scale_factor=2 if phone else 1, is_mobile=phone, has_touch=phone,
            record_video_dir=str(tmp), record_video_size=size, locale="nb-NO" if a.lang == "nb" else "en-GB")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(a.url)
        page.wait_for_timeout(1500)
        if "cloudflareaccess.com" in page.url or not page.locator("#task-text").count():
            ctx.close()
            sys.exit("Not logged in. Run once with --login first.")
        # fresh state: right language, start screen
        page.evaluate(f"""() => {{ try{{ localStorage.setItem('tenkemakker-lang','{a.lang}'); }}catch(e){{}} }}""")
        page.reload(); page.wait_for_timeout(1500)
        video = page.video
        try:
            Demo(page, a.lang, phone, a.pace).run()
        finally:
            ctx.close()
        src = Path(video.path())
        dst = OUT / f"tenkemakker-{a.device}-{a.lang}.webm"
        shutil.move(str(src), dst); shutil.rmtree(tmp, ignore_errors=True)
        print("Video:", dst)
        if shutil.which("ffmpeg"):
            mp4 = dst.with_suffix(".mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(dst), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=False)
            if mp4.exists():
                print("Video:", mp4)


if __name__ == "__main__":
    main()
