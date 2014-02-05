import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from resources.lib.udacity import Udacity, UdacityAuth
from resources.lib.utils import widgets_to_answer

class MockWidget():
    def getContent(self):
        return True


class UnitTests(unittest.TestCase):
    def test_return_answer_data_from_list_of_widgets(self):
        mock_1 = MockWidget()
        mock_2 = MockWidget()
        widgets = [
            {'data': {'marker': True},
             'obj': mock_1},
            {'data': {'marker': True},
             'obj': mock_2},
        ]
        result = widgets_to_answer(widgets)
        self.assertTrue('submission' in result)
        self.assertTrue(result['submission']['parts'][0]['content'])

    def test_dont_fail_when_answer_data_empty(self):
        data = {
            '382888632': {
                'quiz_ref': {
                    'ref': 'Node',
                    'key': '381838603'
                },
                'answer_ref': None,
                'lecture_ref': None,
                'model': 'Exercise',
            },
            '313947755': {
                'steps_refs': [{
                    'key': '382888632'
                }],
            },
            '381838603': {'model': 'Quiz'},
        }
        udacity = Udacity(None)
        results = udacity.process_lesson_contents(data, '313947755')
        print results
        self.assertTrue(not results[0]['answer_ref'])

    def test_dont_fail_when_no_image_data(self):
        data =  {
            'st101': {
                'title': 'Test 1',
                'catalog_entry': {
                    'subtitle': 'Making Decisions Based on Data',
                    'level': 'beginner',
                    '_image': None,
                    'short_summary': 'Summary!',
                },
                'model': 'Lesson',
                '_available': True
            }
        }
        udacity = Udacity(None)
        results = udacity.process_courses(data)
        # Check that the thumbnail field in the tuple is None
        self.assertTrue(results[0][3] == None)

    def test_only_include_available_courses(self):
        data =  {
            'st101': {
                'title': 'Test 1',
                'catalog_entry': {
                    'subtitle': 'Making Decisions Based on Data',
                    'level': 'beginner',
                    '_image': None,
                    'short_summary': 'Summary!',
                },
                'model': 'Lesson',
                '_available': False
            }
        }
        udacity = Udacity(None)
        results = udacity.process_courses(data)
        # Check that the thumbnail field in the tuple is None
        self.assertTrue(len(results) == 0)


class OfflineTest(unittest.TestCase):
    def test_return_true_when_cookies_and_token_are_set(self):
        auth = UdacityAuth(
            {'xsrf_token': 'SOMEVALUE',
             'cookies': 'ANOTHERVALUE'})
        self.assertTrue(auth.authenticate('test', 'pass'))


class ApiTests(unittest.TestCase):
    def test_get_lesson_contents(self):
        ud = Udacity(None)
        contents = ud.get_lesson_contents('308873795')
        self.assertTrue(type(contents) == list)
        self.assertTrue(type(contents[0]) == dict)

    def test_get_courses(self):
        ud = Udacity(None)
        courses = ud.get_courses(None)
        self.assertTrue(type(courses) == list)

    def test_get_courses_filters_results(self):
        level = 'Beginner'
        ud = Udacity(None)
        courses = ud.get_courses(level)
        self.assertTrue(all([c[2] == level for c in courses]))

    def test_get_course_contents(self):
        ud = Udacity(None)
        courses = ud.get_course_contents('cs215')
        self.assertTrue(type(courses) == list)
        self.assertTrue(len(courses[0]) == 3)


if __name__ == '__main__':
    unittest.main()
