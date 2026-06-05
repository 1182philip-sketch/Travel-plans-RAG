import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
USERS_FILE = PROJECT_ROOT / "users.csv"
CHAT_FILE = PROJECT_ROOT / "chat_history.csv"
BACKUP_DIR = PROJECT_ROOT / "backups"

CSV_SCHEMAS = {
    USERS_FILE: ["user_id", "preferences", "created_at"],
    CHAT_FILE: ["user_id", "role", "content", "timestamp"],
}


def backup_file(path, stamp):
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def reset_csv(path, headers):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def main():
    parser = argparse.ArgumentParser(
        description="Reset users.csv and chat_history.csv to empty header-only files."
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Reset without copying the current CSV files to backups/ first.",
    )
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = []

    if not args.no_backup:
        for path in CSV_SCHEMAS:
            backup_path = backup_file(path, stamp)
            if backup_path:
                backups.append(backup_path)

    for path, headers in CSV_SCHEMAS.items():
        reset_csv(path, headers)

    print("Reset complete:")
    print(f"- {USERS_FILE.name}")
    print(f"- {CHAT_FILE.name}")
    if backups:
        print("\nBackups created:")
        for backup_path in backups:
            print(f"- {backup_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
