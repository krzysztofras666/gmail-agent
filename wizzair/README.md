# Wizz Air Multipass

CLI, który loguje się do [Wizz Multipass](https://multipass.wizzair.com) i wyszukuje dostępne loty **All You Can Fly** z wybranych lotnisk.

## Szybki start

```bash
cd wizzair
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # uzupełnij WIZZAIR_EMAIL i WIZZAIR_PASSWORD
python -m wizzair login --headed
python -m wizzair doctor
python -m wizzair send --dry-run
```

## Komendy

```bash
python -m wizzair run
python -m wizzair send                 # poranny pełny mail + snapshot
python -m wizzair send-delta           # popołudniowy mail tylko ze zmianami
python -m wizzair send --dry-run
python -m wizzair send-delta --dry-run
python -m wizzair preview-email --out logs/last_email.html
python -m wizzair preview-delta --out logs/last_delta_email.html
python -m wizzair doctor              # sprawdź .env, Gmail, sesję i harmonogram
```

## Harmonogram e-maili (macOS launchd)

| Godzina | Co robi |
| --- | --- |
| **08:00** | Pełny HTML z wszystkimi lotami i linkami |
| **13:00** | Tylko zmiany względem porannego maila (+ nowe, − zniknięte) |

Domyślni odbiorcy:
- `katarzyna.dyngosz@gmail.com`
- `andalath@gmail.com`

### Jednorazowa konfiguracja Gmail

```bash
cd ~/gmail-agent
source .venv/bin/activate
pip install -r requirements.txt
python -m gmail_agent auth --account andalath@gmail.com
```

### Wyślij ręcznie

```bash
cd ~/travel-agent/wizzair
source .venv/bin/activate
python -m wizzair send --dry-run          # poranny podgląd
python -m wizzair send                    # poranny mail
python -m wizzair send-delta --dry-run    # popołudniowy podgląd zmian
python -m wizzair send-delta              # popołudniowy mail (tylko jeśli są zmiany)
```

### Zaplanuj codziennie 08:00 i 13:00

**Bez tego kroku maile nie wyślą się automatycznie.** Harmonogram działa tylko na Macu.

```bash
cd ~/travel-agent/wizzair
chmod +x scripts/*.sh
./scripts/install_wizzair_schedule.sh
python -m wizzair doctor
./scripts/run_wizzair_morning.sh --dry-run
./scripts/run_wizzair_afternoon.sh --dry-run
```

Sprawdzenie, czy harmonogram jest aktywny:

```bash
launchctl print "gui/$(id -u)/com.wizzair.daily"
```

Jeśli widzisz `Could not find service` — harmonogram nie jest zainstalowany.

Logi:
- `logs/wizzair_morning.log`
- `logs/wizzair_afternoon.log`
- `logs/last_email.html`
- `logs/last_delta_email.html`
- `logs/snapshots/YYYY-MM-DD-morning.json`

## Jak działa

1. Loguje się na Multipass i skanuje loty z **KRK** i **KTW** (dziś + 3 dni)
2. O **08:00** wysyła pełny HTML z linkami przy każdej ofercie:
   - **Rezerwuj w Multipass**
   - **Zobacz na wizzair.com**
3. Zapisuje snapshot poranny do `logs/snapshots/`
4. O **13:00** skanuje ponownie i wysyła mail **tylko ze zmianami**:
   - nowe loty od rana
   - loty, które zniknęły
5. Jeśli o 13:00 nie ma zmian — mail nie jest wysyłany
6. Lot jest uznawany za dostępny **tylko**, gdy karta wyniku w UI zawiera:
   - przycisk **WYBIERZ**
   - kod lotu **W6…**
   - nazwę/kod właściwej destynacji (np. Rodos/RHO)
   - cenę w **zł**

## Jak skrócić skan

Domyślnie: **2 lotniska × ~30 destynacji × 4 dni ≈ 240 wyszukiwań UI** (~30–45 min).

| Sposób | Przykład | Efekt |
| --- | --- | --- |
| Mniej dni | `--days 2` lub `WIZZAIR_DAYS=2` | ~2× szybciej |
| Jedno lotnisko | `--origin KRK` | ~2× szybciej |
| Wybrane kierunki | `--destination FCO --destination BCN` | proporcjonalnie mniej |
| Tryb fast | `--fast` lub `WIZZAIR_FAST_SCAN=true` | ~30–40% szybciej |
| Kombinacja | `send --origin KRK --days 2 --fast` | np. ~8–12 min |

Przykłady:

```bash
# tylko Kraków, dziś + jutro
python -m wizzair send --origin KRK --days 2

# tylko kilka popularnych kierunków
python -m wizzair send --destination FCO,BCN,LTN,MXP

# szybki test
python -m wizzair run --origin KRK --days 1 --destination FCO --fast
```

Lista destynacji jest cache'owana w `~/.config/wizzair/destinations-KRK.json` (odświeża się co 7 dni).

## Konfiguracja (`.env`)

| Zmienna | Domyślnie | Opis |
| --- | --- | --- |
| `WIZZAIR_EMAIL` | — | Login Multipass |
| `WIZZAIR_PASSWORD` | — | Hasło Multipass |
| `WIZZAIR_EMAIL_FROM` | `andalath@gmail.com` | Nadawca |
| `WIZZAIR_EMAIL_TO` | katarzyna + andalath | Odbiorcy |
| `GMAIL_TOKEN_DIR` | `~/.config/gmail-agent` | Token OAuth |
| `WIZZAIR_ORIGINS` | `KRK,KTW` | Lotniska wylotu |
| `WIZZAIR_DAYS` | `4` | Ile dni do przodu (dziś włącznie) |
| `WIZZAIR_DESTINATIONS` | — | Opcjonalny filtr IATA (np. `FCO,BCN`) |
| `WIZZAIR_FAST_SCAN` | `false` | Krótsze timeouty UI |
