import time, os, shutil
import instagram_scraper as insta
import json
from subprocess import call
from getpass import getpass
import random

insta_profiles = []
delay = 5

def scraper(profile, start, posts, username, passwd):
    imgScraper = insta.InstagramScraper(usernames=[profile], login_user=username, login_pass=passwd, maximum=start + posts - 1, media_metadata=True, latest=True,media_types=['image'])
    imgScraper.scrape()
    # Take last json image data and post in instagram images,  tags and decription
    with open(os.path.join(profile, profile + '.json'), 'r') as j:
        json_data = json.load(j)
        pics = json_data[start  : (start + posts)]
        for pic in pics:
            newstr = (pic["display_url"])
            imgUrl = newstr.split('?')[0].split('/')[-1]
            cap = None
            try:
                cap = pic["edge_media_to_caption"]["edges"][-1]["node"]["text"] + '\n'
                if caption is False:
                    cap = ""
                else:
                    print("Caption: " + cap)
            except:
                cap = ""
                print("No caption exists.")
            random.shuffle(tags)
            tagString = "#" + " #".join(tags[:min(30, len(tags)) - 1])
            call('instapy -u ' + username + ' -p ' + passwd + ' -f ./' + profile + '/' + imgUrl +' -t "' 
                + cap + tagString + '"', shell=True)
            print(imgUrl)
            time.sleep(delay)

    print ("Scraped " + str(posts) + "(Post no. " + str(start) + ", Post no. " + str(start + posts - 1) + ") posts from " + profile)

username = input("Enter your username: ")
passwd = getpass("Enter your password: ")
delay = int(input("Enter the time interval(in seconds) between the successive posts: "))
tags = input("Add a list of tags to be used for posts: ").replace(" ", "").split("#")
cvalue = 'No'
caption = (cvalue[0] == 'Y' or cvalue[0] == 'y')


while(True):
    handle = input("Enter insta profile name: ")
    start = int(input("Enter starting post number by " + handle + " you want to download: "))
    posts = int(input("Enter number of posts by " + handle + " you want to download: "))
    insta_profiles.append((handle, start, posts))
    cont = input("Do you wish to add more profiles?(Yes/No):")
    if cont[0] == 'N' or cont[0] == 'n':
        break

for profile, start, posts in insta_profiles:
    scraper(profile, start, posts, username, passwd)
    profilepath = os.path.join(os.getcwd(), profile)
    if os.path.exists(profilepath):
        shutil.rmtree(profilepath)