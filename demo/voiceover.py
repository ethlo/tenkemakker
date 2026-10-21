#!/usr/bin/env python3
"""
Tenkemakker: add an ElevenLabs voice-over and background music to the 90-second pitch video.

Runs on your own machine with your own ElevenLabs key. Only Python's standard library
and ffmpeg are needed (no pip install).

    export ELEVENLABS_API_KEY=...            # your key; never commit it
    python3 voiceover.py                     # Norwegian: tenkemakker-pitch-nb.mp4 -> tenkemakker-pitch-nb-voice.mp4
    python3 voiceover.py --lang en
    python3 voiceover.py --list-voices       # pick a voice, then --voice <voice_id>
    python3 voiceover.py --no-music          # voice only
    python3 voiceover.py --fake              # test the mixing without calling ElevenLabs (beeps instead of speech)

Each beat's line is placed on the exact second the beat starts in pitch.py (0, 10, 22, 32, 46, 56, 66, 78 s).
Generated audio is cached in ./voiceover-cache, so re-running only re-mixes and costs nothing.
"""
import argparse, json, os, shutil, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.elevenlabs.io/v1"
TOTAL = 90.0
BEAT_LEN = [10, 12, 10, 14, 10, 10, 12, 12]          # must match demo/pitch.py
STARTS = [sum(BEAT_LEN[:i]) for i in range(len(BEAT_LEN))]

# Spoken lines, kept short enough to fit each beat (≈ 2.4 words per second)
LINES = {
 "nb": [
  "Dette er Ida, tretten år, med mattelekse. En vanlig KI løser den på to sekunder. Men hva lærer hun da?",
  "Med Tenkemakker får hun hjelp, ikke fasit. Står hun fast, får hun et spørsmål tilbake, og svarer med ett trykk, eller med stemmen.",
  "Feil svar koster ingenting. Færre hint gir flere poeng. Poengene er for å tenke, ikke for fart.",
  "Så bytter de roller. Makker tror svaret er tre sjudeler. Nå må Ida forklare. Å lære bort gir mest poeng, for det er der læringen sitter.",
  "Klassen kan konkurrere, eller jobbe mot et felles mål. Det valget hører hjemme hos skolen og foreldrene.",
  "Ida kan øve på hva hun vil. Hun skriver et tema, og KI lager en ny oppgave til henne.",
  "Forelderen ser mønsteret, ikke samtalen, og får et spørsmål til middagen. Læreren ser hva klassen misforstår, før prøven.",
  "I 2030 er KI overalt. Skal den tenke for barna, eller få dem til å tenke selv? Tenkemakker.",
 ],
 "en": [
  "This is Ida, thirteen, with her maths homework. An ordinary AI solves it in two seconds. But what does she learn?",
  "With Tenkemakker she gets help, not answers. When she's stuck, she gets a question back, and replies with one tap, or with her voice.",
  "Wrong answers cost nothing. Fewer hints earn more points. Points are for thinking, not speed.",
  "Then they swap roles. Makker thinks the answer is three sevenths. Now Ida has to explain. Teaching earns the most, because that's where learning sticks.",
  "The class can compete, or work towards a shared goal. That choice belongs with schools and parents.",
  "Ida can practise anything. She types a topic, and AI makes a new task for her.",
  "The parent sees the pattern, not the conversation, and gets a question for dinner. The teacher sees what the class gets wrong, before the test.",
  "By 2030, AI is everywhere. Will it think for children, or make them think for themselves? Tenkemakker.",
 ],
}
MUSIC_PROMPT = ("Warm, playful, optimistic instrumental background music for a short product pitch about an AI "
                "learning buddy for 13-year-olds. Light marimba and plucked synths, soft pads, gentle uplifting beat "
                "around 100 BPM, calm enough to sit under a voice-over, builds slightly towards the end, clean ending.")


def die(msg):
    sys.exit("\n" + msg)


def need_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} is not installed. On Ubuntu/Debian: sudo apt install ffmpeg")


