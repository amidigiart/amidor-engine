# Acord de Confidențialitate pentru Acces Demo (NDA) / Demo Access Non-Disclosure Agreement

> **Notă onestă / Honest note:** acesta este un ȘABLON pregătit de proiect, nu
> consultanță juridică. Înainte de semnarea cu o contraparte reală, șablonul se
> revizuiește de un avocat. / This is a TEMPLATE prepared by the project, not
> legal advice. Have a lawyer review it before signing with a real counterparty.

---

## Română

**Între:**
- **Divulgator:** Mihai Roșca, cercetător independent, Brăila, România
  (contact@kinderagi.com) — autorul motorului REAI / amidor-engine;
- **Primitor:** ____________________________________________
  (nume complet / organizație, adresă, e-mail),

denumite împreună „Părțile".

### 1. Scopul
Divulgatorul acordă Primitorului acces de evaluare la **demonstrația privată**
a motorului REAI (inclusiv panoul live `/monitor` prin cod de acces personal,
instanțe pilot, discuții tehnice și comerciale), exclusiv pentru ca Primitorul
să evalueze o posibilă colaborare, licențiere sau finanțare.

### 2. Ce ESTE informație confidențială
a) codurile de acces la demo (ex. `MONITOR_ACCESS_CODE`) și orice instanță
privată la care Primitorul primește acces;
b) know-how nepublic împărtășit în sesiunile de demo (calibrări, configurări,
rezultate pe date pilot, arhitectura desfășurărilor private);
c) termenii comerciali discutați (prețuri, structuri de licență în negociere);
d) orice date ale utilizatorilor-pilot (protejate suplimentar de GDPR).

### 3. Ce NU este informație confidențială (declarat explicit)
a) **codul sursă publicat** al proiectului — `amidor-engine` e public sub
AGPL-3.0, `ukbe-core` sub Apache-2.0; NDA-ul nu restrânge drepturile acordate
de aceste licențe;
b) lucrarea științifică și reproducerea ei (DOI: 10.5281/zenodo.21269201);
c) informații devenite publice fără culpa Primitorului, cunoscute anterior de
Primitor, primite legal de la terți sau dezvoltate independent;
d) divulgări cerute de lege sau de o autoritate (cu notificare prealabilă a
Divulgatorului, unde legea permite).

### 4. Obligațiile Primitorului
a) folosește informația confidențială DOAR pentru scopul de la pct. 1;
b) nu dezvăluie codurile de acces și nu permite accesul terților la demo;
c) nu publică capturi de ecran / înregistrări ale demo-ului fără acord scris;
d) protejează informația cel puțin la fel de atent ca pe a sa proprie;
e) la cererea Divulgatorului, încetează accesul și șterge materialele nepublice
primite. Codul de acces este personal și poate fi revocat oricând.

### 5. Fără licență
Acest acord NU acordă nicio licență comercială, niciun drept de proprietate
intelectuală și niciun drept de utilizare în producție. Utilizarea comercială
closed-source a componentelor AGPL necesită licența comercială separată
(vezi `COMMERCIAL.md`).

### 6. Durata
Obligațiile de confidențialitate intră în vigoare la semnare și rămân valabile
**3 (trei) ani** de la ultima divulgare, indiferent de încetarea evaluării.

### 7. Legea aplicabilă și litigii
Acordul e guvernat de legea română. Litigiile se soluționează amiabil în 30 de
zile; altfel, de instanțele competente din România.

### 8. Semnături

| | Divulgator | Primitor |
|---|---|---|
| Nume | Mihai Roșca | ____________________ |
| Data | ____________ | ____________________ |
| Semnătura | ____________ | ____________________ |

---

## English (courtesy translation — the Romanian version prevails)

**Between** Mihai Roșca, independent researcher, Brăila, Romania
(contact@kinderagi.com), author of the REAI engine / amidor-engine
(the "Discloser"), and ______________________________ (the "Recipient").

1. **Purpose.** The Discloser grants the Recipient evaluation access to the
   **private demo** of the REAI engine (including the live `/monitor` panel via
   a personal access code, pilot instances, and technical/commercial
   discussions), solely to evaluate a potential collaboration, license, or
   funding.
2. **Confidential Information** includes: demo access codes and private
   instances; non-public know-how shared in demo sessions; commercial terms
   under negotiation; any pilot-user data (additionally protected by GDPR).
3. **Not confidential** (stated explicitly): the project's **published source
   code** (amidor-engine is public under AGPL-3.0, ukbe-core under Apache-2.0 —
   this NDA does not restrict rights granted by those licenses); the published
   paper and its reproduction (DOI: 10.5281/zenodo.21269201); information that
   is or becomes public without the Recipient's fault, was previously known,
   lawfully received from third parties, or independently developed; legally
   compelled disclosures (with prior notice where permitted).
4. **Recipient's obligations:** use Confidential Information only for the
   Purpose; do not share access codes or grant third parties demo access; no
   screenshots/recordings of the demo without written consent; protect the
   information with at least reasonable care; on request, cease access and
   delete non-public materials. The access code is personal and revocable at
   any time.
5. **No license.** This agreement grants no commercial license, no IP rights,
   and no production-use rights. Closed-source commercial use of AGPL
   components requires the separate commercial license (see `COMMERCIAL.md`).
6. **Term:** confidentiality obligations survive for **three (3) years** from
   the last disclosure.
7. **Governing law:** Romanian law; amicable resolution within 30 days, then
   the competent Romanian courts.
8. **Signatures:** Discloser: Mihai Roșca, date, signature / Recipient: name,
   date, signature.

---

### Procesul de acces demo / Demo access flow

1. Primitorul semnează acest NDA (PDF sau semnătură electronică) →
2. Divulgatorul emite un `MONITOR_ACCESS_CODE` **personal** pentru Primitor →
3. Accesul: `https://app.amidorai.com/monitor/?code=<cod>` (când instanța
   pilot e activă) sau demo ghidat pe instanța locală →
4. La finalul evaluării (sau la nevoie), codul se revocă prin schimbarea
   variabilei de mediu — un singur restart.
