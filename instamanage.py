import requests
import random
import time
import json
import atexit
import signal
import sys
import datetime
import os.path

if not os.path.isfile('config.json'):
    print 'please create a config.json file (config_sammple.json in root)'
    quit()

with open('config.json', 'r') as fp:
    try:
        config = json.load(fp)
    except:
        print 'invalid config.json file (probably parsing issue)'
        quit()

logged_in = False
logged_in_id = None

user_followers = []
user_following = []

# opt 2/3
num_unfollow = 50
min_to_unfollow = 25
unfollow_delay = 30

session = requests.Session()
csrftoken = ''

url = 'https://www.instagram.com/'
url_login = 'https://www.instagram.com/accounts/login/ajax/'
url_logout = 'https://www.instagram.com/accounts/logout/'
url_follow = 'https://www.instagram.com/web/friendships/%s/follow/'
url_unfollow = 'https://www.instagram.com/web/friendships/%s/unfollow/'

def menu():
    global num_unfollow, min_to_unfollow, unfollow_delay

    print 'instamanage 0.0.1 by ebrian'
    print ''
    print 'choose an option from the choices below. if the option has stars'
    print 'beneath it then that means there are config options that you\'ll'
    print 'be asked to provide answers for. defaults are in brackets[].'
    print ''
    print 'menu:'
    print ''
    print ' [1] - sync followers and following, write to json'
    print ''
    print ' [2] - sync followers and following, write to json, diff, unfollow'
    print '  * c1[50]: # to unfollow'
    print '  * c2[25]: how many minutes to take to unfollow c1'
    print ''
    print ' [3] - load followers and following from file (state.json), diff, unfollow'
    print '  * c1[50]: # to unfollow'
    print '  * c2[25]: how many minutes to take to unfollow c1'
    print ''

    try:
        choice = raw_input('What would you like to do? ')
    except:
        print ''
        quit()

    def config_opt_23():
        global num_unfollow, min_to_unfollow, unfollow_delay

        try:
            opt = int(raw_input('# to unfollow[50]: '))
            num_unfollow = opt if opt else num_unfollow
        except:
            pass

        try:
            opt = int(raw_input('in how long (min)[25]: '))
            min_to_unfollow = opt if opt else min_to_unfollow
        except:
            pass

        unfollow_delay = (min_to_unfollow * 60) / num_unfollow

        print 'unfollow rate set at once every %i seconds' % unfollow_delay

    if choice:
        if int(choice) == 1:
            start_sync()
        elif int(choice) == 2:
            config_opt_23()
            start_sync()
            load_sync()
        elif int(choice) == 3:
            config_opt_23()
            load_sync()
        else:
            menu()
    else:
        menu()


def start_sync():
    login()

    print 'building follower list...'

    # get page 1 of followers
    followers_post = {
        'q': 'ig_user(%i) { \
          followed_by.first(20) { \
            count, \
            page_info { \
              end_cursor, \
              has_next_page \
            }, \
            nodes { \
              id, \
              is_verified, \
              followed_by_viewer, \
              requested_by_viewer, \
              full_name, \
              profile_pic_url, \
              username \
            } \
          } \
        }' % (logged_in_id),
        'ref': 'relationships::follow_list',
        'query_id': '17845270936146575'
    }

    followers = session.post('https://www.instagram.com/query/', data=followers_post)
    data = json.loads(followers.text)

    for node in data['followed_by']['nodes']:
        user_followers.append(node['id'])

    sys.stdout.write('\rfound {0} followers'.format(len(user_followers)))
    sys.stdout.flush()

    while data['followed_by']['page_info']['has_next_page']:
        time.sleep(1 + random.random())

        end_cursor = data['followed_by']['page_info']['end_cursor']

        followers_post = {
            'q': 'ig_user(%i) { \
              followed_by.after(%s, 20) { \
                count, \
                page_info { \
                  end_cursor, \
                  has_next_page \
                }, \
                nodes { \
                  id, \
                  is_verified, \
                  followed_by_viewer, \
                  requested_by_viewer, \
                  full_name, \
                  profile_pic_url, \
                  username \
                } \
              } \
            }' % (logged_in_id, end_cursor),
            'ref': 'relationships::follow_list',
            'query_id': '17845270936146575'
        }

        followers = session.post('https://www.instagram.com/query/', data=followers_post)
        data = json.loads(followers.text)

        for node in data['followed_by']['nodes']:
            user_followers.append(node['id'])

        sys.stdout.write('\rfound {0} followers'.format(len(user_followers)))
        sys.stdout.flush()

    print '\ndone finding followers'

    print 'building following list...'

    # get page 1 of following
    following_post = {
        'q': 'ig_user(%i) { \
          follows.first(20) { \
            count, \
            page_info { \
              end_cursor, \
              has_next_page \
            }, \
            nodes { \
              id, \
              is_verified, \
              followed_by_viewer, \
              requested_by_viewer, \
              full_name, \
              profile_pic_url, \
              username \
            } \
          } \
        }' % (logged_in_id),
        'ref': 'relationships::follow_list',
        'query_id': '17845270936146575'
    }

    following = session.post('https://www.instagram.com/query/', data=following_post)
    data = json.loads(following.text)

    for node in data['follows']['nodes']:
        user_following.append(node['id'])

    sys.stdout.write('\rfound {0} following'.format(len(user_following)))
    sys.stdout.flush()

    while data['follows']['page_info']['has_next_page']:
        time.sleep(1 + random.random())

        end_cursor = data['follows']['page_info']['end_cursor']

        following_post = {
            'q': 'ig_user(%i) { \
              follows.after(%s, 20) { \
                count, \
                page_info { \
                  end_cursor, \
                  has_next_page \
                }, \
                nodes { \
                  id, \
                  is_verified, \
                  followed_by_viewer, \
                  requested_by_viewer, \
                  full_name, \
                  profile_pic_url, \
                  username \
                } \
              } \
            }' % (logged_in_id, end_cursor),
            'ref': 'relationships::follow_list',
            'query_id': '17845270936146575'
        }

        following = session.post('https://www.instagram.com/query/', data=following_post)
        data = json.loads(following.text)

        for node in data['follows']['nodes']:
            user_following.append(node['id'])

        sys.stdout.write('\rfound {0} following'.format(len(user_following)))
        sys.stdout.flush()

    print '\ndone finding following'

    diff = set(user_following) - set(user_followers)

    print 'found %i people who you follow but don\'t follow you back' % (len(diff))

    with open('state.json', 'w') as user_state:
        print 'writing data to state.json'

        json.dump({
            'version': '0.0.1',
            'state_date': datetime.datetime.now().isoformat(),
            'followers': {
                'data': user_followers
            },
            'following': {
                'data': user_following
            }
        }, user_state, indent=4, sort_keys=True)
        user_state.close()


