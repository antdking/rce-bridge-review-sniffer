#!/usr/bin/env python

from __future__ import annotations
from dataclasses import dataclass, field
import inspect
import json
from pathlib import Path
import time
import math

import typing
import itertools


import os
import googleapiclient.discovery
from functools import partial

from youtube_transcript_api import YouTubeTranscriptApi, CouldNotRetrieveTranscript


from dotenv import load_dotenv
load_dotenv()  # load up the .env file


if typing.TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3.resources import YouTubeResource
    from googleapiclient._apis.youtube.v3.schemas import PlaylistItem



RCE_CHANNEL_ID = 'UCeP4Yv3s4RvS0-6d9OInRMw'
RCE_UPLOADS_PLAYLIST = 'UUeP4Yv3s4RvS0-6d9OInRMw'
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
CACHE_DIR = '.rce-cache'


def get_youtube_api(key=GOOGLE_API_KEY) -> YouTubeResource:
    service_name = "youtube"
    api_version = "v3"

    return googleapiclient.discovery.build('youtube', 'v3', developerKey=key)


def _get_videos(playlist_id=RCE_UPLOADS_PLAYLIST) -> typing.Generator[PlaylistItem, None, None]:
    uploads = get_youtube_api().playlistItems()
    req = uploads.list(part='contentDetails,snippet', playlistId=playlist_id)

    while req is not None:
        doc = req.execute()

        yield from iter(doc.get('items') or [])

        req = uploads.list_next(req, doc)


def get_videos():
    for video in _get_videos():
        yield {
            "id": video["contentDetails"]['videoId'],
            "title": video['snippet']['title'],
            "publishedOn": video['contentDetails']['videoPublishedAt']
        }


class TranscriptItem(typing.TypedDict):
    text: str
    start: float
    duration: float


def get_transcript(video_id: str) -> list[TranscriptItem] :
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return transcript


def ichunk(iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


@dataclass()
class JSONFileStore:
    dir: str
    pretty: bool = field(default=False)

    dir_path: Path = field(init=False)
    json_dump: typing.Callable = field(init=False)

    _MISS = object()

    def __post_init__(self):
        self.dir_path = Path(self.dir)
        self.dir_path.mkdir(parents=True, exist_ok=True)

        if self.pretty:
            self.json_dump = partial(json.dump, sort_keys=True, indent=4)
        else:
            self.json_dump = json.dump

    def memoize(self, func=None, *, tag: str):
        if func is None:
            return partial(self.memoize, tag=tag)

        # setup the tag, hacky
        (self.dir_path / tag).mkdir(exist_ok=True)

        sig = inspect.signature(func)

        assert len(sig.parameters) == 1, "keep it simple for now"

        def inner(arg1):
            cached = self.get(tag, arg1)
            if cached is self._MISS:
                return self.set(tag, arg1, func(arg1))
            return cached

        return inner

    def get(self, tag: str, key: str):
        f_path = self.dir_path / tag / f"{key}.json"

        try:
            with f_path.open() as f:
                return json.load(f)
        except FileNotFoundError:
            return self._MISS


    def set(self, tag: str, key: str, val):
        f_path = self.dir_path / tag / f"{key}.json"

        with f_path.open(mode='w') as f:
            self.json_dump(val, f)

        # ensure we're consistent
        return self.get(tag, key)



def main():
    from devtools import debug
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = JSONFileStore(CACHE_DIR, pretty=True)
    cached_get_transcript = cache.memoize(tag='transcript')(get_transcript)
    (cache.dir_path / 'video').mkdir(exist_ok=True)
    cache_video = lambda video: cache.set('video', video['id'], video)

    videos_gen = get_videos()

    failures = []

    for videos in ichunk(videos_gen, 10):
        # avoid getting rate limited, do 10 at a time then sleep
        time.sleep(0.2)

        for video in videos:
            # just get the video data onto the filesystem
            cache_video(video)
            try:
                transcript = cached_get_transcript(video["id"])

                # kinda sorta nicer formatting while debugging
                truncated_transcripts = (
                    [f"[t{math.floor(t['start'])}+{math.ceil(t['duration'])}] -- {t['text']}" for t in (transcript[:3])]
                    + [f"... Skipping {len(transcript) - 6} entries ..."]
                    + [f"[t{math.floor(t['start'])}+{math.ceil(t['duration'])}] -- {t['text']}" for t in (transcript[-3:])]
                )
                debug(
                    video,
                    truncated_transcripts

                )
            except CouldNotRetrieveTranscript as e:
                failures.append((video, e))

    for video, py_error in failures:
        pretty_error = str(py_error)
        debug(video, pretty_error)



if __name__ == "__main__":
    main()
