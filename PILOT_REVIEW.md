# Kritisk gjennomgang av Brøkverkstedet — 21. oktober 2026

## Konklusjon

De påviste feilene som kunne forstyrre en lokal pilot er rettet og testet.
Anbefalt neste steg er en liten pilot i lokal øvingsmodus med voksenoppfølging.
Dette er teknisk og faglig gjennomgang av prototypen, ikke dokumentasjon av
læringseffekt eller godkjenning av KI-veiledning med ekte elevtekst.

Utgangspunkt: PR #6, commit 4eaf21e. Endringene er begrenset til Brøkverkstedet,
regresjonstester og dokumentasjon; hovedoppgaver og lærerens poengoversikt er bevart.

## Forløpet som ble gjennomgått

| Steg | Status etter retting | Kontroll |
|---|---|---|
| 1. Første oppgave og hint | Bestått | Eksakt brøkregning, feilformat, ulike svar, hjelp og uavklart videreføring. Siste hint beholder tastaturfokus; hvert hint kan leses opp. |
| 2. Strimler, tallinje og symboler | Bestått | Alle valg 2–24, ugyldige valg, nevner 12/24 og 10/20, bevart mengde, lik helhet, markering og omskriving. |
| 3. Forklaring til Makker | Bestått lokalt og med simulerte KI-svar | Tekst, lokale spørsmål, språk, lange/tomme svar, avbrudd og forsinkede svar. Ekte KI-kvalitet ikke undersøkt. |
| 4. Ny oppgave | Bestått | 1/2 + 1/5 starter med egen støttehistorikk. Modell, nevner og hint nullstilles. Både løst og uavklart utgang testet. |
| 5. Oppsummering og eksport | Bestått | Tidligere forsøk forblir uendret. Riktig svar skilles fra uavklart, og støtte fra forståelse. Tekstinnholdet i eksporten opplyses. |
| 6. Foreldrevisning | Bestått | Eget kort uten elevens fritekst. Ingen poeng eller lærerresultater fra verkstedet blandes inn i hovedoppgavene. |
| 7. Senere oppgave og utskrift | Bestått teknisk | 1/3 + 1/6 på separat ark, uten elevtekst. Printvisning og tilbakeføring kontrolleres i nettlesertesten; fysisk skriver er ikke testet. |

## Funn som er rettet

1. **Uklart hvilken nevner modellen bruker (steg 2).** Feltet kunne vise 24 mens
   modellen og omskrivingen fortsatt viste 12. Nå viser en melding gjeldende
   inndeling, og omskrivingen kan ikke kontrolleres før det nye valget er brukt.
   Instruksjonen navngir nevneren i modellen. Samme valg en gang til bevarer arbeidet.
   En egen knapp viser de opprinnelige delene igjen.
2. **For små markeringstreff på mobil (steg 2).** Ved 24 deler var hver del ca.
   10,7 px bred ved 390 px skjermbredde. En mer romslig velger og knapp (minst
   44 px høy) kan nå markere nøyaktig samme del. Mørk prikk på ufylt område er
   synlig; markering endrer ikke mengdefargen. Tastatur fungerer i begge metodene.
3. **Forsinkede KI-svar stjal fokus (steg 3).** Svaret flyttet fokus til
   forklaringsfeltet selv når eleven skrev i nevnerfeltet. Aktivt felt, skrivemerke
   og leseposisjon bevares nå. Også navigasjonskontroller og samtaleloggen er testet.
4. **Ubrukelig KI-tekst ble vist som veiledning (steg 3).** Bare mellomrom kunne
   bli en tom boble. Tomme svar og svar over 1200 tegn gir nå tydelig lokal
   reserveveiledning. Dette er en formatkontroll, ikke en faglig godkjenning av KI.
5. **Hint og tale hadde hull i betjeningen (steg 1–3).** Tredje hint gjorde knappen
   deaktivert og sendte tastaturfokus til BODY. Fokus går nå til selve hintet.
   Hvert hint kan leses opp, og verkstedets opplesning stoppes når fanen forlates.
6. **Sluttsidens opplesning endret oppgaveregistreringen (steg 5–7).** Opplesning
   av neste dags oppgave ble ført som støtte til oppgaven som allerede var avsluttet.
   Nå registreres den separat i `summaryReadAloud`; oppgaver og forsøk er uendret.
7. **Konsekvensene av tekst og eksport var lite synlige (steg 3 og 5).** Det vises
   nå når en kladd ikke er sendt, og at nedlastingen inneholder elevens skrevne svar
   og forklaringer. Foreldrekortet viser fortsatt ikke denne teksten. «Uten støtte»
   er presisert til støtte åpnet i verkstedet; voksenhjelp registreres manuelt.

## Verifikasjon

- 178 integrasjonskontroller + 561 kontroller av det sammenhengende forløpet +
  94 nye kontroller fra denne gjennomgangen = **833 beståtte nettleserkontroller**.
- Worker-kontrakttester og `git diff --check` bestått. Ingen live KI-kall i testene.
- Norsk/engelsk, mobil 390 px, lys/mørk visning, skrivebord, tastatur, følsomme
  overganger, eksport, reserveveiledning og utskrift er dekket. Skjermbilder fra
  den faktiske Codex-forhåndsvisningen er kontrollert i denne gjennomgangen.
- Konkrete reproduksjoner før retting: nevnerfelt 24 med modell 12; 10,65625 px
  brede markeringstreff; fokus på BODY etter siste hint; sluttsidens opplesning
  endret andre oppgaves `readAloud` fra [] til ["question"].
- Ingen tester eller varsler er undertrykt. Ingen nye avhengigheter er installert.

## Det som fortsatt må undersøkes

- Kvaliteten på ekte KI-svar, inkludert om fasit kan avsløres. Første elevpilot
  bruker derfor lokal øvingsmodus som avtalt; ingen KI-vurdering av eleven.
- Hørbar lydkvalitet på enhetene som faktisk skal brukes. Taleadaptere prøver
  kontrollflyten, men erstatter ikke å lytte. Lesing på skjermen er tilgjengelig.
- Bruk med faktisk skjermleser og deltakere med ulike tilgjengelighetsbehov.
  Tastatur/etiketter og visuell kontroll er ikke en full WCAG-sertifisering.
- Om den relativt lange mobilsiden og selve begrepene er lette for elevene å
  forstå. Behold layouten i første pilot; noter leting og behov for voksenforklaring.
- Elevpilot, læring over tid, publisering og innlogget produksjonskontroll er ikke
  gjennomført. Utskriften er manuell; appen kan ikke måle senere læring alene.

Se PILOT.md for observasjonsopplegg. Skjermbilder og en lesbar lokal rapport ligger
under Learning Ways/output/tenkemakker-pilot-audit/. Bildene er fra denne runden,
ikke gjenbrukte bilder fra implementeringen.
