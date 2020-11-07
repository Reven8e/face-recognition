from bs4 import BeautifulSoup as bs
from stories.Stories import *
from getpass import getpass
import requests
import re
import wget
import os
import json

insta_sess = requests.session()

url = 'https://www.instagram.com'
query_url = 'https://www.instagram.com/graphql/query/'


def get_sidecar_childrens(shortcode):       # Problem in this function need to figure out

    variables = '{"shortcode":"%s","child_comment_count":3,"fetch_comment_count":40,"parent_comment_count":24,"has_threaded_comments":false}' % shortcode

    result = insta_sess.get(query_url, params={'query_hash': sidecar_query_hash, 'variables': variables}).json()

    sidecar_main_node = result['data']['shortcode_media']['edge_sidecar_to_children']['edges']

    return [index['node']['display_url'] for index in sidecar_main_node]


def download_videos(video_short_codes, location):

    if not os.path.isdir(location):
        os.makedirs(location)

    for video_short_code in video_short_codes:
        variables = '{"shortcode":"%s","child_comment_count":3,"fetch_comment_count":40,"parent_comment_count":24,"has_threaded_comments":false}' % video_short_code

        result = insta_sess.get(query_url, params={'query_hash': sidecar_query_hash, 'variables': variables}).json()
        video_url = result['data']['shortcode_media']['video_url']
        print '[Video] %s' % video_url.split('?')[0]
        wget.download(video_url, out=location, bar=None)


def download(images, video_short_codes, location):

    if images:
        images_location = os.path.join(location, "Images")
        if not os.path.isdir(images_location):
            os.makedirs(images_location)
        for image in images:
            print '[Image] %s' % image.split('?')[0]
            wget.download(image, out=images_location, bar=None)

    if video_short_codes:
        download_videos(video_short_codes, os.path.join(location, 'Videos'))


def grab_all_images(edges):

    for edge in edges:

        if edge['node']['__typename'] == 'GraphSidecar':
            yield get_sidecar_childrens(edge['node']['shortcode'])
        else:
            yield edge['node']['display_url']


def grab_video_shortcodes(edges):

    for edge in edges:
        if edge['node']['__typename'] == 'GraphVideo':
            yield edge['node']['shortcode']


def get_csrf_token(url):

    insta_sess.get(url)
    return dict(insta_sess.cookies)['csrftoken']


def scrape_data(edges, downloads_location):

    imgs = list(grab_all_images(edges))

    videos = list(grab_video_shortcodes(edges))

    images = []
    for img in imgs:
        if isinstance(img, list):
            images.extend(img)
        else:
            images.append(img)

    download(images, videos, downloads_location)


def insta_login(username, password):

    csrf_token = get_csrf_token('https://www.instagram.com/accounts/login/')

    headers = {
        'x-csrftoken': csrf_token,
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }

    login_status = insta_sess.post('https://www.instagram.com/accounts/login/ajax/', data={'username': username, 'password': password, 'queryParams': '{"source": "auth_switcher"}'}, headers=headers).json()

    try:
        if login_status['authenticated']:
            return True

        return False
    except KeyError:

        check_point_url = url + login_status['checkpoint_url']

        insta_sess.post(check_point_url, data={'choice': '0'}, headers=headers)

        security_code = getpass('Enter OTP: ')
        status = insta_sess.post(check_point_url, data={'security_code': security_code}, headers=headers).content

        if 'profile_pic_url' in status:
            return True

        print 'Incorrect OTP'
        return False


def extract_friends(resp, friendslist):

    for node in resp['edges']:
        friendslist.append(node['node']['username'])


def get_friends_list():

    home_url = 'https://www.instagram.com/'
    owner_homepage = insta_sess.get(home_url).content
    owner_user_name = re.search(r'username":"[\w\d\-\@]+', owner_homepage).group().split('"')[-1]
    owner_user_id = insta_sess.get('https://www.instagram.com/%s' % owner_user_name, params={'__a': 1}).json()['graphql']['user']['id']

    page = url + re.search(r'/static/bundles/metro/consumer.js/[\w\d]+.js', owner_homepage, re.IGNORECASE).group()
    friends_query_hash = re.search(r'n="[\w\d]+', insta_sess.get(page).content).group().split('"')[-1]
    variables = {
        "id": owner_user_id,
        "include_reel": True,
        "fetch_mutual": False,
        "first": 24
    }

    friendslist = []

    main_resp = insta_sess.get('https://www.instagram.com/graphql/query/', params={'query_hash': friends_query_hash, 'variables': json.dumps(variables)}).json()['data']['user']['edge_follow']
    extract_friends(main_resp, friendslist)
    has_next_page_ = main_resp['page_info']['has_next_page']
    if has_next_page_:
        variables['first'] = 12
        variables['after'] = main_resp['page_info']['end_cursor']

    while has_next_page_:

        data = insta_sess.get('https://www.instagram.com/graphql/query/', params={'query_hash': friends_query_hash, 'variables': json.dumps(variables)}).json()['data']['user']['edge_follow']
        extract_friends(data, friendslist)
        has_next_page_ = data['page_info']['has_next_page']
        variables['after'] = data['page_info']['end_cursor']
    return friendslist


