#!/usr/bin/env python

from __future__ import annotations
import time

import typing
import itertools


import os
import googleapiclient.discovery

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptList


from dotenv import load_dotenv
load_dotenv()  # load up the .env file


if typing.TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3.resources import YouTubeResource
    from googleapiclient._apis.youtube.v3.schemas import PlaylistItem



RCE_CHANNEL_ID = 'UCeP4Yv3s4RvS0-6d9OInRMw'
RCE_UPLOADS_PLAYLIST = 'UUeP4Yv3s4RvS0-6d9OInRMw'
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

some_video_ids = ["5NiuwWwO2Ng", '1IflykOzLLY', 'iqEcbLz0Q-w']




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


def get_transcript(video_id: str) -> list[TranscriptItem]:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return transcript


def ichunk(iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk



def main():
    from devtools import debug

    videos_gen = get_videos()

    for videos in ichunk(videos_gen, 10):
        # avoid getting rate limited, do 10 at a time then sleep
        time.sleep(1)

        for video in videos:
            transcript = get_transcript(video["id"])
            debug(f'title={video["title"]}', video, transcript)
        break


if __name__ == "__main__":
    main()
