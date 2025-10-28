#!/usr/bin/env python3
"""YouTube uploader helper for SportSync pipeline.

This module tries to upload directly using the YouTube Data API v3 when the
Google client libraries and OAuth credentials are available. If any dependency
is missing it falls back to creating a metadata handoff JSON that can be picked
up later by a manual publishing step.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - optional dependency
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:  # pragma: no cover
    Credentials = None  # type: ignore
    build = None  # type: ignore
    MediaFileUpload = None  # type: ignore

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_PATH = Path('publishers/youtube/token.json')
CLIENT_SECRET_ENV = 'YOUTUBE_CLIENT_SECRET'


def load_credentials() -> Credentials | None:  # type: ignore[name-defined]
    if Credentials is None:
        return None
    if TOKEN_PATH.exists():
        return Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    client_secret = os.getenv(CLIENT_SECRET_ENV)
    if not client_secret:
        return None
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
    creds = flow.run_console()
    TOKEN_PATH.write_text(creds.to_json(), encoding='utf-8')
    return creds


def youtube_upload(file_path: Path, title: str, description: str, tags: list[str], privacy: str, schedule: str | None) -> None:
    creds = load_credentials()
    if not creds or build is None or MediaFileUpload is None:
        raise RuntimeError('YouTube client libraries or credentials missing.')

    youtube = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22',
        },
        'status': {
            'privacyStatus': privacy,
        },
    }
    if schedule and privacy == 'private':
        body['status']['publishAt'] = schedule

    media = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    response = request.execute()
    print(f"✅ Uploaded to YouTube: https://youtu.be/{response.get('id')}")


def fallback_manifest(file_path: Path, title: str, description: str, tags: list[str], privacy: str, schedule: str | None) -> None:
    manifest_dir = Path('publishers/youtube/pending')
    manifest_dir.mkdir(parents=True, exist_ok=True)
    slug = file_path.stem
    manifest = {
        'file': str(file_path.resolve()),
        'title': title,
        'description': description,
        'tags': tags,
        'privacy': privacy,
        'schedule': schedule,
        'created_at': dt.datetime.utcnow().isoformat() + 'Z',
    }
    out_path = manifest_dir / f'{slug}.json'
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"ℹ️  Saved YouTube upload manifest → {out_path}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Upload SportSync videos to YouTube or create a publishing manifest.')
    parser.add_argument('--file', required=True, help='Path to the video file (mp4)')
    parser.add_argument('--title', required=True)
    parser.add_argument('--desc', required=True)
    parser.add_argument('--tags', default='', help='Comma separated list of tags')
    parser.add_argument('--privacy', default='unlisted', choices=['public', 'unlisted', 'private'])
    parser.add_argument('--schedule', help='Optional RFC3339 timestamp for scheduled publish (requires private).')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    file_path = Path(args.file)
    if not file_path.exists():
        raise FileNotFoundError(args.file)

    tags = [t.strip() for t in args.tags.split(',') if t.strip()]

    try:
        youtube_upload(file_path, args.title, args.desc, tags, args.privacy, args.schedule)
    except Exception as exc:
        print(f"⚠️  YouTube direct upload unavailable ({exc}). Creating manifest instead.")
        fallback_manifest(file_path, args.title, args.desc, tags, args.privacy, args.schedule)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
