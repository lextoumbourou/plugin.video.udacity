import json
from xbmcswift2 import Plugin, xbmcgui

from resources.lib.udacity import Udacity, UdacityAuth
from resources.lib import controls

plugin = Plugin()


@plugin.route('/')
def index():
    items = [{'label': 'Course Catalog',
             'path': plugin.url_for('course_catalog')},]
    items.append(
        {'label': 'My Courses',
         'path': plugin.url_for('my_courses')},
    )
    items.append(
        {'label': 'Change plugin settings',
         'path': plugin.url_for('open_settings')},
    )

    return items


@plugin.route('/course_catalog/')
def course_catalog():
    udacity = Udacity(None)
    courses = udacity.get_courses(None)
    items = [{
        'label': title,
        'path': plugin.url_for('open_course', course_id=course_id),
        'thumbnail': thumbnail
    } for title, course_id, _, thumbnail in courses]

    return items


@plugin.route('/course/<course_id>')
def open_course(course_id):
    items = []
    udacity = Udacity(None)
    contents = udacity.get_course_contents(course_id)
    for title, key, model in contents:
        items.append({
            'label': title,
            'path': plugin.url_for('open_lesson', course_id=course_id, lesson_key=key)
        })

    return items


@plugin.route('/open_lesson/<course_id>/<lesson_key>')
def open_lesson(course_id, lesson_key):
    items = []
    udacity = Udacity(None)
    videos = udacity.get_video_list(lesson_key)
    for title, model, youtube_id, group_id, asset_id, quiz_data in videos:
        if model == 'Video':
            items.append({
                'label': title,
                'path': plugin.url_for('play_lecture', lec_id=youtube_id),
                'is_playable': True,
            })
        elif model == 'Quiz':
            items.append({
                'label': title,
                'path': plugin.url_for(
                    'open_quiz', course_id=course_id, lesson_key=lesson_key,
                    group_id=group_id, asset_id=asset_id,
                    quiz_data=json.dumps(quiz_data)),
            })

    return items


@plugin.cached_route('/my_courses/')
def my_courses():
    items = []
    auth_storage = plugin.get_storage('auth')
    auth = UdacityAuth(auth_storage)
    username = plugin.get_setting('username')
    password = plugin.get_setting('user_password')
    if auth.authenticate(username, password):
        udacity = Udacity(auth)
        courses = udacity.get_my_courses()
        for title, course_id in courses:
            items.append({
                'label': title,
                'path': plugin.url_for('open_course', course_id=course_id),
            })

        return items
    else:
        return plugin.notify(auth.error)


@plugin.route('/open_settings/')
def open_settings():
    return plugin.open_settings()


@plugin.route('/open_quiz/<course_id>/<lesson_key>/<group_id>/<asset_id>/<quiz_data>')
def open_quiz(course_id, lesson_key, group_id, asset_id, quiz_data):
    auth = UdacityAuth(plugin.get_storage('auth'))
    auth.authenticate(
        plugin.get_setting('username'),
        plugin.get_setting('user_password'))
    udacity = Udacity(auth)
    data = json.loads(quiz_data)
    print data
    new = controls.FormQuiz()
    new.build(course_id, lesson_key, group_id, asset_id, data, udacity)
    new.doModal()
    del new


@plugin.route('/lectures/<lec_id>')
def play_lecture(lec_id):
    youtube_url = (
        "plugin://plugin.video.youtube/"
        "?action=play_video&videoid={0}").format(lec_id)
    return plugin.set_resolved_url(youtube_url)

if __name__ == '__main__':
    plugin.run()
