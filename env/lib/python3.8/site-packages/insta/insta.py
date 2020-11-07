from instagram.instagram import *
from getpass import getpass
import argparse
import os


def download_user_data(friendname):

    print '\n\n[+]Downloading %s media' % friendname
    query_hash = get_query_hash(friendname, location)

    if not query_hash:
        return

    target_user_profile_id = get_profile_id()

    try:

        download_media(friendname, query_hash, target_user_profile_id, location)
    except KeyboardInterrupt:
        return


def check_out_dir(output_dir):

    if output_dir:
        if not os.path.isdir(output_dir.strip()):
            print '\nDirectory doesn\'t exist.'
            return
        else:
            return output_dir.strip()
    else:
        return os.getcwd()


def check_login(username, password):

    try:
        status = insta_login(username, password)

        if not status:
            print 'Invalid Username or Password.'
            return
        print '\nLogged in as %s' % username
        return True
    except requests.exceptions.ConnectionError:
        print 'Try again after sometime.'
        return


def main():

    global location
    parser = argparse.ArgumentParser(
        description="""It allows user to download
            photos,videos and statuses of a target user.
            we can specifiy one or more target users.
            Target user should be friend of instagram user
            else it will download profile picture only.

            Examples:


                To download all your's INSTAGRAM all friends media you can execute below command.

                    insta-scraper -u YOUR_INSTAGRAM_USERNAME


                To download  one or more user's media

                    insta-scraper -u YOUR_INSTAGRAM_USERNAME username1 username2


                You can also specify a file containing target usernames to download.

                    insta-scraper -u YOUR_INSTAGRAM_USERNAME -f filename


                You can even specify the target downloads location by using -o option

                    insta-scraper -u YOUR_INSTAGRAM_USERNAME -o destination

            """
    )
    parser.add_argument('-u', '--user', type=str, required=True, help='Your Instagram Username')
    parser.add_argument('-t', '--target-users', nargs='+', help='One or more friends Usernames to download')
    parser.add_argument('-f', '--filename', type=file, help='A file containing target instagram usernames.')
    parser.add_argument('-o', '--output-dir', type=str, help='Output directory to store media')
    args = parser.parse_args()

    location = check_out_dir(args.output_dir)
    if not location:
        return

    password = getpass('Password:')

    if not check_login(args.user, password):
        return

    if args.target_users:
        to_iterate = args.target_users
    elif args.filename:
        to_iterate = args.filename
    else:
        print '\n[*]Collecting usernames........'
        to_iterate = get_friends_list()

    for friend in to_iterate:
        download_user_data(friend.strip())


if __name__ == '__main__':

    main()
