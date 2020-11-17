from flask_appbuilder.views import IndexView


class MyIndexView(IndexView):
    index_template = 'index.html'