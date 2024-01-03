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


def get_playlists(youtube: googleapiclient.discovery.Resource):
    playlists_svc = youtube.playlists()
    results = []
    request = playlists_svc.list(part="snippet,contentDetails", maxResults=50, mine=True)
    page_num = 0
    while request is not None:
        page_num += 1
        # print(f'Requesting playlists page {page_num}...')

        response = request.execute()
        for item in response['items']:
            results.append(item)

        request = playlists_svc.list_next(request, response)

    return results


def iso_duration_to_seconds(iso_duration: str) -> float:
    delta = isodate.parse_duration(iso_duration)
    return delta.total_seconds()


def get_playlist_items(playlist_id: str, youtube: googleapiclient.discovery.Resource):
    plitems_svc = youtube.playlistItems()
    videos = []
    request = plitems_svc.list(playlistId=playlist_id, part="snippet,contentDetails", maxResults=50)
    page_num = 0
    while request is not None:
        page_num += 1
        # print(f'Requesting playlistitems page {page_num}...')

        response = request.execute()
        for item in response['items']:
            videos.append(item)

        request = plitems_svc.list_next(request, response)

    return videos


def get_videos(video_ids: list[str], youtube: googleapiclient.discovery.Resource):
    vid_svc = youtube.videos()
    videos = {}
    chunk_count = 50
    chunk_num = 0
    for chunk_start in range(0, len(video_ids), chunk_count):
        chunk_num += 1
        chunk_end = chunk_start + chunk_count
        chunk_ids = video_ids[chunk_start:chunk_end]
        vid_ids_str = ','.join(chunk_ids)
        # print(f'Chunking IDs [{chunk_start}, {chunk_end}]')
        # print(f'  {chunk_ids}')
        # print(f'  {vid_ids_str}')

        request: googleapiclient.http.HttpRequest = vid_svc.list(
            part="snippet,contentDetails,statistics",
            id=vid_ids_str,
            maxResults=chunk_count,
        )

        page_num = 0
        while request is not None:
            page_num += 1
            # print(f'Requesting bulk videos chunk {chunk_num} page {page_num}...')

            response = request.execute()
            for item in response['items']:
                vid_id = item['id']
                videos[vid_id] = item

            request = vid_svc.list_next(request, response)

    return videos
