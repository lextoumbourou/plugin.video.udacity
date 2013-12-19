import json
import datetime as dt

import requests
from BeautifulSoup import BeautifulSoup

UDACITY_URL = "https://www.udacity.com"
# Temporary measure. I'll stop faking the UA when I'm done testing - promise!
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36")
HEADERS = {'user-agent': USER_AGENT}


class Udacity(object):
    def __init__(self, auth):
        self.auth = auth

    def update_activity(
            self, course_id, lesson_id, group_id, asset_id, activity_type):
        occurence_time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data = {'items': [
            {'occurrence_time': occurence_time, 'content_context': [
                {'tag': 'c-', 'node_key': course_id},
                {'tag': 'l-', 'node_key': lesson_id},
                {'tag': "e-", "node_key": group_id},
                {'tag': "m-", "node_key": asset_id}],
                'data': {'model': activity_type}}],
            'current_time': occurence_time}

        r = requests.post(
            '{0}/api/activity'.format(UDACITY_URL),
            data=json.dumps(data), headers=self.auth.get_request_headers(),
            cookies=self.auth.get_cookies())

        if not r.status_code == 200:
            self.error = r.text
            return False

        return True

    def get_my_courses(self):
        results = []
        if self.auth.is_authenticated:
            r = requests.get(
                '{0}/api/users/me'.format(UDACITY_URL),
                headers=self.auth.get_request_headers(),
                cookies=self.auth.get_cookies())
            data = json.loads(r.text[5:])
            enrollments = data['user']['_enrollments']
            current = [e for e in enrollments if e['state'] == 'enrolled']
            send_data = json.dumps(
                {'keys':
                    [e['node_key'] for e in current],
                    'fresh': False, 'depth': 0})
            course_req = requests.get(
                '{0}/api/nodes'.format(UDACITY_URL),
                params={'json': send_data},
                headers=self.auth.get_request_headers(),
                cookies=self.auth.get_cookies())
            course_data = json.loads(course_req.text[5:])
            courses = course_data['references']['Node']
            for key in courses.keys():
                title = courses[key]['title']
                results.append((title, key))

            return results
        else:
            return None

    def get_lesson_contents(self, section):
        results = []
        url = "{0}/api/nodes/{1}".format(UDACITY_URL, section)
        url += (
            "?depth=2&fresh=false&required_behavior=view&projection=classroom")
        r = requests.get(url)
        data = json.loads(r.text[5:])['references']['Node']
        steps = data[section]['steps_refs']
        for step in steps:
            node = data[step['key']]

            # Push the quiz and lecture data into the dictionary
            # to support XBMC's stateless nature
            if node['model'] == 'Exercise':
                if node['lecture_ref']:
                    lecture_key = node['lecture_ref'].get('key')
                    node['lecture_ref']['data'] = data[lecture_key]
                if node['quiz_ref']:
                    quiz_key = node['quiz_ref']['key']
                    node['quiz_ref']['data'] = data[quiz_key]
                if node['answer_ref']:
                    answer_key = node['answer_ref']['key']
                    node['answer_ref']['data'] = data[answer_key]

            results.append(node)

        return results

    def get_courses(self, level):
        output = []
        r = requests.get("{0}/courses".format(UDACITY_URL))
        soup = BeautifulSoup(r.text)
        courses = soup.find('ul', id='unfiltered-class-list').findAll('li')
        for course in courses:
            title = course.find('span', 'crs-li-title').text
            thumbnail = course.find(
                'span', 'crs-li-thumbnails').find('img')['src']
            difficulty = course.find('span', 'level-widget')['title']
            url = course.find('a')['href']
            course_id = url.split('/')[-1]
            output.append((title, course_id, difficulty, 'http:' + thumbnail))

        return output

    def get_course_contents(self, course_id):
        output = []
        url = (
            "{0}/api/nodes/{1}"
            "?depth=1&fresh=false&required_behavior=view"
            "&projection=navigation").format(UDACITY_URL, course_id)
        r = requests.get(url)
        data = json.loads(r.text[5:])
        steps = data['references']['Node'][course_id]['steps_refs']
        for step in steps:
            try:
                step_data = data['references']['Node'][step['key']]
            except KeyError:
                continue
            title = step_data['title']
            key = step_data['key']
            model = step_data['model']
            output.append(
                (title, key, model))

        return output

    def submit_quiz(self, quiz_id, widgets):
        url = "{0}/api/nodes/{1}/evaluation?_method=GET".format(
            UDACITY_URL, quiz_id)
        parts = []
        for widget in widgets:
            parts.append(
                {"model": "SubmissionPart",
                 "marker": widget['data']['marker'],
                 "content": widget['obj'].getContent()})

        answer_data = {
            "submission": {
                "model": "Submission",
                "operation": "GRADE",
                "parts": parts
            }
        }
        r = requests.post(
            url, data=json.dumps(answer_data),
            headers=self.auth.get_request_headers())
        return json.loads(r.text[5:])


class UdacityAuth(object):
    def __init__(self, auth_stored):
        """
        params:
            auth_stored - persistant storage object from get_storage() function
        """
        self.is_authenticated = False
        self.auth_stored = auth_stored

    def get_xsrf_token(self, force=False):
        if not self.auth_stored.get('xsrf_token') or force:
            r = requests.get('{0}/'.format(UDACITY_URL), headers=HEADERS)
            if r.status_code == 200:
                self.auth_stored['xsrf_token'] = r.cookies['XSRF-TOKEN']

        return self.auth_stored.get('xsrf_token')

    def get_cookies(self):
        return self.auth_stored.get('cookies')

    def authenticate(self, username, password):
        if not username or not password:
            self.error = 'Username and password required'
            return False

        if (self.auth_stored.get('cookies') and
                self.auth_stored.get('xsrf_token')):
            self.is_authenticated = True
            return True

        if not self.get_xsrf_token(force=True):
            self.error = "Can't obtain xsrf token"
            return False

        url = '{0}/api/session'.format(
            UDACITY_URL)

        r = requests.post(url, data=json.dumps(
            {'udacity': {'username': username, 'password': password}}),
            headers=self.get_request_headers())
        if r.status_code == 200:
            self.is_authenticated = True
            self.auth_stored['cookies'] = r.cookies
            return True
        else:
            result = json.loads(r.text[5:])
            self.error = result['error']
            return False

    def get_request_headers(self):
        return dict(HEADERS.items() + {
            'xsrf_token': self.get_xsrf_token(),
            'content-type': 'application/json;charset=UTF-8',
        }.items())

if __name__ == '__main__':
    ud = Udacity(None)
    print ud.get_lesson_contents('308873795')
