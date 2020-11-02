#! /usr/bin/python3

import requests, getpass, json, sys

BASE_URL = 'https://www.instagram.com/'
GRAPH_URL = 'https://www.instagram.com/graphql/query/'
LOGIN_URL = BASE_URL + 'accounts/login/ajax/'
USER_AGENT = 'Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15'

def get_list(token, user_id, key):
	has_next_page = True
	variables = {"id": user_id, "first": 50}
	follow_dict = dict()
	while has_next_page:
		try:
			follow = session.get("{}?query_hash={}&variables={}".format(GRAPH_URL, token, json.dumps(variables, separators=(',', ':')))).json()['data']['user'][key]
		except:
			print(session.get("{}?query_hash={}&variables={}".format(GRAPH_URL, token, json.dumps(variables, separators=(',', ':')))).json())
		has_next_page = follow['page_info']['has_next_page']
		variables['after'] = follow['page_info']['end_cursor']
		for user in follow['edges']:
			follow_dict[user['node']['username']] = {'id': user['node']['id'], 'name': user['node']['full_name']}
	return follow_dict

session = requests.Session()

if len(sys.argv) == 3:
	session.cookies.set('ds_user_id', sys.argv[1])
	session.cookies.set('sessionid', sys.argv[2])
	user_id = sys.argv[1]

	# get token for followers
	profile = session.get("{}".format(BASE_URL), stream=True)
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

	print("Now you can use this script with '{} {} {}'".format(sys.argv[0], cookies['ds_user_id'], cookies['sessionid']))

	check = '"authenticated": true'

	current_result = login.text

	if check not in current_result:
		print(login.text)
		print('Unable to connect with your credentials, please try again')
		exit(1)

	user_id = cookies['ds_user_id']

	# get token for followers
	profile = session.get("{}/{}".format(BASE_URL, USERNAME), stream=True)

for line in profile.iter_lines():
	line = str(line)
	if 'Consumer.js' in line and '<link' in line:
		line = line.split(' ')
		for item in line:
			if 'href' in item:
				script_url = BASE_URL + item[7:-1]

script = session.get(script_url)

line_token = None

for line in script.iter_lines():
	line = str(line)
	if "s=\\\'edge_follow\\\'" in line:
		line_token = line
		break

if not line_token:
	print('An error occured, please try again')
	exit(1)

followers_token = line_token[line_token.index('t="') + 3:]
followers_token = followers_token[0:followers_token.index('"')]
following_token = line_token[line_token.index('n="') + 3:]
following_token = following_token[0:following_token.index('"')]

followers = get_list(followers_token, user_id, 'edge_followed_by')
following = get_list(following_token, user_id, 'edge_follow')

good = sorted(followers.keys() - following.keys())
bad = sorted(following.keys() - followers.keys())
print("{} users follow you, but not you:\n{}\n".format(len(good), ', '.join(good)))
print("{} users do the same with you:\n{}\n".format(len(bad), ', '.join(bad)))
