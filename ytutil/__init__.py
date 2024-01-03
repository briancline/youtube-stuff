import json
import pathlib
# import pprint
from math import floor

import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import isodate

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
# USER_DATA_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

MAX_PAGE_SIZE = 50

# TODO: add logger to curtail my print() proclivities


def youtube_init(creds_file: pathlib.Path):
    with open(creds_file, 'r', encoding='utf-8') as fd:
        cred_data = json.load(fd)

    # youtube: googleapiclient.discovery.Resource = googleapiclient.discovery.build(
    #     API_SERVICE_NAME, API_VERSION,
    #     developerKey="abc")

    creds = google.oauth2.credentials.Credentials(**cred_data)
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)


def save_json_file(obj, file_path: pathlib.Path):
    with open(file_path, 'w', encoding='utf-8') as fd:
        json.dump(obj, fd, indent=2)


def format_duration(seconds: float) -> str:
    hours, secs_left = divmod(seconds, 3600)
    mins, seconds = divmod(secs_left, 60)
    hours = int(hours)
    mins = int(mins)
    seconds = int(floor(seconds))
    return ''.join((f'{hours}:' if hours else '',
                    f'{mins:02d}:{seconds:02d}' if hours else f'{mins}:{seconds:02d}'))


def video_duration_str(iso_duration: str) -> str:
    return format_duration(iso_duration_to_seconds(iso_duration))


def iso_duration_to_seconds(iso_duration: str) -> float:
    delta = isodate.parse_duration(iso_duration)
    return delta.total_seconds()


def list_all(svc, properties=None, **kwargs):
    properties = properties or 'snippet'
    if 'maxResults' not in kwargs:
        kwargs['maxResults'] = MAX_PAGE_SIZE

    request = svc.list(part=properties, **kwargs)

    page_num = 0
    records = []
    while request is not None:
        page_num += 1
        # print(f'Requesting page {page_num}...')

        response = request.execute()
        for item in response['items']:
            records.append(item)

        request = svc.list_next(request, response)

    return records


def get_playlists(youtube: googleapiclient.discovery.Resource):
    return list_all(
        youtube.playlists(),
        properties='snippet,contentDetails',
        mine=True,
    )


def get_playlist_items(playlist_id: str, youtube: googleapiclient.discovery.Resource):
    return list_all(
        youtube.playlistItems(),
        playlistId=playlist_id,
        properties='snippet,contentDetails',
    )


def get_videos(video_ids: list[str], youtube: googleapiclient.discovery.Resource):
    properties = 'snippet,contentDetails,statistics'
    vid_svc = youtube.videos()
    videos = {}
    chunk_count = MAX_PAGE_SIZE
    chunk_num = 0

    for chunk_start in range(0, len(video_ids), chunk_count):
        chunk_num += 1
        chunk_end = chunk_start + chunk_count
        chunk_ids = video_ids[chunk_start:chunk_end]
        vid_ids_str = ','.join(chunk_ids)

        # print(f'Chunking IDs [{chunk_start}, {chunk_end}]')
        # print(f'  {chunk_ids}')
        # print(f'  {vid_ids_str}')

        for item in list_all(vid_svc, id=vid_ids_str, properties=properties,
                             maxResults=chunk_count):
            videos[item['id']] = item

    return videos
