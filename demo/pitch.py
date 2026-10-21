#!/usr/bin/env python3
"""
Tenkemakker: 90-second pitch video with overlays.

Plays the app in exactly the eight beats of demo/SCRIPT.md, with a lower-third
overlay per beat, a progress bar and a timer, and records it as a video.

    pip install playwright && playwright install chromium     # once
    python3 demo/pitch.py --login                             # once, for tenkemakker.ethlo.com
    python3 demo/pitch.py                                     # Norwegian
    python3 demo/pitch.py --lang en
    python3 demo/pitch.py --url file:///path/to/index.html    # local file, practice mode

Output: demo/out/tenkemakker-pitch-<lang>.webm (+ .mp4 with ffmpeg). Fictional data only.
"""
import argparse, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PROFILE, OUT = HERE / ".profile", HERE / "out"
TOTAL = 90

# (seconds, kicker, title, on-screen line) per beat, matching demo/SCRIPT.md
BEATS = {
 "nb": [
  (10, "Problemet", "Ida, 13 år · Matteleksa", "En vanlig KI løser den på to sekunder. Hva lærer hun da?"),
  (12, "Hjelp, ikke fasit", "Hun står fast – og får et spørsmål tilbake", "Svar med ett trykk eller med stemmen."),
  (10, "Feil er gratis", "Poeng for å tenke, ikke for fart", "Færre hint gir flere tankepoeng."),
  (14, "Rollebytte", "Lær bort til Makker", "Makker tror svaret er 3/7. Nå må Ida forklare – det gir mest poeng."),
  (10, "Klassen", "Mot hverandre – eller sammen?", "Et valg for skoler og foreldre, ikke for appen."),
  (10, "Øv på hva som helst", "Ida skriver et tema – KI lager oppgaven", "Med hint og en misforståelse å rydde opp i."),
  (12, "Forelder og lærer", "De ser mønsteret, ikke samtalen", "Et spørsmål til middagen. Klassens misforståelser før prøven."),
  (12, "2030", "Tenker KI for barna – eller får den dem til å tenke?", "64 675 elever i Oslo. Tenkemakker."),
 ],
 "en": [
  (10, "The problem", "Ida, 13 · Maths homework", "An ordinary AI solves it in two seconds. What does she learn?"),
  (12, "Help, not answers", "She's stuck – and gets a question back", "Reply with one tap, or with your voice."),
  (10, "Mistakes are free", "Points for thinking, not speed", "Fewer hints earn more thinking points."),
  (14, "Role swap", "Teach Makker", "Makker thinks the answer is 3/7. Now Ida explains – that earns the most."),
  (10, "The class", "Compete – or together?", "A choice for schools and parents, not the app."),
  (10, "Practise anything", "Ida types a topic – AI makes the task", "With hints and a misunderstanding to untangle."),
  (12, "Parents and teachers", "They see the pattern, not the conversation", "A question for dinner. The class's misconceptions before the test."),
  (12, "2030", "Does AI think for children – or make them think?", "64,675 pupils in Oslo. Tenkemakker."),
 ],
}
TEXT = {
 "nb": {"explain": "du må ha felles nevner, så gjør begge om til tolvdeler først", "topic": "sannsynlighet med terning", "end": "KI som får barn til å tenke selv"},
 "en": {"explain": "you need a common denominator, so make both into twelfths first", "topic": "probability with a dice", "end": "AI that makes kids think for themselves"},
}

