from wtforms import Form, StringField, SubmitField
from wtforms.validators import DataRequired
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3TextAreaFieldWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import widgets


class BS3TextAreaFieldWidget_1(widgets.TextArea):
    def __call__(self, field, **kwargs):
        kwargs["class"] = u"form-control"
        kwargs["rows"] = 10
        if field.label:
            kwargs["placeholder"] = field.label.text
        return super(BS3TextAreaFieldWidget_1, self).__call__(field, **kwargs)


class BS3ButtonFieldWidget(widgets.SubmitInput):
    def __call__(self, field, **kwargs):
        kwargs["class"] = u"form-control"
        #if field.label:
        #    kwargs["placeholder"] = field.label.text
        #if "name_" in kwargs:
        #    field.name = kwargs["name_"]
        return super(BS3ButtonFieldWidget, self).__call__(field, **kwargs)


class YamlForm(DynamicForm):
    baserun = StringField(('baserun'),
                          description=(''),
                          validators=[DataRequired()],
                          widget=BS3TextFieldWidget())
    testrun = StringField(('testrun'),
                          description=(''),
                          validators=[DataRequired()],
                          widget=BS3TextFieldWidget())
    yaml1 = StringField(('testrun_results config'),
                        description=(''),
                        validators=[DataRequired()],
                        widget=BS3TextAreaFieldWidget_1())
    yaml2 = StringField(('benchmark_results config'),
                        description=(''),
                        validators=[DataRequired()],
                        widget=BS3TextAreaFieldWidget_1())
    yaml3 = StringField(('benchmark_metadata config'),
                        description=(''),
                        validators=[DataRequired()],
                        widget=BS3TextAreaFieldWidget_1())
    #reset = SubmitField("Reset",widget=BS3ButtonFieldWidget())


class NewTestrunForm(DynamicForm):
    testrun = StringField(
        ('testrun'),
        description=('Note: duplicate testruns are not allowed'),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget())
