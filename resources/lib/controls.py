from xbmcswift2 import xbmcgui
import math
import json
import udacity as Udacity

# To do:
# * Clean up "magic" values
# * Get cancel button to work
# * Get Submit to work

WIDGET_MAPPING = {
    'TextInputWidget': xbmcgui.ControlTextBox,
     'NumericInputWidget': xbmcgui.ControlTextBox,
     'RadioButtonWidget': xbmcgui.ControlRadioButton,
     'CheckboxWidget': xbmcgui.ControlRadioButton,
 }

OFFSET_X_MULTIPLIER = 0.65
OFFSET_Y_MULTIPLIER = 0.65
WIDGET_X_OFFSET = 15
WIDGET_Y_OFFSET = 5
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
BUTTON_TEXT_COLOUR = '0xFFFFFFFF'


class FormQuiz(xbmcgui.Window):
    def build(self, course_id, lesson_id, group_id, asset_id, data, udacity):
        self.udacity = udacity
        self.data = data
        self.widgets = []
        self.udacity.update_activity(
            course_id, lesson_id, group_id, asset_id, 'NodeVisit')

        self.width = int(self.getWidth() * 0.60)
        self.height = int(self.getHeight() * 0.60)
        offset_x = int((self.getWidth() * OFFSET_X_MULTIPLIER - self.width) / 2)
        if '_background_image' in data:
            url = 'http:' + data['_background_image']['serving_url']
            x_pos = y_pos = 0
            self.addControl(xbmcgui.ControlImage(
                x=x_pos + offset_x, y=y_pos, width=self.width,
                height=self.height, filename=url))

        widgets = data['widgets']
        for widget in widgets:
            model = widget['model']
            x = int(math.ceil(
                    widget['placement']['x'] * self.width) - WIDGET_X_OFFSET) + offset_x
            y = int(math.ceil(
                    widget['placement']['y'] * self.height) - WIDGET_Y_OFFSET)
            widget_height = int(self.height * widget['placement']['height'])
            widget_width = int(self.width * widget['placement']['width'])

            obj = WIDGET_MAPPING[model](
                x=x, y=y,
                height=widget_height, width=widget_width, label='')
            self.addControl(obj)
            self.widgets.append({
                'obj': obj, 'data': widget})
        self.submit_button = xbmcgui.ControlButton(
            x = self.width - BUTTON_WIDTH, y = self.height + 5, width = BUTTON_WIDTH,
            height = BUTTON_HEIGHT, label='Submit', font='font13', textColor=BUTTON_TEXT_COLOUR)
        self.addControl(self.submit_button)
        self.cancel_button = xbmcgui.ControlButton(
            x = self.width - 230, y = self.height + 5, width = BUTTON_WIDTH,
            height = BUTTON_HEIGHT, label='Cancel', font='font13', textColor=BUTTON_TEXT_COLOUR)
        self.addControl(self.cancel_button)

    def onControl(self, control):
        if control == self.cancel_button:
            self.close()
        elif control == self.submit_button:
            result = self.udacity.submit_quiz(self.data['key'], self.widgets)
            dialog = xbmcgui.Dialog()
            dialog.ok('Result', result['evaluation']['comment'])
            print result
            
