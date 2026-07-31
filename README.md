# Agents

This repo hosts two independent CLI agents that share a single `.venv`
and a single `OPENAI_API_KEY`:

- **`gmail_agent`** — drafts replies to your unread Gmail. Documented
  below.
- **`travel_agent`** — scrapes Polish travel portals (esky, itaka,
  r.pl, wakacyjnipiraci, …), extracts concrete offers with an LLM, and
  groups the cheapest ones per destination ordered by departure date.
  See [the travel agent section](#travel-deals-agent) at the bottom.
  Repo: **https://github.com/krzysztofras666/travel-agent**
- **`tech_news_agent`** — fetches tech headlines from RSS/API sources and
  emails a daily digest.
  Repo: **https://github.com/krzysztofras666/tech-news-agent**

---

# Gmail Agent

A small CLI agent that:

1. Connects to **one or more** Gmail accounts via OAuth.
2. Reads your unread emails in each INBOX (or just the Primary tab via
   `--scope primary`).
3. Drafts a reply for each one using OpenAI, optionally informed by a
   per-account knowledge base (e.g. product catalog, FAQ, live web pages).
4. Saves each draft directly to that account's Gmail **Drafts** folder,
   attached to the original thread, so you can review, edit, and hit
   **Send** from Gmail itself.

The agent never sends mail. It only creates drafts.

---

## 1. Prerequisites

- Python 3.10+
- An OpenAI API key
- A Google Cloud project with the Gmail API enabled and an OAuth Desktop
  App client (see step 2)

## 2. Google Cloud setup (one-time)

1. <https://console.cloud.google.com/> → create / pick a project.
2. **APIs & Services → Library** → enable **Gmail API**.
3. **APIs & Services → OAuth consent screen** → *External*, add yourself
   (and any other Gmail you want to authorize) under **Test users**.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   → application type **Desktop app** → Download JSON.
5. Save as `credentials.json` in this repo root (or point
   `GOOGLE_CREDENTIALS_FILE` at it). The same `credentials.json` is reused
   for every account; only the per-account refresh tokens differ.

## 3. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set OPENAI_API_KEY (and optionally USER_PROFILE)
```

## 4. Add an account

```bash
python -m gmail_agent auth
```

This opens a browser, asks you to grant the app access to the Gmail
account you sign in with, and writes the token under
`accounts/<that-email>/token.json`.

Repeat for each additional Gmail account you want the agent to process —
each one needs its own OAuth grant.

You can list configured accounts at any time:

```bash
python -m gmail_agent accounts
```

## 5. Run

```bash
# All configured accounts, all unread in INBOX, up to 10 per account,
# drafts saved automatically, no interactive review.
python -m gmail_agent run

# Just one account.
python -m gmail_agent run --account katarzyna.ras@leadersisland.com

# Interactive review of each draft before it's saved.
python -m gmail_agent run --review

# Limit to Gmail's Primary tab.
python -m gmail_agent run --scope primary
```

The agent will, per account:

- Skip no-reply / `noreply` / `do-not-reply` senders.
- Skip mailing lists and automated mail (`List-Unsubscribe`,
  `Auto-Submitted`, `Precedence: bulk/list`).
- Skip threads where you've already sent a reply.
- Skip messages you sent yourself.
- Skip messages it has already drafted for (label `agent/drafted`).
- Leave the original message **unread**.

When it's done, open Gmail (for that account) and look at the **Drafts**
folder. Each draft is attached to the original conversation.

### Review mode (`--review`)

In review mode the agent shows you, for each generated draft:

- The sender, subject, date.
- The original email body (truncated; press `v` to see the full text).
- The proposed draft.

| key | action                                                                 |
| --- | ---------------------------------------------------------------------- |
| `a` | **Accept** — save the draft to Gmail and apply the agent label.        |
| `e` | **Edit** — opens the draft in `$EDITOR` (`$VISUAL` if set, else `vi`). |
| `v` | **View** — print the full original email body.                         |
| `r` | **Regenerate** — call the model again, optionally with steering text.  |
| `s` | **Skip** — don't save anything for this email.                         |
| `q` | **Quit** — stop the run; remaining emails are left untouched.          |

Only `a` saves a draft and applies the `agent/drafted` label.

### Label (`agent/drafted`)

After a draft is created the agent applies a Gmail label (default
`agent/drafted`, configurable via `AGENT_LABEL_NAME`). The next run uses
this label to skip emails it has already drafted for, so re-runs are
idempotent. Remove the label in Gmail to force re-processing.

## 6. Per-account customization

Anything you drop into `accounts/<email>/` is picked up automatically.
All files are optional except `token.json` (created by `auth`).

```
accounts/
└── katarzyna.ras@leadersisland.com/
    ├── token.json          # created by `python -m gmail_agent auth`
    ├── profile.md          # who you are + how you sign your replies
    ├── knowledge.md        # facts the model can quote: catalog, FAQ, etc.
    └── live_sources.txt    # one URL per line, fetched on each run
```

- **`profile.md`** — free text describing the persona and tone. Overrides
  the global `USER_PROFILE` from `.env`.
- **`knowledge.md`** — free text that gets injected into every prompt
  for that account. The system prompt tells the model to treat it as
  facts and quote URLs / dates verbatim instead of inventing them.
- **`live_sources.txt`** — one URL per line. Each URL is fetched at the
  start of every `run` (results cached for the duration of that run) and
  its plain-text content is appended to the knowledge so the model sees
  fresh data such as a current schedule page.

This repo ships with a pre-seeded knowledge base for
`katarzyna.ras@leadersisland.com` covering the Leaders Island training
catalog (extracted from `Katalog szkoleń_wersja PL.pdf`) and the live
schedule page <https://leadersisland.com/szkolenia/>.

## 7. Scheduled daily runs

The repo ships with a launchd job (macOS-native scheduler) that runs the
agent every day at **08:15 local time** for every configured account.
launchd is used instead of cron because it (a) doesn't require granting
cron Full Disk Access on modern macOS, and (b) catches up automatically
if the Mac was asleep at 08:15 — when it wakes, it runs the missed job.

### Install

```bash
./scripts/install_schedule.sh
```

That command copies `scripts/com.gmail-agent.daily.plist` to
`~/Library/LaunchAgents/` and loads it via `launchctl bootstrap`. It's
idempotent: re-run it after editing the plist or the wrapper to refresh
the installed job.

### Test now (without waiting until 08:15)

```bash
launchctl kickstart gui/$(id -u)/com.gmail-agent.daily
```

Or just run the wrapper directly:

```bash
./scripts/run_daily.sh              # real run
./scripts/run_daily.sh --dry-run    # safe smoke test, no drafts
```

### Logs

```
logs/run.log              # per-run agent output (rotated at ~5 MB)
logs/launchd.out.log      # launchd-captured stdout
logs/launchd.err.log      # launchd-captured stderr
```

`tail -f logs/run.log` after a launch to watch a run in real time.

### Status

```bash
launchctl print gui/$(id -u)/com.gmail-agent.daily
```

Look for `state`, `next fire`, and `last exit code` in the output.

### Change the schedule

Edit `scripts/com.gmail-agent.daily.plist`, find the
`StartCalendarInterval` block, change the `Hour` / `Minute` integers,
then re-run `./scripts/install_schedule.sh`.

For multiple firings per day, replace the dict with an array of dicts:

```xml
<key>StartCalendarInterval</key>
<array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>15</integer></dict>
    <dict><key>Hour</key><integer>13</integer><key>Minute</key><integer>0</integer></dict>
</array>
```

### Uninstall

```bash
./scripts/uninstall_schedule.sh
```

### Troubleshooting

#### `Token has been expired or revoked.` (every 7 days)

Google OAuth apps stuck in the **Testing** publish status invalidate
refresh tokens after exactly 7 days. The agent now reports this clearly
on the next run and the daily wrapper posts a macOS notification, but
the fix is the same: re-authorize the affected account.

```bash
python -m gmail_agent auth --account <email>
```

To stop this from recurring forever, **publish** the OAuth consent
screen — it's still free and still works for personal accounts; it just
removes the 7-day timer:

1. Open <https://console.cloud.google.com/apis/credentials/consent>.
2. Make sure the project picker (top bar) is set to the project that
   owns your `credentials.json`.
3. Click **Publish app** → confirm.
4. The app moves from *Testing* to *In production*. Refresh tokens
   minted after this no longer expire on a clock.
5. Re-run `auth` once more so a fresh token is issued under the new
   policy.

The "Production" status doesn't require Google verification as long as
you only request the `gmail.modify` scope (and other scopes Google
classifies as non-sensitive). You'll see an *unverified* warning at the
consent screen — click **Advanced → Continue** the same way you do
in Testing mode.

If you'd rather keep the app in Testing, you can also script a
re-auth reminder (e.g. `at now + 6 days` or a separate launchd job).

### Plain cron (alternative)

If you'd rather use cron, drop the launchd job and add this line via
`crontab -e`:

```cron
15 8 * * * /Users/krzysztofras/gmail-agent/scripts/run_daily.sh
```

Note: macOS Ventura and later require you to grant `/usr/sbin/cron` Full
Disk Access (System Settings → Privacy & Security → Full Disk Access) so
it can read files in your home directory. Cron also won't catch up on
runs missed while the Mac was asleep — launchd will.

## 8. Security notes

- `credentials.json`, `accounts/**/token.json`, and `.env` are gitignored.
  Keep them private — a token is effectively a long-lived key into that
  Gmail account.
- The OAuth scope used is `gmail.modify`. Google's write scopes all
  technically permit sending, but the agent's code never calls a send
  endpoint — only `drafts.create`. Sending requires you to open the
  draft in Gmail and click **Send** yourself.
- Audit `gmail_agent/gmail_client.py` if you want to confirm:
  `users().messages().send`, `drafts().send`, etc. are not used.

---

# Travel deals agent

`travel_agent` is a standalone CLI that scrapes a curated list of
Polish travel portals, extracts concrete offers from the messy HTML
using an LLM, deduplicates across sites, and prints the cheapest 1–N
offers per destination ordered by departure date.

## Configured sites

| ID                | Site                       |
| ----------------- | -------------------------- |
| `esky`            | esky.pl                    |
| `coraltravel`     | coraltravel.pl             |
| `itaka`           | itaka.pl                   |
| `fly`             | fly.pl                     |
| `lastminute`      | pl.lastminute.com          |
| `travelplanet`    | travelplanet.pl            |
| `rpl`             | r.pl                       |
| `wakacyjnipiraci` | wakacyjnipiraci.pl         |
| `superlastminute` | super-last-minute.pl       |
| `kanalwyjazdowy`  | kanalwyjazdowy.pl          |

`python -m travel_agent list-sites` prints this list, plus the exact
listing URLs each site falls back to in order.

## First-time setup

```bash
pip install -r requirements.txt        # picks up playwright too
playwright install chromium            # ~100 MB browser, one-time
```

The `playwright install` step is only needed if you want the headless-
Chromium fallback (recommended — it's what unlocks the JS-rendered and
anti-bot-protected sites). The agent runs fine without it and will
just skip the fallback, printing a one-line hint.

## Run

```bash
source .venv/bin/activate
python -m travel_agent run                       # all sites, auto-fallback
python -m travel_agent run --site itaka --site rpl   # subset
python -m travel_agent run --json > deals.json   # machine-readable
python -m travel_agent run --max-per-destination 1   # one best deal per place
python -m travel_agent run --no-diagnostics      # hide per-site status

# Fetcher engine knobs:
python -m travel_agent run --no-browser     # httpx only, fastest, may miss some sites
python -m travel_agent run --browser-all    # every site through real Chromium
```

Output is a single table grouped by destination, sorted by departure
date, with the cheapest offers per destination:

```
Destination          Dates                       Price        Source
Tunezja, Mahdia      2026-05-28 → 2026-06-04     2 199 PLN    travelplanet.pl
Egipt, Hurghada      2026-06-06 → 2026-06-14     2 499 PLN    itaka.pl
Grecja, Kreta        2026-09-01 → 2026-09-08     2 899 PLN    r.pl
```

A second diagnostics table shows what each source returned (chars
fetched, offers extracted, any errors).

## How it works

1. **Fetch (httpx)** — all sites concurrently with `httpx`, realistic
   browser headers (Polish `Accept-Language`, desktop Chrome UA,
   gzip+brotli decoding). For each site we try a `/last-minute` or
   `/promocje` subpage first and fall back to the homepage.
2. **Fetch (browser fallback)** — for any site whose httpx response
   came back too short, with a 4xx/5xx, or looking like an anti-bot
   interstitial ("Pardon Our Interruption", "Access Denied", etc.),
   the agent retries through a single headless Chromium running
   Playwright. The browser dismisses Polish cookie banners
   (Didomi/OneTrust/etc.), then waits for either the page body to
   render past 600 chars *or* the network to go idle, whichever fires
   first. One browser process is shared across all fallback fetches
   so the cost is paid only once per run.
3. **Clean** — strip `<script>`/`<style>`/`<nav>`/etc., collapse
   whitespace, clip to ~18k chars. RSS feeds (wakacyjnipiraci,
   kanalwyjazdowy) are flattened without the heavy DOM stripping.
4. **Extract** — feed the cleaned text per-site to the LLM with a
   strict JSON schema (destination, departure/return date, price,
   currency, nights, title, notes). The model is told to skip
   marketing banners and never invent missing dates or prices.
5. **Aggregate** — deduplicate across sites (same destination + dates +
   rounded price), keep the cheapest N per destination, then sort
   destinations by earliest departure date.
6. **Render** — pretty table via `rich` (or JSON with `--json`). The
   per-site diagnostics row shows which fetcher engine (`http` or
   `browser`) actually produced the text.

## Configuration

All settings come from environment variables / `.env` (loaded
automatically). Travel-specific knobs are optional:

| Variable                       | Default          | Purpose                                                                 |
| ------------------------------ | ---------------- | ----------------------------------------------------------------------- |
| `OPENAI_API_KEY`               | —                | Required. Shared with `gmail_agent`.                                    |
| `TRAVEL_OPENAI_MODEL`          | `OPENAI_MODEL` or `gpt-4o-mini` | Cheap and accurate enough for HTML→JSON extraction.        |
| `TRAVEL_HTTP_TIMEOUT`          | `20`             | Per-request HTTP timeout, seconds.                                      |
| `TRAVEL_FETCH_CONCURRENCY`     | `6`              | Max simultaneous HTTP requests.                                         |
| `TRAVEL_MAX_TEXT_CHARS`        | `18000`          | Per-site cap on cleaned text sent to the LLM.                           |
| `TRAVEL_MAX_OFFERS_PER_DEST`   | `3`              | How many offers per destination to keep (cheapest wins).                |
| `TRAVEL_USER_AGENT`            | a desktop Chrome UA | Override if you need to test from a specific browser fingerprint.    |
| `TRAVEL_BROWSER_RETRY_MIN_CHARS` | `2000`         | Httpx responses shorter than this trigger a browser retry (`auto` mode). |

## Site coverage

With `playwright install chromium` done, 9 of 10 sites return real
offer data:

| Site | Engine | Notes |
| --- | --- | --- |
| itaka.pl | http | Server-renders 12k+ chars of offers in HTML. |
| r.pl | http | Server-renders offer cards. |
| travelplanet.pl | http | Server-renders. |
| super-last-minute.pl | http | Server-renders. |
| wakacyjnipiraci.pl | http | RSS feed (`/feed`). |
| kanalwyjazdowy.pl | http | RSS feed (`/feed/`). |
| esky.pl | browser | Auto-falls-back; httpx gets a 403, browser sees the full last-minute grid. |
| fly.pl | browser | Auto-falls-back; offer cards are JS-rendered. |
| pl.lastminute.com | browser | Auto-falls-back to `/deals`, which shows real package deals. |
| **coraltravel.pl** | **blocked** | Protected by Imperva Incapsula (returns `403` + JS challenge even to a real browser). Bypassing this needs `playwright-stealth` plus possibly a residential proxy — out of scope here. |

### Why `--browser-all` exists

`auto` is the right default. Use `--browser-all` only when you suspect
a normally-http-served site has changed its template — fetching every
site through Chromium gives the most permissive view of what's there,
at the cost of ~3–6s per site.

### Why `--no-browser` exists

Use `--no-browser` for the fastest possible run (typically <5s total)
when you don't care about the four JS-heavy / anti-bot sites and
just want the RSS+SSR sources.

## Email the digest

The agent can render the result as a Gmail-friendly HTML digest and
send it to a list of recipients. It uses the OAuth token created by
`python -m gmail_agent auth` — no new credentials needed.

```bash
# scrape + email to the configured recipients
python -m travel_agent send

# preview the email without sending it (writes logs/last_email.html)
python -m travel_agent send --dry-run

# override recipients ad-hoc (repeatable, or comma-separated)
python -m travel_agent send --to me@example.com --to friend@example.com

# render the HTML to disk only (no Gmail API call at all)
python -m travel_agent preview-email --out /tmp/preview.html
```

### Defaults

| What | Default | How to override |
| --- | --- | --- |
| Sender (`From`) | `andalath@gmail.com` | `--from <email>` or `TRAVEL_EMAIL_FROM` env var. Must already be authenticated via `python -m gmail_agent auth`. |
| Recipients (`To`) | `andalath@gmail.com, goniaras@gmail.com, katarzyna.dyngosz@gmail.com` | `--to` (repeatable) or `TRAVEL_EMAIL_TO` env var (comma-separated). |
| Subject | `Tanie wakacje — YYYY-MM-DD (N kierunków, M ofert)` | Not configurable from CLI; edit `render_html.py` if needed. |

The body is multipart/alternative — Gmail clients see the HTML, plain
text clients see the readable plain-text fallback. The HTML uses only
inline CSS (no external stylesheets, no remote images) so it renders
identically in Gmail desktop, Gmail mobile, and Outlook.

> Note: this is the **only** place in this repo that calls a Gmail
> `send` endpoint. `gmail_agent` deliberately creates drafts only.
> The travel digest sends because you've explicitly opted into a
> scheduled outbound email.

## Scheduled daily run (08:30)

A second launchd job ships in this repo, running 15 minutes after the
gmail_agent's daily draft pass:

```bash
./scripts/install_travel_schedule.sh
```

This installs `~/Library/LaunchAgents/com.travel-agent.daily.plist`
which fires `scripts/run_travel_daily.sh` every day at **08:30 local
time**. If the Mac was asleep at 08:30, launchd runs the job at the
next wake (just like the gmail_agent job).

### Test it once now (without waiting for 08:30)

```bash
launchctl kickstart gui/$(id -u)/com.travel-agent.daily
# or run the wrapper directly:
./scripts/run_travel_daily.sh                # real run, sends mail
./scripts/run_travel_daily.sh --dry-run      # safe smoke test, no send
```

### Logs

```
logs/travel_run.log              # per-run output (rotated at ~5 MB)
logs/travel.launchd.out.log      # launchd-captured stdout
logs/travel.launchd.err.log      # launchd-captured stderr
logs/last_email.html             # most recent rendered email (overwritten)
```

`tail -f logs/travel_run.log` to watch a run live; open
`logs/last_email.html` in any browser to see exactly what was sent.

### Change the schedule

Edit `scripts/com.travel-agent.daily.plist` → `StartCalendarInterval`
→ change `Hour` / `Minute`, then re-run
`./scripts/install_travel_schedule.sh`.

### Uninstall

```bash
./scripts/uninstall_travel_schedule.sh
```

# gmail-agent
