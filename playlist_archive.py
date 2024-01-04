# import argparse
import os
import pathlib
import sys

import rich.console
import rich.theme

import ytutil

console = rich.console.Console(theme=rich.theme.Theme({'repr.number': 'bold'}))


def print_info(msg):
    console.print(msg, style='white', markup=False)


def print_detail(msg):
    console.print(msg, style='dim', markup=False)


def truncate_title(title, max_len=70):
    safe_len = max_len - 3
    return f'{title[0:safe_len]}...' if len(title) >= max_len + 3 else title


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-p', '--playlist-id', required=False)
    # args = parser.parse_args()
    data_dir = pathlib.Path(os.path.dirname(__file__)) / 'data'
    youtube = ytutil.youtube_init('creds-user.json')

    print_info('Retrieving playlists')
    playlists = ytutil.get_playlists(youtube)
    playlists = sorted(playlists, key=lambda x: x['snippet']['title'].strip().lower())

    print_info(f'Archiving list of {len(playlists)} playlists')
    ytutil.save_playlists(playlists, data_dir, overwrite=True)

    all_videos = {}
    all_video_ids = []
    for pl_num, pl in enumerate(playlists):
        pl_id = pl['id']
        pl_name = pl['snippet']['title']

        print_info(f'[{pl_num + 1}/{len(playlists)}] {pl_name}')
        pl_items = ytutil.get_playlist_items(pl_id, youtube)

        print_detail(f'  - Archiving metadata for {len(pl_items)} playlist items')
        ytutil.save_playlist_items(pl_id, pl_items, data_dir, overwrite=True)

        for vid_id in [x['contentDetails']['videoId'] for x in pl_items]:
            all_video_ids.append(vid_id)

    all_video_ids = list(set(all_video_ids))
    print_info(f'Retrieving video metadata for {len(all_video_ids)} videos')
    all_videos = ytutil.get_videos(all_video_ids, youtube)

    print_info(f'Archiving video metadata for {len(all_videos)} videos)')
    for vid_id, vid in all_videos.items():
        vid_title = truncate_title(vid['snippet']['title'], 60)
        print_detail(f'  - [{vid_id}] {vid_title}')
        ytutil.save_video_meta(vid, data_dir, overwrite=False)

    unavail_count = len(all_video_ids) - len(all_videos)
    print_info(f'Archived metadata for {len(playlists)} playlists, {len(all_videos)} videos. '
               f'Skipped {unavail_count} unavailable videos.')
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
