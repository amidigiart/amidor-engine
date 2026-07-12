# Deploy AmiDor — arhitectură pe două niveluri (GDPR by design)

## Nivelul 1 — amidorai.com (public) = landing static, GitHub Pages, GRATUIT
Fața onestă a proiectului (RO/EN): ce e, ce NU e, cum funcționează motorul dual
și scam-shield-ul. Fără chat. Sursa: `docs/`.

**DNS în Cloudflare (norișor GRI = „DNS only", NU proxied — altfel certificatul GitHub nu se emite):**

| Type | Name | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | amidigiart.github.io |

Apoi GitHub → repo Settings → Pages → Custom domain: `amidorai.com`.

## Nivelul 2 — app.amidorai.com (privat) = aplicația, pe VPS Hetzner UE

Chat-ul cu vârstnici NU se expune public nesupravegheat. Instanța pilot rulează
cu `AMIDOR_ACCESS_CODE` — doar familiile care au primit codul intră.

### Conformitate GDPR — de ce Hetzner + aceste alegeri
- **Reședința datelor:** Hetzner = Germania/Finlanda (UE). Alege o locație UE.
- **Model A:** API UE (Mistral, Franța). **Model B:** rulat LOCAL pe VPS (Ollama),
  NU API-ul DeepSeek din China (ar fi transfer extra-UE fără temei). Ambele modele
  procesează în UE.
- **Voce:** piper (TTS) local pe VPS = nicio silabă nu pleacă. Fără piper,
  browserul face TTS/STT — dar interfața AFIȘEAZĂ nota de confidențialitate.
- **Jurnal:** semnat local, per instanță, DOAR cu consimțământul persoanei.
- **Alerte:** doar evenimentul (categoria de risc + ora), fără conținut de conversație.

### Pași (Hetzner CX32, ~€8/lună, Ubuntu 24.04, locație UE)

```bash
# 1. pe VPS
curl -fsSL https://get.docker.com | sh

# 2. codul
git clone https://github.com/amidigiart/amidor-engine && cd amidor-engine/deploy
cp .env.example .env && nano .env      # PIN real, cod acces, cheie Mistral, alerte

# 3. DNS: A record  app.amidorai.com -> IP-ul VPS-ului (in Cloudflare)

# 4. porneste (app + ollama local + caddy cu HTTPS automat)
docker compose up -d --build

# 5. o singura data: modelul local B
docker compose exec ollama ollama pull mistral

# 6. verifica
curl https://app.amidorai.com/api/health
```

### Resurse și scalare
- CX32 (4 vCPU/8GB): Model B (7-8B) pe CPU răspunde în ~15-60 s — ok pentru pilot.
- Creștere: GPU EU (Hetzner GEX44) pentru latență mică și mai mulți utilizatori.
- **Local-first recomandat:** o instanță per familie/cămin = zero date centralizate.

### Backup (jurnal semnat + chei notar + log alerte)
```bash
docker run --rm -v deploy_amidor_data:/d -v $PWD:/b alpine \
  tar czf /b/amidor-backup.tgz /d
```

### Checklist pilot cu familii reale
- [ ] `.env`: PIN schimbat, `AMIDOR_ACCESS_CODE` setat, cheie Model A, alerte configurate
- [ ] `AMIDOR_JOURNAL_CONSENT=true` DOAR după acordul explicit al persoanei
- [ ] locație Hetzner UE confirmată
- [ ] voce locală (piper) montată dacă se promite confidențialitate deplină
- [ ] o familie de test (poate una din Brăila) înainte de orice extindere
