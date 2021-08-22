#! /usr/bin/env python3

import requests, getpass, json, sys

BASE_URL = 'https://www.instagram.com'
API_URL = 'https://i.instagram.com/api/v1/friendships'
LOGIN_URL = BASE_URL + '/accounts/login/ajax/'
USER_AGENT = 'Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15'

def get_list(user_id, key):
	payload = {'max_id': True}
	result_dict = dict()
	while payload['max_id']:
		if payload['max_id'] == True:
			payload['max_id'] = ''
		r = session.get(f"{API_URL}/{user_id}/{key}", params=payload)
		payload['max_id'] = r.json()['next_max_id'] if 'next_max_id' in r.json() else ''
		for user in r.json()['users']:
			result_dict[user['username']] = {'id': user['pk'], 'name': user['full_name']}
	return result_dict

session = requests.Session()

if len(sys.argv) == 3:
	session.cookies.set('ds_user_id', sys.argv[1])
	session.cookies.set('sessionid', sys.argv[2])
	user_id = sys.argv[1]
else:
	USERNAME = input('Username: ')
	PASSWD = getpass.getpass()

	session.headers = {'Referer': BASE_URL, 'user-agent': USER_AGENT}
	session.cookies.set('ig_pr', '1')

	req = session.get(BASE_URL)

	session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})
	login_data = {'username': USERNAME, 'password': PASSWD}
	login = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
	session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})

	cookies = login.cookies

	current_result = login.json()

	if 'authenticated' not in current_result or not current_result['authenticated']:
		print('Unable to connect with your credentials, please try again', file=sys.stderr)
		exit(1)

	print("Now you can use this script with '{} {} {}'".format(sys.argv[0], cookies['ds_user_id'], cookies['sessionid']))

	session.cookies.clear()
	session.headers.clear()

	session.cookies.set('ds_user_id', cookies['ds_user_id'])
	session.cookies.set('sessionid', cookies['sessionid'])

	user_id = cookies['ds_user_id']

# get x-ig-app-id
r = session.get(BASE_URL)

if r.status_code != 200:
	print("Error in status_code ({}): {}".format(r.status_code, r.content), file=sys.stderr)
	exit(1)

for line in r.text.split('\n'):
	if 'ConsumerLibCommon' in line and '<script' in line:
		script = BASE_URL + line.split('src="')[1].split('"')[0]
		break
if not script:
	print('Script not found', file=sys.stderr)
	exit(1)

r = session.get(script)
if r.status_code != 200:
	print("Error in status_code ({}): {}".format(r.status_code, r.content), file=sys.stderr)
	exit(1)
for line in r.text.split('\n'):
	if 'instagramWebDesktopFBAppId=\'' in line:
		session.headers.update({'x-ig-app-id': line.split('instagramWebDesktopFBAppId=\'')[1].split('\'')[0]})
		break

followers = get_list(user_id, 'followers')
following = get_list(user_id, 'following')

good = sorted(followers.keys() - following.keys())
bad = sorted(following.keys() - followers.keys())
print("{} users follow you, but not you:\n{}\n".format(len(good), ', '.join(good)))
print("{} users do the same with you:\n{}\n".format(len(bad), ', '.join(bad)))
