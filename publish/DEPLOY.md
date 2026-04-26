# Deploy-Anleitung — private-ai-bridge Landing Page

> Für die Session/Person, die das Deployment auf den eigenen Server übernimmt.

## Was ist in diesem Ordner?

Der Ordner `publish/` enthält **alles, was auf den öffentlichen Webserver kommt**.
Drei statische HTML-Seiten plus CSS — komplett selbsterklärend, keine Build-Tools, keine Datenbank, kein Backend.

```
publish/
├── DEPLOY.md         # diese Datei (kommt nicht auf den Server)
├── index.html        # Landing Page (Konzept, Architektur, Features)
├── demo.html         # Live-Demo mit Wintersportwoche-Beispiel
├── flow.html         # Datenfluss-Visualisierung
└── css/
    └── style.css     # Geteiltes Stylesheet
```

Alles andere im Repo (`server/`, `examples/`, `install.sh` etc.) ist Server-/Tooling-Code und gehört NICHT auf den öffentlichen Server.

## Was sind diese Seiten?

**Landing Page für eine Open-Source-Veröffentlichung von Thomas Schroffenegger, MSc MAS BEd.**

Das Projekt heißt **private-ai-bridge** und ist ein Framework, das Claude Code DSGVO-konform macht: Personenbezogene Daten werden lokal mit Gemma 4 (via Ollama) gefiltert, bevor sie an die Cloud gehen. Claude bekommt nur anonymisierte Aggregate.

Zielgruppe: Schul-Direktor*innen, Verwaltungsleitungen, IT-Verantwortliche in Bereichen mit personenbezogenen Daten (Schule, Personal, Recht, Sozialarbeit). Konzept ist universell, Demo am Beispiel Wintersportwoche.

## Deployment-Optionen

### Option 1: Apache (XAMPP) im Unterverzeichnis

Wenn die Webseite unter `https://deinedomain.tld/private-ai-bridge/` erreichbar sein soll:

```bash
# Auf dem Server:
cd /var/www/html      # oder /Applications/XAMPP/xamppfiles/htdocs/
git clone https://github.com/harubert/private_ai_bridge.git
# Symlink auf publish/ damit die URL kurz und sauber ist:
ln -s private_ai_bridge/publish private-ai-bridge
# Erreichbar unter: https://deinedomain.tld/private-ai-bridge/
```

Updates:
```bash
cd /var/www/html/private_ai_bridge && git pull
```

### Option 2: Eigene Subdomain mit Apache vhost

Wenn die Seite unter eigener Subdomain laufen soll (z.B. `https://privacy.deinedomain.tld/`):

```apache
<VirtualHost *:443>
    ServerName privacy.deinedomain.tld
    DocumentRoot /var/www/private_ai_bridge/publish

    <Directory /var/www/private_ai_bridge/publish>
        AllowOverride All
        Require all granted
    </Directory>

    SSLEngine on
    SSLCertificateFile /pfad/zu/cert.pem
    SSLCertificateKeyFile /pfad/zu/key.pem
</VirtualHost>
```

### Option 3: nginx

```nginx
server {
    server_name privacy.deinedomain.tld;
    root /var/www/private_ai_bridge/publish;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    listen 443 ssl;
    # ... ssl_certificate etc.
}
```

### Option 4: Nur die Dateien hochladen (FTP/rsync)

Wenn du keinen Git-Zugriff auf dem Server hast:

```bash
# Auf deinem lokalen Rechner:
rsync -avz --exclude=DEPLOY.md \
  /pfad/zu/private_ai_bridge/publish/ \
  user@server:/var/www/html/private-ai-bridge/
```

(Die `DEPLOY.md` wird ausgeschlossen, weil sie nicht öffentlich gehört.)

## Struktur der Seite

| URL | Inhalt | Zweck |
|-----|--------|-------|
| `/` | Landing Page (index.html) | Konzept erklären, Architektur zeigen, Schnellstart, Über das Projekt |
| `/demo.html` | Live-Demo | Schritt-für-Schritt durchgespielt am Beispiel "Wintersportwoche planen" |
| `/flow.html` | Datenfluss | Visualisierung welche Daten wo bleiben, Sicherheitsstufen, Timeline |

Alle drei Seiten sind über die Sticky-Navbar oben verlinkt.

## Wichtige externe Links auf der Seite

- **GitHub-Repo**: `https://github.com/harubert/private_ai_bridge` (in der Topnav rechts und im Footer)
- **About-Sektion** auf index.html: Autor, Erstveröffentlichung April 2026, Lizenzen

## Was die Seite NICHT braucht

- Keine Datenbank
- Kein PHP, kein Node.js auf dem Server
- Keine Build-Pipeline (kein npm, kein Webpack)
- Kein Backend — alles statisch HTML/CSS/JS

## Lokale Vorschau (vor dem Deployment)

```bash
cd publish && python3 -m http.server 8090
# Browser: http://localhost:8090
```

## Updates / neue Inhalte

Updates am Konzept passieren im Hauptrepo (`main`-Branch). Auf dem Server reicht `git pull` — keine weitere Aktion nötig (statische Seiten).

Falls neue Seiten dazukommen, muss die Topnav in **allen drei** HTML-Seiten ergänzt werden (jede Seite hat ihre eigene Navbar inline — bewusst kein Build-System).

## Lizenzhinweis

Die Webseite ist unter **CC BY-SA 4.0** lizenziert (siehe LICENSE-DOCS im Repo-Root).

Beim Deployment auf einem Drittserver oder bei Forks bitte:
- Namensnennung **Thomas Schroffenegger, MSc MAS BEd** beibehalten
- Footer und About-Sektion nicht entfernen
- Bei Modifikationen ebenfalls unter CC BY-SA 4.0 weitergeben

## Kurz-Brief für die andere Claude-Session

> Klone das Repo (`git clone https://github.com/harubert/private_ai_bridge.git`), deploye den Inhalt von `publish/` (3 HTML-Dateien + css/) als statische Seite auf einen Webserver. Keine Build-Tools, kein Backend — alles direkt einsatzbereit. Die DEPLOY.md selbst gehört nicht ins Web-Root (ist nur die Anleitung).
