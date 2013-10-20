import urllib2
import json
import requests
from BeautifulSoup import BeautifulSoup

UDACITY_URL = "https://www.udacity.com"


def get(url):
    """ Return the contents of the page as a string """
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    output = response.read()
    response.close()

    return output.decode('ascii', 'ignore')

def post(url, data):
    """ Post JSON data and return contents of page as string """
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    response = f.read()
    f.close()
    return response

def get_video_list(section):
    results = []
    url = "{0}/api/nodes/{1}".format(UDACITY_URL, section)
    url += "?depth=2&fresh=false&required_behavior=view&projection=classroom"
    output_json = get(url)
    data = json.loads(output_json[5:])['references']['Node']
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
            lecture_key = data_obj['lecture_ref']['key']
            lecture_data = data[lecture_key]
            youtube_id = lecture_data['_video']['youtube_id']
            results.append(
                (title, 'Video', youtube_id, None))
            quiz_key = data_obj['quiz_ref']['key']
            quiz_data = data[quiz_key]
            results.append(
                (title + ' (Quiz)', 'Quiz', quiz_key, quiz_data))
            answer_key = data_obj['answer_ref']['key']
            youtube_id = data[answer_key]['_video']['youtube_id']
            title = title + ' (Answer)'
            results.append(
                (title, 'Video', youtube_id, None))

    return results


def get_courses(level):
    output = []
    html = get("{0}/courses".format(UDACITY_URL))
    soup = BeautifulSoup(html)
    courses = soup.find('ul', id='unfiltered-class-list').findAll('li')
    for course in courses:
        title = course.find('span', 'crs-li-title').text
        thumbnail = course.find('span', 'crs-li-thumbnails').find('img')['src']
        difficulty = course.find('span', 'level-widget')['title']
        url = course.find('a')['href']
        course_id = url.split('/')[-1]
        output.append((title, course_id, difficulty, 'http:' + thumbnail))

    return output


def get_course_contents(course_id):
    output = []
    url = (
        "{0}/api/nodes/{1}"
        "?depth=1&fresh=false&required_behavior=view"
        "&projection=navigation").format(UDACITY_URL, course_id)
    html = get(url)
    data = json.loads(html[5:])
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

def submit_quiz(quiz_id, widgets):
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

if __name__ == '__main__':
    quiz_data = {'key': 48719273}
    print submit_quiz(quiz_data)