def api(path, body=None, key=None, method="POST", accept="audio/mpeg"):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        die(f"ElevenLabs said {e.code} for {path}:\n{detail}")
    except urllib.error.URLError as e:
        die(f"Could not reach ElevenLabs: {e.reason}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def find_video(lang, given):
    if given:
        return Path(given)
    name = f"tenkemakker-pitch-{lang}.mp4"
    for c in (Path.cwd() / name, HERE / name, HERE / "out" / name):
        if c.exists():
            return c
    die(f"Could not find {name}. Make it with pitch.py first, or pass --video path/to/video.mp4")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=["nb", "en"], default="nb")
    ap.add_argument("--video", help="input video (default: tenkemakker-pitch-<lang>.mp4 next to this script or in ./out)")
    ap.add_argument("--voice", default="EXAVITQu4vr4xnSDxMaL", help="ElevenLabs voice_id (default: Sarah). See --list-voices")
    ap.add_argument("--model", default="eleven_multilingual_v2", help="TTS model id (e.g. eleven_multilingual_v2, eleven_v4)")
    ap.add_argument("--music-volume", type=float, default=0.22, help="music level under the voice, 0–1")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="ignore the cache and generate again")
    ap.add_argument("--fake", action="store_true", help="no API calls: beeps instead of speech, a hum instead of music")
    a = ap.parse_args()
    need_ffmpeg()

    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and not a.fake:
        die("Set your key first:  export ELEVENLABS_API_KEY=your_key   (or test with --fake)")

    if a.list_voices:
        data = json.loads(api("/voices", method="GET", key=key, accept="application/json"))
        for v in data.get("voices", []):
            labels = ", ".join(f"{k}: {x}" for k, x in (v.get("labels") or {}).items())
            print(f"{v['voice_id']}  {v['name']:<22} {labels}")
        return

    video = find_video(a.lang, a.video)
    cache = HERE / "voiceover-cache"; cache.mkdir(exist_ok=True)
    tag = "fake" if a.fake else f"{a.voice}-{a.model}"

    # 1. Voice clips, one per beat
    clips = []
    for i, text in enumerate(LINES[a.lang]):
        f = cache / f"{a.lang}-{tag}-{i + 1}.mp3"
        if a.fresh or not f.exists():
            if a.fake:
                secs = max(2.0, min(BEAT_LEN[i] - 1.0, len(text.split()) / 2.6))
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={440 + 40 * i}:duration={secs:.2f}",
                                "-af", "volume=0.3", str(f)], check=True)
            else:
                print(f"Voice {i + 1}/8 …")
                audio = api(f"/text-to-speech/{a.voice}?output_format=mp3_44100_128",
                            {"text": text, "model_id": a.model,
                             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}, key=key)
                f.write_bytes(audio)
        clips.append(f)

    # 2. Background music, exactly 90 s
    music = None
    if not a.no_music:
        music = cache / ("music-fake.mp3" if a.fake else "music.mp3")
        if a.fresh or not music.exists():
            if a.fake:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={TOTAL}",
                                "-af", "volume=0.5", str(music)], check=True)
            else:
                print("Music (can take a minute) …")
                audio = api("/music?output_format=mp3_44100_128",
                            {"prompt": MUSIC_PROMPT, "music_length_ms": int(TOTAL * 1000), "force_instrumental": True}, key=key)
                music.write_bytes(audio)

    # 3. Fit each clip inside its beat: speed up slightly if too long, then place it 0.3 s into the beat
    inputs, filters, labels = ["-i", str(video)], [], []
    for i, f in enumerate(clips):
        d = duration(f)
        room = BEAT_LEN[i] - 0.6
        tempo = min(1.25, d / room) if d > room else 1.0
        if d / max(tempo, 1e-6) > room + 0.05:
            print(f"Note: line {i + 1} is {d:.1f}s for a {BEAT_LEN[i]}s beat even at 1.25× speed; it will overlap the next beat a little.")
        delay = int((STARTS[i] + 0.3) * 1000)
        inputs += ["-i", str(f)]
        chain = f"[{i + 1}:a]aformat=sample_rates=44100:channel_layouts=stereo"
        if tempo > 1.0:
            chain += f",atempo={tempo:.3f}"
        chain += f",adelay={delay}|{delay}[v{i}]"
        filters.append(chain); labels.append(f"[v{i}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad=whole_dur={TOTAL},atrim=0:{TOTAL}[voice]")

    if music:
        m = len(clips) + 1
        inputs += ["-i", str(music)]
        filters.append(f"[{m}:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=whole_dur={TOTAL},atrim=0:{TOTAL},"
                       f"volume={a.music_volume},afade=t=in:d=1.5,afade=t=out:st={TOTAL - 3}:d=3[mus]")
        # duck the music while someone talks
        filters.append("[voice]asplit=2[vk][vm]")
        filters.append("[mus][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[ducked]")
        filters.append("[ducked][vm]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]")
    else:
        filters.append("[voice]alimiter=limit=0.95[out]")

    out = video.with_name(video.stem + ("-voice-fake" if a.fake else "-voice") + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
           "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL), "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print("Done:", out)


if __name__ == "__main__":
    main()
