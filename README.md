### SL prodajni klicni bot (Twilio Voice)

Node.js strežnik, ki izvede odhodni klic v slovenščini, vodi razgovor s TTS glasom in prepoznavanjem govora ter obravnava ugovore za prodajo storitev za spletne strani.

#### Opozorilo in odgovornost
- Uporaba avtomatiziranih klicev je pravno občutljiva. Preverite veljavno zakonodajo (GDPR, ZEPT, TCPA/ekvivalenti), pravila Twilia in morebitne zahteve za predhodno privolitev. 
- Vedno se predstavite in omogočite takojšnjo prekinitev klica. 
- Uporabljajte le številke in kontakte, za katere imate legitimno podlago za kontakt.

#### Zahteve
- Node.js >= 18
- Twilio račun (Account SID, Auth Token) in preverjena odhodna številka (`TWILIO_CALLER_NUMBER`).
- Javno dosegljiv URL za webhooke (`PUBLIC_BASE_URL`), npr. preko ngrok.

#### Namestitev
1. Kopirajte `.env.example` v `.env` in izpolnite vrednosti.
2. Namestite odvisnosti:
   ```bash
   npm install
   ```
3. Zaženite lokalno:
   ```bash
   npm run dev
   ```
4. Expose localhost preko ngrok (primer):
   ```bash
   ngrok http 3000
   ```
   Nastavite `PUBLIC_BASE_URL` na posredovani HTTPS URL.

#### Twilio nastavitev
- Ni potrebno predhodno nastavljati webhookov v konzoli, ker odhodni klic uporablja dinamiko `url` parametra (`/voice/answer`).
- Preverite, da je `TWILIO_CALLER_NUMBER` dovoljeno za klicanje ciljne številke (regijske omejitve).

#### Uporaba API-ja
- Inicializirajte klic:
  ```bash
  curl -X POST "$PUBLIC_BASE_URL/api/call" \
    -H "Content-Type: application/json" \
    -d '{
      "companyName": "Podjetje d.o.o.",
      "phoneNumber": "+38640123456"
    }'
  ```
- Odziv vrne `callId` in Twilio `sid`.

#### Kaj bot počne
- Uvod in kvalifikacija (sl-SI).
- Dve glavni poti: brez spletne strani ali nadgradnja obstoječe.
- Obvladovanje pogostih ugovorov (čas, cena, že imamo partnerja, pošljite e‑pošto, ne zanima, pokličite kasneje).
- Poskus dogovora termina, sicer vljudna zaključitev.

#### Glas in jezik
- `TWILIO_LANGUAGE=sl-SI` za ASR. 
- `TWILIO_VOICE`: Twilio posreduje Amazon Polly glasove; izberite glas, ki podpira slovenščino (npr. posodobite glede na aktualno ponudbo). Če glas ne podpira slovenščine, razmislite o Twilio Voice <Say> brez Polly ali znebičnem TTS preko <Play> (napredna integracija).

#### Varnost
- Nastavite `WEBHOOK_AUTH_TOKEN` in ga podajte kot `token` query parameter. 
- Omejite dostop do API-ja po potrebi (npr. dodatna avtentikacija, IP filtriranje).

#### Opombe
- Shramba stanja je v pomnilniku (Map). Za produkcijo uporabite podatkovno bazo (Redis, Postgres).
- Klici in prepis govora lahko stanejo. Spremljajte stroške v Twilio konzoli.

---

### EN quick overview
- Express server exposes `/api/call` to place an outbound call via Twilio.
- Webhooks (`/voice/*`) return TwiML, drive a Slovenian script with objection handling and scheduling attempt.
- Configure `.env`, run `npm run dev`, expose via ngrok, POST to `/api/call`.