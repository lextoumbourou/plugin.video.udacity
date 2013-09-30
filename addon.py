from xbmcswift2 import Plugin

from resources.lib import udacity_api as api

plugin = Plugin()


@plugin.route('/')
def index():
    items = [
        {'label': 'Course Catalog',
         'path': plugin.url_for('course_catalog')},
        {'label': 'My Courses (not implemented yet)',
         'path': plugin.url_for('my_courses')}
    ]

    return items


@plugin.route('/course_catalog/')
def course_catalog():
    courses = api.get_courses(None)
    items = [{
        'label': title,
        'path': plugin.url_for('open_course', course_id=course_id),
        'thumbnail': thumbnail
    } for title, course_id, _, thumbnail in courses]

    return items


@plugin.route('/course/<course_id>')
def open_course(course_id):
    items = []
    contents = api.get_course_contents(course_id)
    for title, key, model in contents:
        items.append({
            'label': title,
            'path': plugin.url_for('open_lesson', lesson_key=key)
        })

    return items


@plugin.route('/open_lesson/<lesson_key>')
def open_lesson(lesson_key):
    items = []
    videos = api.get_video_list(lesson_key)
    for title, model, youtube_id, quiz_data in videos:
        if model == 'Video':
            items.append({
                'label': title,
                'path': plugin.url_for('play_lecture', lec_id=youtube_id),
                'is_playable': True,
            })
        elif model == 'Quiz':
            items.append({
                'label': title,
                'path': plugin.url_for('open_quiz', ref_id=''),
            })

    return items


@plugin.route('/my_courses/')
def my_courses():
    return []


@plugin.route('/open_quiz/')
def open_quiz():
    return []


@plugin.route('/lectures/<lec_id>')
def play_lecture(lec_id):
    youtube_url = (
        "plugin://plugin.video.youtube/"
        "?action=play_video&videoid={0}").format(lec_id)
    plugin.set_resolved_url(youtube_url)

if __name__ == '__main__':
    plugin.run()
