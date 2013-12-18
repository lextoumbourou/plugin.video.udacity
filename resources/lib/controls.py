from xbmcswift2 import xbmcgui, xbmc
import math
import os

MEDIA_DIR = os.path.dirname(
    os.path.dirname(__file__)) + os.sep + "media" + os.sep

OFFSET_X_MULTIPLIER = 0.65
OFFSET_Y_MULTIPLIER = 0.65


class TextBox(xbmcgui.ControlButton):
    def getContent(self):
        return self.getLabel()

    def updateLabel(self):
        label = self.getLabel()
        keyboard = xbmc.Keyboard(label)
        keyboard.doModal()
        self.setLabel(
            keyboard.getText())

    @property
    def canUpdateLabel(self):
        return True


class RadioButton(xbmcgui.ControlRadioButton):
    def getContent(self):
        return self.isSelected()

    @property
    def canUpdateLabel(self):
        return False


class FormQuiz(xbmcgui.WindowDialog):
    def __init__(self):
        xbmcgui.Window.__init__(self)
        self.width = 1280
        self.height = 720
        self.bottom_height = 70
        self.widget_x_offset = 25
        self.widget_y_offset = 5
        self.widget_y_multiplier_offset = 70
        self.button_width = 100
        self.button_height = 50
        self.text_box_width = 100
        self.text_box_height = 50
        self.button_text_colour = '0xFFFFFFFF'

    def build(
            self, course_id, lesson_id, group_id, quiz_id, quiz_data, udacity):
        self.udacity = udacity
        self.data = quiz_data['data']
        print self.data
        self.widgets = []
        self.udacity.update_activity(
            course_id, lesson_id, group_id, quiz_id, 'NodeVisit')
        bg_image_path = MEDIA_DIR + "blank.png"
        self.addControl(xbmcgui.ControlImage(
            0, 0, self.width, 720, bg_image_path)
        )
        if '_background_image' in self.data:
            url = 'http:' + self.data['_background_image']['serving_url']
            self.addControl(xbmcgui.ControlImage(
                x=0, y=0, width=self.width,
                height=self.height - self.bottom_height, filename=url))

        widgets = self.data['widgets']
        for widget in widgets:
            model = widget['model']
            x = int(math.ceil(
                widget['placement']['x'] * self.width) - self.widget_x_offset)
            y = int(math.ceil(
                widget['placement']['y'] *
                (self.height - self.widget_y_multiplier_offset)) -
                self.widget_y_offset)
            widget_height = int(self.height * widget['placement']['height'])
            widget_width = int(self.width * widget['placement']['width'])

            if model == 'TextInputWidget' or model == 'NumericInputWidget':
                # Not sure why, but needs to be adjusted slightly
                x = x + 20
                obj = TextBox(
                    x=x, y=y, height=widget_height, width=widget_width,
                    label='', textColor="0xFF000000", shadowColor='0xFF000000')
            else:
                obj = RadioButton(
                    x=x, y=y,
                    height=widget_height, width=widget_width,  label='')

            self.addControl(obj)
            self.widgets.append({
                'obj': obj, 'data': widget})

        self.submit_button = xbmcgui.ControlButton(
            x=1100, y=660, width=self.button_width,
            height=self.button_height, shadowColor='0xFF000000',
            label='Submit', font='font13', textColor=self.button_text_colour)
        self.back_button = xbmcgui.ControlButton(
            x=970, y=660, width=self.button_width,
            height=self.button_height, label='Back',
            font='font13', textColor=self.button_text_colour)

        self.addControl(self.submit_button)
        self.addControl(self.back_button)

    def onControl(self, control):
        if control == self.back_button:
            self.close()
            return
        elif control == self.submit_button:
            result = self.udacity.submit_quiz(self.data['key'], self.widgets)
            dialog = xbmcgui.Dialog()
            dialog.ok('Result', result['evaluation']['comment'])
        else:
            for count, widget in enumerate(self.widgets):
                if widget['obj'].canUpdateLabel:
                    self.widgets[count]['obj'].updateLabel()
