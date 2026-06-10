# Runbook — n8n self-hosted su Hetzner CX22 (Fase 2, dal 3° cliente)

Costo fisso: **€4,51/mese** per tutti i clienti. Tempo di setup: 3–4 ore. Migrazione del 1° cliente da Make: 6–8 ore una tantum.

## 1. Provisioning

1. Account su Hetzner Cloud (console.hetzner.cloud) + **2FA attivata subito**
2. Nuovo progetto → Add Server:
   - Location: **Falkenstein o Nuremberg** (Germania → dati in UE, coerente col DPA)
   - Image: **Ubuntu 24.04**
   - Type: **CX22** (2 vCPU, 4 GB RAM, 40 GB SSD)
   - SSH key: carica la tua chiave pubblica (mai password)
3. DNS: record A `n8n.[TUODOMINIO.IT]` → IP del server (TTL 300)

## 2. Hardening base (30 min)

```bash
# da root al primo accesso
adduser opsuser && usermod -aG sudo opsuser
rsync --archive --chown=opsuser:opsuser ~/.ssh /home/opsuser

# SSH: solo chiave, no root
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# firewall: solo SSH, HTTP, HTTPS
apt update && apt -y install ufw fail2ban unattended-upgrades
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable
dpkg-reconfigure -plow unattended-upgrades
```

## 3. Docker + stack n8n

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker opsuser
mkdir -p /opt/n8n && cd /opt/n8n
```

`/opt/n8n/.env` (genera i segreti con `openssl rand -hex 24`):

```env
POSTGRES_PASSWORD=[SEGRETO_1]
N8N_ENCRYPTION_KEY=[SEGRETO_2]
N8N_HOST=n8n.[TUODOMINIO.IT]
```

`/opt/n8n/docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n"]
      interval: 10s
      retries: 5

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: ${POSTGRES_PASSWORD}
      DB_POSTGRESDB_DATABASE: n8n
      N8N_HOST: ${N8N_HOST}
      N8N_PROTOCOL: https
      WEBHOOK_URL: https://${N8N_HOST}/
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
      GENERIC_TIMEZONE: Europe/Rome
      TZ: Europe/Rome
    volumes:
      - n8n_data:/home/node/.n8n

  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

volumes:
  postgres_data:
  n8n_data:
  caddy_data:
```

`/opt/n8n/Caddyfile` (TLS automatico Let's Encrypt):

```
n8n.[TUODOMINIO.IT] {
    reverse_proxy n8n:5678
}
```

Avvio: `docker compose up -d` → apri `https://n8n.[TUODOMINIO.IT]`, crea l'account owner con password robusta e **attiva la 2FA in n8n** (Settings → Personal → Two-factor).

## 4. Backup settimanale cifrato (retention 4 settimane)

`/opt/n8n/backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%F)
DIR=/opt/n8n/backups
mkdir -p "$DIR"
docker compose -f /opt/n8n/docker-compose.yml exec -T postgres pg_dump -U n8n n8n > "$DIR/db-$STAMP.sql"
docker run --rm -v n8n_n8n_data:/data -v "$DIR":/backup alpine tar czf "/backup/n8n-data-$STAMP.tar.gz" -C /data .
tar czf - -C "$DIR" "db-$STAMP.sql" "n8n-data-$STAMP.tar.gz" | gpg --batch --yes --symmetric --passphrase-file /root/.backup-pass -o "$DIR/n8n-backup-$STAMP.tar.gz.gpg"
rm "$DIR/db-$STAMP.sql" "$DIR/n8n-data-$STAMP.tar.gz"
# offsite: Hetzner Storage Box (BX11, €3,20/mese) o rclone verso cloud a scelta
rclone copy "$DIR/n8n-backup-$STAMP.tar.gz.gpg" storagebox:n8n-backups/ 2>/dev/null || true
find "$DIR" -name "*.gpg" -mtime +28 -delete
```

```bash
chmod +x /opt/n8n/backup.sh
echo "0 4 * * 0 /opt/n8n/backup.sh" | crontab -
```

**Test di restore ogni trimestre** (in calendario, non opzionale): scarica l'ultimo backup, decifra con gpg, ripristina su container locale, verifica che i workflow si aprano.

## 5. Aggiornamenti (1 volta al mese, 10 min)

1. Snapshot del VPS dalla console Hetzner (€0,012/GB/mese, cancellalo dopo)
2. `cd /opt/n8n && docker compose pull && docker compose up -d`
3. Apri n8n, esegui un test del workflow di un cliente con lead finto

## 6. Multi-tenancy

- 1 workflow per cliente: `Lead Response - [CLIENTE]` (duplicato dal template, vedi [`n8n/README.md`](n8n/README.md))
- **Credenziali separate per cliente** (SMTP, Telegram): se un cliente cessa, revochi le sue senza toccare gli altri
- Naming webhook: `/webhook/lead-[cliente]` — mai riusare path tra clienti
- Registro clienti (Google Sheet privato): cliente, path webhook, bot Telegram, casella SMTP, data attivazione, pacchetto

## 7. Migrazione del 1° cliente da Make (6–8h una tantum)

1. Importa il template in n8n e personalizza le variabili del cliente
2. Test end-to-end con lead finto sul nuovo webhook n8n
3. Cambia l'URL webhook nel form del cliente (Elementor/CF7/Gravity)
4. **Doppia esecuzione per 48h**: lascia attivo anche lo scenario Make (il form punta a n8n; Make resta come riferimento spento ma pronto al rollback)
5. Dopo 48h senza anomalie: disattiva lo scenario Make, downgrade/chiusura account Make
6. Aggiorna il registro clienti e l'elenco sub-responsabili se serve (il DPA già prevede Hetzner)