OVERLAY_JS = """
({i, n, kicker, title, line, elapsed, total, end}) => {
  const css = `
  #__pitch{position:fixed;inset:0;pointer-events:none;z-index:99999;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
  #__pitch .bar{position:absolute;left:0;top:0;height:6px;background:linear-gradient(90deg,#6b4cf6,#14c49b);transition:width .4s linear}
  #__pitch .clock{position:absolute;right:16px;top:14px;background:rgba(30,23,72,.85);color:#fff;font:700 14px/1 system-ui;padding:7px 11px;border-radius:999px;font-variant-numeric:tabular-nums}
  #__pitch .lt{position:absolute;left:24px;bottom:28px;max-width:min(620px,86vw);background:rgba(30,23,72,.94);color:#fff;border-radius:20px;padding:16px 22px 18px;
    box-shadow:0 14px 40px rgba(0,0,0,.35);border-left:8px solid #ffc531;animation:__in .45s cubic-bezier(.2,1.2,.4,1)}
  #__pitch .k{font:800 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:#ffc531;margin-bottom:8px;display:flex;gap:10px}
  #__pitch .k b{color:#b9adff}
  #__pitch .t{font:800 26px/1.15 system-ui;margin:0 0 6px}
  #__pitch .l{font:500 17px/1.35 system-ui;opacity:.92;margin:0}
  #__pitch .endcard{position:absolute;inset:0;display:grid;place-items:center;background:rgba(30,23,72,.93);color:#fff;text-align:center;animation:__fade .6s}
  #__pitch .endcard h1{font:900 64px/1 system-ui;margin:0;color:#b9adff}
  #__pitch .endcard h1 span{color:#3ddcb3}
  #__pitch .endcard p{font:600 24px/1.3 system-ui;margin:16px 0 0;opacity:.9}
  @keyframes __in{from{transform:translateY(24px);opacity:0}to{transform:none;opacity:1}}
  @keyframes __fade{from{opacity:0}to{opacity:1}}`;
  let root = document.getElementById('__pitch');
  if(!root){ root = document.createElement('div'); root.id='__pitch'; const st=document.createElement('style'); st.textContent=css; root.appendChild(st);
    root.insertAdjacentHTML('beforeend','<div class="bar"></div><div class="clock"></div><div class="slot"></div>'); document.body.appendChild(root); }
  root.querySelector('.bar').style.width = Math.min(100, elapsed/total*100) + '%';
  const mm = s => Math.floor(s/60) + ':' + String(Math.floor(s%60)).padStart(2,'0');
  root.querySelector('.clock').textContent = mm(elapsed) + ' / ' + mm(total);
  const slot = root.querySelector('.slot');
  if(end){ slot.innerHTML = '<div class="endcard"><div><h1>Tenke<span>makker</span></h1><p></p></div></div>'; slot.querySelector('p').textContent = end; return; }
  if(slot.dataset.i !== String(i)){
    slot.dataset.i = String(i);
    slot.innerHTML = '<div class="lt"><div class="k"><b></b><span></span></div><p class="t"></p><p class="l"></p></div>';
    slot.querySelector('.k b').textContent = (i+1) + '/' + n;
    slot.querySelector('.k span').textContent = kicker;
    slot.querySelector('.t').textContent = title;
    slot.querySelector('.l').textContent = line;
  }
}
"""


