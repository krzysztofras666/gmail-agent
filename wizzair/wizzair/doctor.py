from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from wizzair.config import default_session_path, get_settings
from wizzair.email import find_gmail_token_path


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    fix: str | None = None


def run_doctor() -> list[CheckResult]:
    root = Path(__file__).resolve().parents[1]
    results: list[CheckResult] = []

    env_path = root / ".env"
    if env_path.exists():
        results.append(CheckResult(".env", True, str(env_path)))
    else:
        results.append(
            CheckResult(
                ".env",
                False,
                "Brak pliku .env",
                f"cp {root / '.env.example'} {env_path} i uzupełnij dane logowania",
            )
        )

    try:
        settings = get_settings()
        results.append(CheckResult("WIZZAIR_EMAIL", True, settings.email))
    except RuntimeError as exc:
        results.append(
            CheckResult(
                "WIZZAIR_EMAIL / WIZZAIR_PASSWORD",
                False,
                str(exc),
                "Uzupełnij WIZZAIR_EMAIL i WIZZAIR_PASSWORD w .env",
            )
        )
        settings = None

    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.exists():
        results.append(CheckResult("venv", True, str(venv_python)))
    else:
        results.append(
            CheckResult(
                "venv",
                False,
                "Brak .venv/bin/python",
                f"cd {root} && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
            )
        )

    session_path = default_session_path()
    if settings is not None:
        session_path = settings.storage_state_path
    if session_path.exists():
        results.append(CheckResult("sesja przeglądarki", True, str(session_path)))
    else:
        results.append(
            CheckResult(
                "sesja przeglądarki",
                False,
                f"Brak {session_path}",
                "python -m wizzair login --headed",
            )
        )

    if settings is not None:
        try:
            token_path = find_gmail_token_path(settings, settings.email_from)
            results.append(CheckResult("token Gmail", True, str(token_path)))
        except RuntimeError as exc:
            results.append(
                CheckResult(
                    "token Gmail",
                    False,
                    str(exc).split("\n\n", 1)[0],
                    f"cd ~/gmail-agent && python -m gmail_agent auth --account {settings.email_from}",
                )
            )

    results.extend(_launchd_checks(root))
    results.extend(_log_checks(root))
    return results


def _launchd_checks(root: Path) -> list[CheckResult]:
    if platform.system() != "Darwin":
        return [
            CheckResult(
                "harmonogram launchd",
                False,
                "Dostępny tylko na macOS",
                "./scripts/install_wizzair_schedule.sh (na Macu)",
            )
        ]

    if not shutil.which("launchctl"):
        return [
            CheckResult(
                "harmonogram launchd",
                False,
                "Brak launchctl",
                "./scripts/install_wizzair_schedule.sh",
            )
        ]

    uid = _macos_uid()
    checks: list[CheckResult] = []
    for label, hour in (("com.wizzair.daily", "08:00"), ("com.wizzair.afternoon", "13:00")):
        plist = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
        if not plist.exists():
            checks.append(
                CheckResult(
                    f"harmonogram {hour}",
                    False,
                    f"Brak {plist}",
                    "./scripts/install_wizzair_schedule.sh",
                )
            )
            continue

        loaded = _launchd_service_loaded(uid, label)
        if loaded:
            checks.append(CheckResult(f"harmonogram {hour}", True, f"aktywny ({label})"))
        else:
            checks.append(
                CheckResult(
                    f"harmonogram {hour}",
                    False,
                    f"Plik istnieje, ale usługa nie jest załadowana ({label})",
                    "./scripts/install_wizzair_schedule.sh",
                )
            )
    return checks


def _log_checks(root: Path) -> list[CheckResult]:
    morning_log = root / "logs" / "wizzair_morning.log"
    if morning_log.exists():
        return [
            CheckResult(
                "ostatni poranny run",
                True,
                f"{morning_log} (istnieje — harmonogram już kiedyś uruchomił skan)",
            )
        ]

    return [
        CheckResult(
            "ostatni poranny run",
            False,
            "Brak logs/wizzair_morning.log — automatyczny skan o 08:00 jeszcze nie ruszył",
            "./scripts/install_wizzair_schedule.sh && ./scripts/run_wizzair_morning.sh --dry-run",
        )
    ]


def _macos_uid() -> str:
    try:
        return str(subprocess.check_output(["id", "-u"], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        return "501"


def _launchd_service_loaded(uid: str, label: str) -> bool:
    try:
        subprocess.run(
            ["launchctl", "print", f"gui/{uid}/{label}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def print_doctor_report(results: list[CheckResult]) -> int:
    ok_count = sum(1 for item in results if item.ok)
    print(f"Wizzair doctor: {ok_count}/{len(results)} OK\n")

    for item in results:
        status = "OK" if item.ok else "BRAK"
        print(f"[{status}] {item.name}")
        print(f"      {item.detail}")
        if not item.ok and item.fix:
            print(f"      → {item.fix}")
        print()

    failed = [item for item in results if not item.ok]
    if not failed:
        print("Wszystko gotowe. Test ręczny: python -m wizzair send --dry-run")
        return 0

    if any(item.name.startswith("harmonogram") for item in failed):
        print(
            "Najczęstsza przyczyna braku maili: harmonogram nie jest zainstalowany na Macu.\n"
            "Uruchom: ./scripts/install_wizzair_schedule.sh"
        )
    return 1
