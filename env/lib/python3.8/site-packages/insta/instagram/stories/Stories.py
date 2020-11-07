import wget
import os
import json

query_url = 'https://www.instagram.com/graphql/query/'


def is_user_has_stories(stories_query_hash, userid, session):

    global edge_highlight_reels, profile_id
    profile_id = userid
    variables = '{"user_id":"%s","include_chaining":true,"include_reel":true,"include_suggested_users":false,"include_logged_out_extras":false,"include_highlight_reels":true}' % userid

    page = session.get(query_url, params={'query_hash': stories_query_hash, 'variables': variables}).json()['data']['user']

    edge_highlight_reels = page.get('edge_highlight_reels', None)
    if not edge_highlight_reels['edges']:
        return False
    return True


def extract_reel_ids():

    main_node = edge_highlight_reels['edges']

    for sub_node in main_node:
        yield sub_node['node']['id']


def download_reels(reels_media, location):

    for reel in reels_media:
        for item in reel['items']:
            if item['is_video']:
                for video_item in item['video_resources']:
                    video_url = video_item['src']
                    print '[StoryVideo] %s' % video_url.split('?')[0]
                    wget.download(video_url, out=location, bar=None)
            else:
                image_url = item['display_url']
                print '[StoryImage] %s' % image_url.split('?')[0]
                wget.download(image_url, out=location, bar=None)


def download_present_stories(query_hash, session, location):

    variables = {
        "reel_ids": [profile_id],
        "tag_names": [],
        "location_ids": [],
        "highlight_reel_ids": [],
        "precomposed_overlay": False,
        "show_story_viewer_list": True,
        "story_viewer_fetch_count": 50,
        "story_viewer_cursor": ""
    }

    current_status = session.get(query_url, params={'query_hash': query_hash, 'variables': json.dumps(variables)}).json()['data']

    if not current_status['reels_media']:
        return

    download_reels(current_status['reels_media'], location)


def download_stories(query_hash, session, location):

    if not os.path.isdir(location):
        os.makedirs(location)

    download_present_stories(query_hash, session, location)

    highlight_reel_ids = list(extract_reel_ids())
    variables = {
        "reel_ids": [],
        "tag_names": [],
        "location_ids": [],
        "highlight_reel_ids": highlight_reel_ids,
        "precomposed_overlay": False,
        "show_story_viewer_list": True,
        "story_viewer_fetch_count": 50,
        "story_viewer_cursor": ""
    }

    reels_media = session.get(query_url, params={'query_hash': query_hash, 'variables': json.dumps(variables)}).json()['data']['reels_media']

    download_reels(reels_media, location)