class Pitch:
    def __init__(self, page, lang):
        self.p, self.lang, self.beats, self.txt = page, lang, BEATS[lang], TEXT[lang]
        self.t0 = time.time(); self.i = 0; self.beat_end = 0

    def elapsed(self):
        return time.time() - self.t0

    def overlay(self, end=None):
        k, ti, li = self.beats[self.i][1:]
        try:
            self.p.evaluate(OVERLAY_JS, {"i": self.i, "n": len(self.beats), "kicker": k, "title": ti, "line": li,
                                         "elapsed": min(self.elapsed(), TOTAL), "total": TOTAL, "end": end})
        except Exception:
            pass

    def wait(self, s):
        """Wait s seconds, keeping the overlay clock ticking."""
        end = time.time() + s
        while time.time() < end:
            self.overlay()
            self.p.wait_for_timeout(int(min(0.25, max(0.01, end - time.time())) * 1000))

    def beat(self, i):
        self.i = i
        self.beat_end = sum(b[0] for b in self.beats[:i + 1])
        self.overlay()

    def finish_beat(self):
        """Pad so each beat ends exactly on its scripted second."""
        rest = self.beat_end - self.elapsed()
        if rest > 0:
            self.wait(rest)

    def click(self, sel):
        loc = self.p.locator(sel).first
        loc.scroll_into_view_if_needed(); self.wait(0.3); loc.click(); self.overlay()

    def type(self, sel, text, delay=40):
        loc = self.p.locator(sel).first
        loc.scroll_into_view_if_needed(); loc.click(); loc.fill(""); loc.type(text, delay=delay); self.overlay()

    def wait_makker(self, before, timeout=8):
        end = time.time() + timeout
        while time.time() < end:
            if self.p.locator("#chat .msg.m:not(.thinking)").count() > before and self.p.locator("#chat .thinking").count() == 0:
                return
            self.wait(0.2)

    def mcount(self):
        return self.p.locator("#chat .msg.m:not(.thinking)").count()

    def top(self):
        self.p.evaluate("window.scrollTo({top:0,behavior:'smooth'})")

    def run(self):
        p, txt = self.p, self.txt
        # 1. Problem
        self.beat(0); self.wait(2.5)
        p.locator("#task-text").scroll_into_view_if_needed(); self.finish_beat()
        # 2. Help, not answers
        self.beat(1)
        b = self.mcount(); self.click("#stuck"); self.wait_makker(b); self.wait(2.2)
        b = self.mcount(); self.click("#chips button"); self.wait_makker(b); self.finish_beat()
        # 3. Mistakes are free
        self.beat(2)
        self.type("#answer", "3/7", 110); self.click("#answer-form button[type=submit]"); self.wait(2.4)
        self.type("#answer", "11/12", 110); self.click("#answer-form button[type=submit]"); self.finish_beat()
        # 4. Teach Makker
        self.beat(3); self.wait(2.5)
        if p.locator("#teach").is_visible():
            self.type("#explain", txt["explain"], 38)
            b = self.mcount(); self.click("#send"); self.wait_makker(b)
        self.finish_beat()
        # 5. The class
        self.beat(4)
        if p.locator("#tab-elev").is_visible():
            p.locator("#lower").scroll_into_view_if_needed()
        else:
            self.click(".bottomnav button[data-v=klasse]")
        self.wait(2.5); self.click("#m-tog"); self.wait(3); self.click("#m-vs"); self.finish_beat()
        # 6. Practise anything
        self.beat(5); self.top(); self.wait(0.8)
        if not p.locator("#topic-form").is_visible():
            self.click(".new-topic")
        self.type("#topic", txt["topic"], 55); self.click("#make-task")
        try:
            p.wait_for_function("() => document.querySelector('#topic-form').hidden", timeout=7000)
        except Exception:
            pass
        self.top(); self.finish_beat()
        # 7. Parents and teachers
        self.beat(6)
        self.click("#tab-forelder") if p.locator("#tab-forelder").is_visible() else self.click(".bottomnav button[data-v=forelder]")
        self.wait(5.2)
        self.click("#tab-laerer") if p.locator("#tab-laerer").is_visible() else self.click(".bottomnav button[data-v=laerer]")
        self.wait(2.5); p.mouse.wheel(0, 300); self.finish_beat()
        # 8. 2030
        self.beat(7); self.top(); self.wait(0.3)
        self.click(".vision-link"); p.wait_for_load_state("domcontentloaded"); self.overlay()
        for _ in range(4):
            self.wait(1.2); p.keyboard.press("ArrowRight")
        # end card for the last ~3 s
        rest = self.beat_end - self.elapsed() - 3
        if rest > 0: self.wait(rest)
        end = time.time() + max(0.5, self.beat_end - self.elapsed())
        while time.time() < end:
            self.overlay(end=txt["end"]); p.wait_for_timeout(200)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://tenkemakker.ethlo.com/")
    ap.add_argument("--lang", choices=["nb", "en"], default="nb")
    ap.add_argument("--show", action="store_true", help="show the browser while recording")
    ap.add_argument("--login", action="store_true", help="log in to tenkemakker.ethlo.com once, then exit")
    a = ap.parse_args()
    size = {"width": 1280, "height": 720}
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_raw_pitch"; shutil.rmtree(tmp, ignore_errors=True)
    with sync_playwright() as pw:
        if a.login:
            ctx = pw.chromium.launch_persistent_context(str(PROFILE), headless=False, viewport=size)
            page = ctx.pages[0] if ctx.pages else ctx.new_page(); page.goto(a.url)
            input("\nLog in in the browser window, then press Enter here … "); ctx.close(); return
        ctx = pw.chromium.launch_persistent_context(str(PROFILE), headless=not a.show, viewport=size,
                                                    record_video_dir=str(tmp), record_video_size=size)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        t_launch = time.time()
        page.goto(a.url); page.wait_for_timeout(1200)
        if "cloudflareaccess.com" in page.url or not page.locator("#task-text").count():
            ctx.close(); sys.exit("Not logged in. Run once with --login first.")
        page.evaluate(f"() => {{ try{{ localStorage.setItem('tenkemakker-lang','{a.lang}'); }}catch(e){{}} }}")
        page.reload(); page.wait_for_timeout(1200)
        # turn read-aloud off so the presenter's voice isn't competing
        page.evaluate("() => { const t=document.getElementById('speak-toggle'); if(t) t.checked=false; }")
        video = page.video
        pitch = Pitch(page, a.lang)
        try:
            pitch.run()
        finally:
            t_end = time.time()
            ctx.close()
        dst = OUT / f"tenkemakker-pitch-{a.lang}.webm"
        shutil.move(str(Path(video.path())), dst); shutil.rmtree(tmp, ignore_errors=True)
        print(f"Video: {dst}  (beats ended at {pitch.elapsed():.1f} s)")
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            mp4 = dst.with_suffix(".mp4")
            # The browser recorder runs slower than real time: stretch the video back to wall-clock
            # time, then cut away the page load before the pitch so the result is exactly TOTAL seconds.
            real = t_end - t_launch
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dst)],
                                       capture_output=True, text=True).stdout.strip() or real)
            factor = real / dur if dur > 0 else 1.0
            lead = max(0.0, pitch.t0 - t_launch)
            vf = f"setpts=PTS*{factor:.5f},trim=start={lead:.2f}:duration={TOTAL},setpts=PTS-STARTPTS"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(dst), "-vf", vf, "-an", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", str(mp4)], check=False)
            if mp4.exists(): print("Video:", mp4)


if __name__ == "__main__":
    main()
