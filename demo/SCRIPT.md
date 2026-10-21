# Tenkemakker – 90-sekunders presentasjon

Manus for den som snakker, og for videoen `demo/pitch.py` lager. Hvert punkt er ett «beat» i videoen, med samme tid og samme tekst på skjermen.
All data er oppdiktet. Ida er en oppdiktet elev.

| Tid | På skjermen | Si dette |
|---|---|---|
| **0:00–0:10** | Ida, 13 år · Matteleksa | «Dette er Ida, 13 år. Hun har matte i lekse. En vanlig KI kan løse den på to sekunder. Men hva lærer hun da? Ingenting.» |
| **0:10–0:22** | Hjelp, ikke fasit | «Med Tenkemakker får hun hjelp, ikke svaret. Står hun fast, får hun et spørsmål tilbake. Hun kan svare med ett trykk, eller med stemmen.» |
| **0:22–0:32** | Feil er gratis | «Feil svar koster ingenting. Riktig svar med færre hint gir flere poeng. Poengene er for å tenke, ikke for fart.» |
| **0:32–0:46** | Lær bort til Makker | «Så bytter de roller. Makker har misforstått – han tror svaret er 3/7. Nå må Ida forklare. Å lære bort gir mest poeng, fordi det er der læringen sitter.» |
| **0:46–0:56** | Mot hverandre – eller sammen? | «Klassen kan konkurrere, eller jobbe mot et felles mål. Det er et valg vi mener skoler og foreldre bør ta – ikke appen.» |
| **0:56–1:06** | Øv på hva som helst | «Ida kan øve på hva hun vil. Hun skriver et tema, og KI lager en ny oppgave med hint og en misforståelse hun skal rydde opp i.» |
| **1:06–1:18** | Forelder og lærer ser mønsteret | «Forelderen ser mønsteret, ikke samtalen, og får et spørsmål til middagen. Læreren ser hva klassen misforstår – før prøven.» |
| **1:18–1:30** | 2030 | «I 2030 er KI overalt. Spørsmålet er om den tenker for barna, eller får dem til å tenke selv. 64 675 elever i Oslo. Tenkemakker.» |

**Kjernebudskap i én setning:** KI som får barn til å tenke selv – hjelp i små steg, aldri fasit, og mest poeng for å forklare.

---

# Tenkemakker – 90-second pitch (English)

| Time | On screen | Say this |
|---|---|---|
| **0:00–0:10** | Ida, 13 · Maths homework | "This is Ida, 13. She has maths homework. An ordinary AI can solve it in two seconds. But what does she learn? Nothing." |
| **0:10–0:22** | Help, not answers | "With Tenkemakker she gets help, not the answer. When she's stuck, she gets a question back. She can reply with one tap, or with her voice." |
| **0:22–0:32** | Mistakes are free | "Wrong answers cost nothing. A right answer with fewer hints earns more points. Points are for thinking, not speed." |
| **0:32–0:46** | Teach Makker | "Then they swap roles. Makker got it wrong – he thinks the answer is 3/7. Now Ida has to explain. Teaching earns the most, because that's where learning sticks." |
| **0:46–0:56** | Compete – or together? | "The class can compete, or work towards a shared goal. That's a choice we think schools and parents should make – not the app." |
| **0:56–1:06** | Practise anything | "Ida can practise anything. She types a topic, and AI makes a new task with hints and a misunderstanding for her to untangle." |
| **1:06–1:18** | Parents and teachers see the pattern | "The parent sees the pattern, not the conversation, and gets a question for dinner. The teacher sees what the class gets wrong – before the test." |
| **1:18–1:30** | 2030 | "By 2030 AI is everywhere. The question is whether it thinks for children, or makes them think. 64,675 pupils in Oslo. Tenkemakker." |

## Make the video

```bash
pip install playwright && playwright install chromium     # once
python3 demo/pitch.py --login                             # once, for tenkemakker.ethlo.com
python3 demo/pitch.py                                     # Norwegian, 1280×720, ~90 s
python3 demo/pitch.py --lang en
python3 demo/pitch.py --url file:///path/to/index.html    # local file, no login, practice mode
```

The video is saved as `demo/out/tenkemakker-pitch-<lang>.webm` (and `.mp4` if ffmpeg is installed).
Tip: the local file (practice mode) gives the most predictable video. The live site uses real Claude, so the words vary and replies can take a few seconds.

## Voice-over and music (ElevenLabs)

```bash
export ELEVENLABS_API_KEY=...        # your own key, never committed
python3 demo/voiceover.py            # tenkemakker-pitch-nb.mp4 -> tenkemakker-pitch-nb-voice.mp4
python3 demo/voiceover.py --lang en
python3 demo/voiceover.py --list-voices   # then --voice <voice_id>
```

One spoken line per beat (shortened versions of the lines above), placed on the beat's start second, plus 90 s of instrumental music that ducks under the voice. Audio is cached in `demo/voiceover-cache/`, so re-runs only re-mix.