def get_query_hash(target_user, location):

    global profile_url_content, query_hash, sidecar_query_hash, profile_inital_json_response, stories_status, story_downloader_query_hash

    profile_url = url + '/' + target_user
    profile_url_content = insta_sess.get(profile_url).content

    try:
        profile_inital_json_response = insta_sess.get('https://www.instagram.com/%s' % target_user, params={'__a': 1}).json()
    except ValueError:
        print 'No instagram account found with given username.'
        return False

    # profile_soup = bs(profile_url_content, 'html.parser')

    # query_hash
    # query_hash_page = url + profile_soup.find('link', attrs={'rel': 'preload', 'as': 'script', 'type': 'text/javascript', 'crossorigin': 'anonymous'})['href']

    query_hash_page = url + re.search(r'/static/bundles/metro/ProfilepageContainer.js/[\w\d]+.js', profile_url_content, re.IGNORECASE).group()

    profileContainerResponse = insta_sess.get(query_hash_page).content
    query_hash = re.search(r's.pagination},queryId:"[\d\w]+', profileContainerResponse).group().split('"')[-1]

    # sidecar hash
    side_car_hash_page = url + re.search(r'/static/bundles/metro/consumer.js/[\w\d]+.js', profile_url_content, re.IGNORECASE).group()
    sidecar_query_hash_response = insta_sess.get(side_car_hash_page).content
    sidecar_query_hash = re.search(r'var u="[\w\d]+",s', sidecar_query_hash_response).group().split('"')[1]

    # stories_hash
    stories_hash = re.search(r'var u="[\w\d]+', profileContainerResponse).group().split('"')[-1]

    # stories status
    stories_status = is_user_has_stories(stories_hash, profile_inital_json_response['graphql']['user']['id'], insta_sess)

    with open('/home/naveen/Desktop/new.txt', 'w') as outfile:
        outfile.write(profile_url_content)
    story_downloader_query_hash_page = insta_sess.get(url + re.search(r'/static/bundles/metro/consumer.js/[\w\d]+.js', profile_url_content, re.IGNORECASE).group()).content
    story_downloader_query_hash = re.search(r'var \w=50,\w="[\w\d]+', story_downloader_query_hash_page).group().split('"')[-1]

    # if edges are zero user may not be your friend or user has not uploaded any content yet.
    if not profile_inital_json_response['graphql']['user']['edge_owner_to_timeline_media']['edges']:
        target_dir = os.path.join(location, target_user)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

        wget.download(profile_inital_json_response['graphql']['user']['profile_pic_url_hd'], out=target_dir, bar=None)
        print '[+] Profile Pic downloaded.'

        # checking if user has atleast any stories and downloading them.

        if stories_status:
            print '\n[+]Downloading Stories.\n'
            download_stories(story_downloader_query_hash, insta_sess, os.path.join(target_dir, 'Stories'))
        return False

    return query_hash


def get_profile_id():

    return profile_inital_json_response['graphql']['user']['id']


def update_variables(profile_id, end_cursor):

    variables = '{"id":"%s","first":12,"after":"%s"}' % (profile_id, end_cursor)
    return variables


def download_media_sequence(root_node, query_hash, target_user_profile_id, location):

    if stories_status:
        print '\nDownloading Stories.'
        download_stories(story_downloader_query_hash, insta_sess, os.path.join(location, 'Stories'))

    user_node = root_node['edge_owner_to_timeline_media']

    while True:
        scrape_data(user_node['edges'], location)
        has_next_page = user_node['page_info']['has_next_page']
        if not has_next_page:
            return
        cursor = user_node['page_info']['end_cursor']
        variables = update_variables(target_user_profile_id, cursor)
        user_node = insta_sess.get(query_url, params={'query_hash': query_hash, 'variables': variables}).json()['data']['user']['edge_owner_to_timeline_media']


def download_media(target_user, query_hash, target_user_profile_id, location):

    global profile_pic_url

    downloads_location = os.path.join(location, target_user)

    root_node = profile_inital_json_response['graphql']['user']
    profile_pic_url = root_node['profile_pic_url_hd']

    if not os.path.isdir(downloads_location):
        os.makedirs(downloads_location)

    wget.download(profile_pic_url, out=downloads_location, bar=None)
    print '[+]Profile picture downloaded.'

    download_media_sequence(root_node, query_hash, target_user_profile_id, downloads_location)
