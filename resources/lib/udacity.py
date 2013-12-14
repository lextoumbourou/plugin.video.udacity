import urllib2
import json
import requests
from BeautifulSoup import BeautifulSoup

UDACITY_URL = "https://www.udacity.com"
# Temporary measure. I'll stop faking the UA when I'm done testing - promise!
HEADERS = {
    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'
}

class Udacity(object):
    def __init__(self, auth):
        self.auth = auth

    def get_my_courses(self):
        results = []
        if self.auth.is_authenticated:
            r = requests.get(
                '{0}/api/users/me'.format(UDACITY_URL),
                headers=self.auth.get_request_headers(),
                cookies=self.auth.cookies)
            data = json.loads(r.text[5:])
            enrollments = data['user']['_enrollments']
            current = [e for e in enrollments if e['state'] == 'enrolled']
            send_data = json.dumps({'keys':
                    [e['node_key'] for e in current], 'fresh': False, 'depth': 0})
            course_req = requests.get(
                    '{0}/api/nodes'.format(UDACITY_URL), params={'json':send_data},
                    headers=self.auth.get_request_headers(),
                    cookies=self.auth.cookies)
            course_data = json.loads(course_req.text[5:])
            courses = course_data['references']['Node']
            for key in courses.keys():
                title = courses[key]['title']
                results.append((title, key))

            return results
        else:
            return None

    def get_video_list(self, section):
        results = []
        url = "{0}/api/nodes/{1}".format(UDACITY_URL, section)
        url += "?depth=2&fresh=false&required_behavior=view&projection=classroom"
        r = requests.get(url)
        data = json.loads(r.text[5:])['references']['Node']
        steps = data[section]['steps_refs']
        for step in steps:
            data_obj = data[step['key']]
            title = data_obj['title']
            model = data_obj['model']
            if model == 'Video':
                youtube_id = data_obj['_video']['youtube_id']
                results.append(
                    (title, model, youtube_id, None))
            elif model == 'Exercise':
                if data_obj['lecture_ref']:
                    lecture_key = data_obj['lecture_ref'].get('key')
                lecture_data = data[lecture_key]
                youtube_id = lecture_data['_video']['youtube_id']
                results.append(
                    (title, 'Video', youtube_id, None))
                quiz_key = data_obj['quiz_ref']['key']
                quiz_data = data[quiz_key]
                results.append(
                    (title + ' (Quiz)', 'Quiz', quiz_key, quiz_data))
                if data_obj['answer_ref']:
                    answer_key = data_obj['answer_ref'].get('key')
                youtube_id = data[answer_key]['_video']['youtube_id']
                title = title + ' (Answer)'
                results.append(
                    (title, 'Video', youtube_id, None))

        return results

    def get_courses(self, level):
        output = []
        r = requests.get("{0}/courses".format(UDACITY_URL))
        soup = BeautifulSoup(r.text)
        courses = soup.find('ul', id='unfiltered-class-list').findAll('li')
        for course in courses:
            title = course.find('span', 'crs-li-title').text
            thumbnail = course.find('span', 'crs-li-thumbnails').find('img')['src']
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
                 "content": widget['obj'].isSelected()})

        answer_data = {
            "submission": {
                "model": "Submission",
                "operation": "GRADE",
                "parts": parts
            }
        }
        data = post(url, json.dumps(answer_data))
        return json.loads(data[5:])

class UdacityAuth(object):
    def __init__(self):
        self.is_authenticated = False
        self.xsrf_token = None
        self.cookies = None

    def _get_xsrf_token(self):
        r = requests.get('{0}/'.format(UDACITY_URL), headers=HEADERS)
        self.xsrf_token = r.cookies['XSRF-TOKEN']

    def authenticate(self, username, password):
        if not self.xsrf_token:
            self._get_xsrf_token()

        url = '{0}/api/session'.format(
            UDACITY_URL)
                    
        r = requests.post(url, data=json.dumps(
            {'udacity': {'username': username, 'password': password}}),
            headers=self.get_request_headers())
        if r.status_code == 200:
            self.is_authenticated = True
            self.cookies = r.cookies
            return True
        else:
            result = json.loads(r.text[5:])
            self.error = result['error']
            return False

    def get_request_headers(self):
        return dict(HEADERS.items() + {
            'xsrf_token': self.xsrf_token,
            'content-type': 'application/json;charset=UTF-8',
        }.items())
