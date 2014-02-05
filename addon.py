import json
from xbmcswift2 import Plugin, xbmcgui

from resources.lib.udacity import Udacity, UdacityAuth
from resources.lib import controls

plugin = Plugin()


@plugin.route('/')
def index():
    items = [
        {'label': plugin.get_string(30004),
         'path': plugin.url_for('course_catalog')},
    ]

    auth_storage = plugin.get_storage('auth')
    auth = UdacityAuth(auth_storage)
    username = plugin.get_setting('username')
    password = plugin.get_setting('user_password')

    # Default settings string displays Login unless logged in
    setting_string_id = 30012
    if username and password:
        if auth.authenticate(username, password):
            items.append(
                {'label': plugin.get_string(30005),
                 'path': plugin.url_for('my_courses')})
            setting_string_id = 30006
        else:
            plugin.notify(auth.error)
            plugin.set_setting('user_password', '')

    items.append(
        {'label': plugin.get_string(setting_string_id),
         'path': plugin.url_for('open_settings')}
    )

    return items


@plugin.route('/course_catalog/')
def course_catalog():
    udacity = Udacity(None)
    courses = udacity.get_courses()
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
            'path': plugin.url_for(
                'open_lesson', course_id=course_id, lesson_id=key)
        })

    return items


@plugin.route('/open_lesson/<course_id>/<lesson_id>')
def open_lesson(course_id, lesson_id):
    items = []
    auth_storage = plugin.get_storage('auth')
    auth = UdacityAuth(auth_storage)
    udacity = Udacity(auth)

    contents = udacity.get_lesson_contents(lesson_id)
    for content in contents:
        if content['model'] == 'Video':
            items.append({
                'label': content.get('title'),
                'path': plugin.url_for(
                    'play_video', course_id=course_id, lesson_id=lesson_id,
                    asset_id=content.get('key'),
                    youtube_id=content['_video'].get('youtube_id')),
                'is_playable': True,
            })
        elif content['model'] == 'Exercise':
            items.append({
                'label': content.get('title'),
                'path': plugin.url_for(
                    'play_exercise', course_id=course_id,
                    lesson_id=lesson_id, group_id=content.get('key'),
                    lecture=json.dumps(content.get('lecture_ref')),
                    quiz=json.dumps(content.get('quiz_ref')),
                    answer=json.dumps(content.get('answer_ref'))),
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
    old_username = plugin.get_setting('username')
    old_password = plugin.get_setting('user_password')
    plugin.open_settings()
    # If the username or password was changed, flush any saved cookies/tokens
    if (old_username != plugin.get_setting('username') or
            old_password != plugin.get_setting('user_password')):
        auth_storage = plugin.get_storage('auth')
        auth_storage['cookies'] = None
        auth_storage['xsrf-token'] = None
        auth_storage.sync()
    return plugin.redirect(plugin.url_for('index'))


@plugin.route((
    '/play_exercise/<course_id>/<lesson_id>/<group_id>'
    '/<lecture>/<quiz>/<answer>'))
def play_exercise(
        course_id, lesson_id, group_id, lecture, quiz, answer):
    lecture_data = json.loads(lecture)
    quiz_data = json.loads(quiz)
    answer_data = json.loads(answer)
    items = []
    if lecture_data:
        items.append({
            'label': plugin.get_string(30007),
            'path': plugin.url_for(
                'play_video', course_id=course_id,
                lesson_id=lesson_id, asset_id=lecture_data.get('key'),
                youtube_id=lecture_data['data']['_video'].get(
                    'youtube_id')),
            'is_playable': True
        })
    if quiz_data:
        items.append({
            'label': plugin.get_string(30008),
            'path': plugin.url_for(
                'load_quiz', course_id=course_id, lesson_id=lesson_id,
                group_id=group_id, quiz=quiz),
        })
    if answer_data and answer_data['data']:
        items.append({
            'label': plugin.get_string(30009),
            'path': plugin.url_for(
                'play_video', course_id=course_id,
                lesson_id=lesson_id, asset_id=answer_data.get('key'),
                youtube_id=answer_data['data']['_video'].get(
                    'youtube_id')),
            'is_playable': True
        })

    return items


@plugin.route('/load_quiz/<course_id>/<lesson_id>/<group_id>/<quiz>')
def load_quiz(course_id, lesson_id, group_id, quiz):
    quiz_data = json.loads(quiz)
    auth = UdacityAuth(plugin.get_storage('auth'))
    auth.authenticate(
        plugin.get_setting('username'),
        plugin.get_setting('user_password'))
    udacity = Udacity(auth)
    last_quiz_data = udacity.get_last_quiz_submission(quiz_data['key'])
    if quiz_data['data']['model'] == 'ProgrammingQuiz':
        dialog = xbmcgui.Dialog()
        dialog.ok(
            plugin.get_string(30010),
            plugin.get_string(30011))
    else:
        new = controls.FormQuiz()
        new.build(
            course_id, lesson_id, group_id, quiz_data['key'],
            quiz_data, last_quiz_data, udacity, plugin)
        new.doModal()


@plugin.route('/lectures/<course_id>/<lesson_id>/<asset_id>/<youtube_id>')
def play_video(course_id, lesson_id, asset_id, youtube_id):
    youtube_url = (
        "plugin://plugin.video.youtube/"
        "?action=play_video&videoid={0}").format(youtube_id)

    return plugin.set_resolved_url(youtube_url)

if __name__ == '__main__':
    plugin.run()
