# import argparse
import argparse
import collections
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
    parser = argparse.ArgumentParser()
    # parser.add_argument('-p', '--playlist-id', required=False)
    parser.add_argument('--list-unavailable',
                        default=False,
                        action='store_true',
                        help='List known details on all unavailable videos found in playlists')
    args = parser.parse_args()

    data_dir = pathlib.Path(os.path.dirname(__file__)) / 'data'
    youtube = ytutil.youtube_init('creds-user.json')

    print_info('Retrieving playlists')
    playlists = ytutil.get_playlists(youtube)

    print_info(f'Archiving list of {len(playlists)} playlists')
    ytutil.save_playlists(playlists, data_dir, overwrite=True)

    all_items = {}
    all_video_ids = []
    vid_playlists = collections.defaultdict(list)

    for pl_display_num, pl_id in enumerate(sorted(playlists.keys())):
        pl = playlists[pl_id]
        pl_name = pl['snippet']['title']

        print_info(f'[{pl_display_num + 1}/{len(playlists)}] {pl_name}')
        pl_items = ytutil.get_playlist_items(pl_id, youtube)
        for item in pl_items:
            vid_id = item['contentDetails']['videoId']
            all_video_ids.append(vid_id)
            vid_playlists[vid_id].append(pl_id)
            if vid_id not in all_items:
                all_items[vid_id] = item

        print_detail(f'  - Archiving metadata for {len(pl_items)} playlist items')
        ytutil.save_playlist_items(pl_id, pl_items, data_dir, overwrite=True)

    all_video_ids = list(set(all_video_ids))
    print_info(f'Retrieving video metadata for {len(all_video_ids)} videos')
    all_videos = ytutil.get_videos(all_video_ids, youtube)

    print_info(f'Archiving video metadata for {len(all_videos)} videos')
    for vid_id, vid in all_videos.items():
        vid_title = truncate_title(vid['snippet']['title'], 60)
        print_detail(f'  - [{vid_id}] {vid_title}')
        ytutil.save_video_meta(vid, data_dir, overwrite=False)

    if args.list_unavailable:
        unavail_video_ids = all_video_ids - all_videos.keys()
        print_info(f'Unavailable videos ({len(unavail_video_ids)}):')
        for vid_id in unavail_video_ids:
            item_details = all_items[vid_id]['snippet']
            item_added = item_details['publishedAt'].split('T')[0]
            vid_title = item_details['title']
            item_pl_names = sorted(
                [playlists[x]['snippet']['title'] for x in vid_playlists[vid_id]])
            print_detail(
                f"  - [{vid_id}] [added {item_added}] {vid_title} ({', '.join(item_pl_names)})")

    unavail_count = len(all_video_ids) - len(all_videos)
    print_info(f'Archived metadata for {len(playlists)} playlists, {len(all_videos)} videos. '
               f'Skipped {unavail_count} unavailable videos.')
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
