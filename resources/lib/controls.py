from xbmcswift2 import xbmcgui
import math
import json

# To do:
# * Clean up "magic" values
# * Get cancel button to work
# * Get Submit to work

WIDGET_MAPPING = {
    'TextInputWidget': xbmcgui.ControlTextBox,
     'NumericInputWidget': xbmcgui.ControlTextBox,
     'RadioInputWidget': xbmcgui.ControlRadioButton,
     'CheckboxWidget': xbmcgui.ControlRadioButton,
 }


class FormQuiz(xbmcgui.Window):
    def build(self, data):
        self.width = int(self.getWidth() * 0.60)
        self.height = int(self.getHeight() * 0.60)
        offset_x = int((self.getWidth() * 0.65 - self.width) / 2)
        if '_background_image' in data:
            url = 'http:' + data['_background_image']['serving_url']
            x_pos = 0
            y_pos = 0
            self.addControl(xbmcgui.ControlImage(x=x_pos + offset_x, y=y_pos, width=self.width, height=self.height, filename=url))

        widgets = data['widgets']
        for widget in widgets:
            model = widget['model']
            x = int(math.ceil(widget['placement']['x'] * self.width) - 15) + offset_x
            y = int(math.ceil(widget['placement']['y'] * self.height) - 5)
            widget_height = int(self.height * widget['placement']['height'])
            widget_width = int(self.width * widget['placement']['width'])

            widget_obj = WIDGET_MAPPING[model](
                x=x, y=y,
                height=widget_height, width=widget_width, label='')
            self.addControl(widget_obj)
        next_button = xbmcgui.ControlButton(x = self.width - 100, y = self.height + 5, width = 100, height = 50, label='Submit', font='font13', textColor='0xFFFFFFFF')
        cancel_button = xbmcgui.ControlButton(x = self.width - 230, y = self.height + 5, width = 100, height = 50, label='Cancel', font='font13', textColor='0xFFFFFFFF')
        self.addControl(next_button)
        self.addControl(cancel_button)
