import argparse
import sys

import rich.console
import rich.table

import ytutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--playlist-id', required=False)
    args = parser.parse_args()

    youtube = ytutil.youtube_init('creds-user.json')

    console = rich.console.Console()
    column = rich.table.Column
    if not args.playlist_id:
        playlists = ytutil.get_playlists(youtube)
        ytutil.save_json_file(playlists, 'data/playlists.json')

        tbl = rich.table.Table(column('ID'),
                               column('Owner'),
                               column('Title'),
                               column('Publish Date', justify='right'),
                               column('Count', justify='right'),
                               show_header=True,
                               header_style="bold",
                               box=rich.table.box.SIMPLE_HEAVY,
                               show_edge=False,
                               show_lines=False,
                               pad_edge=False,
                               padding=(0, 1))

        for pl in playlists:
            tbl.add_row(
                pl['id'],
                pl['snippet']['channelTitle'],
                pl['snippet']['title'],
                pl['snippet']['publishedAt'],
                str(pl['contentDetails']['itemCount']),
            )
    else:
        plitems = ytutil.get_playlist_items(args.playlist_id, youtube)
        ytutil.save_json_file(plitems, f'data/playlist-items-{args.playlist_id}.json')

        videos = ytutil.get_videos([x['contentDetails']['videoId'] for x in plitems], youtube)
        for vid_id, vid in videos.items():
            ytutil.save_json_file(vid, f'data/videos/video-{vid_id}.json')

        tbl = rich.table.Table(column('#', justify='right'),
                               column('Add Date', justify='right'),
                               column('Length', justify='right'),
                               column('Video ID'),
                               column('Channel Name'),
                               column('Title'),
                               show_header=True,
                               header_style="bold",
                               box=rich.table.box.SIMPLE_HEAVY,
                               show_edge=False,
                               show_lines=False,
                               pad_edge=False,
                               padding=(0, 1))

        total_secs = 0
        for plitem in plitems:
            vid_id = plitem['contentDetails']['videoId']
            vid = videos[vid_id]

            video_secs = ytutil.iso_duration_to_seconds(vid['contentDetails']['duration'])
            total_secs += video_secs

            tbl.add_row(
                str(plitem['snippet']['position']),
                plitem['snippet']['publishedAt'],
                ytutil.format_duration(video_secs),
                plitem['contentDetails']['videoId'],
                plitem['snippet']['videoOwnerChannelTitle'],
                plitem['snippet']['title'],
            )
        tbl.add_section()
        tbl.add_row('', '', ytutil.format_duration(total_secs), '', '', '')

    # pprint.pprint(results)
    console.print(tbl)
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