def load_sync():
    fp = open('state.json', 'r')
    user_state = json.load(fp)
    fp.close()

    unfollow_list = set(user_state['following']['data']) - set(user_state['followers']['data'])

    if len(unfollow_list) <= 0:
        print 'nobody to unfollow'
        quit()

    if not logged_in:
        login()

    print 'starting to unfollow %i out of %i people' % (num_unfollow, len(unfollow_list))

    left_to_unfollow = num_unfollow

    for id in unfollow_list:
        print 'unfollowing %s' % id

        unfollow = session.post(url_unfollow % id)

        try:
            status = json.loads(unfollow.text)

            if status['status'] != 'ok':
                raise
        except:
            print 'possibly too fast, preventing ban...'
            print 'error received: %s' % unfollow.text
            quit()

        try:
            user_state['following']['data'].remove(id)
        except:
            pass

        fp = open('state.json', 'w')
        json.dump(user_state, fp, indent=4, sort_keys=True)
        fp.close()

        if left_to_unfollow == 0:
            break

        time.sleep(unfollow_delay)
        left_to_unfollow -= 1


def login():
    global logged_in, logged_in_id

    print 'attempting login...'

    session.cookies.update({
        'sessionid': '',
        'mid': '',
        'ig_pr': '1',
        'ig_vw': '1920',
        'csrftoken': '',
        's_network': '',
        'ds_user_id': ''
    })

    login_details = {
        'username': config['username'],
        'password': config['password']
    }

    session.headers.update({
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Length': '0',
        'Host': 'www.instagram.com',
        'Origin': 'https://www.instagram.com',
        'Referer': 'https://www.instagram.com/',
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36'),
        'X-Instagram-AJAX': '1',
        'X-Requested-With': 'XMLHttpRequest'
    })

    # get the csrf token from a typical request
    r = session.get(url)
    session.headers.update({'X-CSRFToken': r.cookies['csrftoken']})

    time.sleep(5 * random.random())

    # do login
    login = session.post(url_login, data=login_details, allow_redirects=True)
    session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
    csrftoken = login.cookies['csrftoken']

    time.sleep(5 * random.random())

    if login.status_code == 200:
        r = session.get('https://www.instagram.com/')
        finder = r.text.find(config['username'])

        if finder != -1:
            print 'logged in successfully'
            logged_in = True

            # populate user info
            time.sleep(3)

            user_info = session.get('https://www.instagram.com/%s/?__a=1' % (config['username']))
            data = json.loads(user_info.text)

            logged_in_id = int(data['user']['id'])
        else:
            print 'login failed, possible cred issue'
            quit()
    else:
        print 'login failed, non-200'
        print 'code %i found' % (login.status_code)
        quit()


def logout():
    if logged_in:
        time.sleep(5)

        try:
            print 'logging out...'

            logout_post = {'csrfmiddlewaretoken': csrftoken}
            session.post(url_logout, data=logout_post)
        except:
            print 'failed to logout'


signal.signal(signal.SIGTERM, logout)
atexit.register(logout)

menu()