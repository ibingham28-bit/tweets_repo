#!/usr/bin/python3

import glob
import json
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


LATEST_DATA_FILE = Path("latest_trump_archive.json")
LATEST_DATA_URL = (
    "https://drive.google.com/uc?export=download&id=16wm-2NTKohhcA26w-kaWfhLIGwl_oX95"
)
LATEST_DATA_PAGE_URL = (
    "https://drive.google.com/file/d/16wm-2NTKohhcA26w-kaWfhLIGwl_oX95/view?usp=sharing"
)

PHRASES = [
    "Obama",
    "Trump",
    "Mexico",
    "Russia",
    "Fake News",
    "Wall",
    "DACA",
    "Mainstream Media",
]


def download_latest_dataset_if_missing() -> bool:
    if LATEST_DATA_FILE.exists():
        return True
    try:
        urllib.request.urlretrieve(LATEST_DATA_URL, LATEST_DATA_FILE)
        return True
    except Exception:
        return False


def load_master_archive(pattern: str = "master_*.json") -> list[dict]:
    tweets: list[dict] = []
    for path in sorted(glob.glob(pattern)):
        with open(path, "r", encoding="utf-8") as infile:
            tweets.extend(json.load(infile))
    return tweets


def load_all_tweets() -> tuple[list[dict], str]:
    if download_latest_dataset_if_missing() and LATEST_DATA_FILE.exists():
        with open(LATEST_DATA_FILE, "r", encoding="utf-8") as infile:
            return json.load(infile), "latest_faq_json"
    return load_master_archive(), "master_2009_2018_json"


def count_phrases(tweets: list[dict], phrases: list[str]) -> dict[str, int]:
    normalized = [phrase.lower() for phrase in phrases]
    counts = {phrase: 0 for phrase in normalized}
    for tweet in tweets:
        text = str(tweet.get("text", "")).lower()
        for phrase in normalized:
            if phrase in text:
                counts[phrase] += 1
    return counts


def build_markdown_table(counts: dict[str, int], total: int) -> str:
    phrases = sorted(counts.keys())
    phrase_width = max(len("phrase"), max(len(p) for p in phrases))
    percent_width = len("percent of tweets")

    lines = [
        f"| {'phrase':>{phrase_width}} | {'percent of tweets':>{percent_width}} |",
        f"| {'-' * phrase_width} | {'-' * percent_width} |",
    ]
    for phrase in phrases:
        percent = (counts[phrase] / total) * 100
        percent_text = f"{percent:05.2f}"
        lines.append(f"| {phrase:>{phrase_width}} | {percent_text:>{percent_width}} |")
    return "\n".join(lines)


def make_plot(counts: dict[str, int], total: int, out_path: Path) -> None:
    phrases = sorted(counts.keys())
    percentages = [(counts[p] / total) * 100 for p in phrases]

    plt.figure(figsize=(10, 5))
    plt.bar(phrases, percentages, color="#1f77b4")
    plt.ylabel("Percent of tweets")
    plt.xlabel("Phrase")
    plt.title("Percent of Tweets Containing Each Phrase")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def make_device_plot(tweets: list[dict], out_path: Path) -> None:
    device_counts = Counter(str(t.get("device", "Unknown")) for t in tweets)
    top = device_counts.most_common(8)
    labels = [name for name, _ in top]
    values = [count for _, count in top]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color="#ff7f0e")
    plt.ylabel("Number of tweets")
    plt.xlabel("Device/source")
    plt.title("Top Tweet Sources (Extra Credit: non-text field)")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def parse_date_field(tweet: dict) -> datetime | None:
    date_value = tweet.get("date")
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return None


def write_readme(
    table: str,
    phrase_image_name: str,
    device_image_name: str,
    data_source: str,
    total: int,
    min_date: datetime | None,
    max_date: datetime | None,
) -> None:
    date_range = "unknown"
    if min_date and max_date:
        date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"

    source_line = (
        f"Google Drive JSON from TheTrumpArchive FAQ ({LATEST_DATA_PAGE_URL})"
        if data_source == "latest_faq_json"
        else "Local master_2009-2018 JSON files"
    )

    content = "\n".join(
        [
            "# Trump Tweet Phrase Analysis",
            "",
            "This table and charts show phrase percentages and tweet-source trends in the Trump archive data.",
            "",
            "## Dataset Verification",
            "",
            f"- Data source used: {source_line}",
            f"- Total records analyzed: {total}",
            f"- Date range in data: {date_range}",
            "",
            "## Phrase Percent Table",
            "",
            table,
            "",
            f"![Tweet phrase percentages]({phrase_image_name})",
            "",
            "## Extra Credit Plot (non-text field)",
            "",
            f"![Tweets by device/source]({device_image_name})",
            "",
        ]
    )
    Path("README.md").write_text(content, encoding="utf-8")


def main() -> None:
    tweets, data_source = load_all_tweets()
    counts = count_phrases(tweets, PHRASES)
    total = len(tweets)
    dates = [parse_date_field(t) for t in tweets]
    dates = [d for d in dates if d is not None]
    min_date = min(dates) if dates else None
    max_date = max(dates) if dates else None

    print("len(tweets)=", total)
    print("counts=", counts)
    print("data_source=", data_source)
    if min_date and max_date:
        print("date_range=", min_date.strftime("%Y-%m-%d"), "to", max_date.strftime("%Y-%m-%d"))
    print()

    table = build_markdown_table(counts, total)
    print(table)

    phrase_image_name = "tweet_keyword_percentages.png"
    device_image_name = "tweets_by_device.png"
    make_plot(counts, total, Path(phrase_image_name))
    make_device_plot(tweets, Path(device_image_name))
    write_readme(
        table=table,
        phrase_image_name=phrase_image_name,
        device_image_name=device_image_name,
        data_source=data_source,
        total=total,
        min_date=min_date,
        max_date=max_date,
    )


if __name__ == "__main__":
    main()
