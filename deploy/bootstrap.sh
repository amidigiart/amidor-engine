#!/usr/bin/env bash
# AmiDor — bootstrap pentru un VPS Hetzner PROASPAT (Ubuntu 24.04, locatie UE).
# Ruleaza ca root:  curl -fsSL https://raw.githubusercontent.com/amidigiart/amidor-engine/main/deploy/bootstrap.sh | bash
# Idempotent: poate fi rulat din nou fara sa strice nimic.
set -euo pipefail

echo "== [1/6] Docker =="
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

echo "== [2/6] Firewall (doar SSH + HTTP/HTTPS) =="
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH >/dev/null
  ufw allow 80/tcp  >/dev/null
  ufw allow 443/tcp >/dev/null
  yes | ufw enable  >/dev/null || true
fi

echo "== [3/6] Codul =="
if [ -d /opt/amidor-engine/.git ]; then
  git -C /opt/amidor-engine pull --ff-only
else
  git clone https://github.com/amidigiart/amidor-engine /opt/amidor-engine
fi
cd /opt/amidor-engine/deploy

echo "== [4/6] Configurarea (.env) =="
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "!! .env a fost creat din sablon. OPRESTE-TE si completeaza-l acum:"
  echo "!!   nano /opt/amidor-engine/deploy/.env"
  echo "!!   (PIN, AMIDOR_ACCESS_CODE, MODEL_A_KEY, MONITOR_ACCESS_CODE)"
  echo "!! Apoi ruleaza scriptul din nou."
  exit 0
fi
# prod refuza sa porneasca cu PIN-ul implicit — verificare timpurie, aici
if grep -q "schimba-ma-neaparat" .env; then
  echo "!! AMIDOR_FAMILY_PIN e inca cel implicit. Editeaza .env si ruleaza din nou."
  exit 1
fi

echo "== [5/6] Pornire (app + ollama + caddy cu HTTPS automat) =="
docker compose up -d --build

echo "== [6/6] Modelul local B (o singura data; poate dura cateva minute) =="
MODEL_B="$(grep -E '^MODEL_B_NAME=' .env | cut -d= -f2 | awk '{print $1}')"
docker compose exec -T ollama ollama pull "${MODEL_B:-mistral}"

echo ""
echo "== GATA =="
echo "Verifica:  curl -s https://app.amidorai.com/api/health"
echo "Monitor:   https://app.amidorai.com/monitor/?code=<MONITOR_ACCESS_CODE>"
echo "(DNS-ul A app.amidorai.com -> IP-ul acestui VPS trebuie setat in Cloudflare,"
echo " norisor GRI, altfel Caddy nu poate emite certificatul Let's Encrypt.)"
