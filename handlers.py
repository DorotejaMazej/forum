import webapp2
import os
import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

from models import Topic, Comment


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        self.response.out.write(template.render(params))

class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        topics = Topic.query(Topic.deleted==False).order(-Topic.created).fetch()
        args = {"topics":topics}
        if user:
            args["username"] = user.nickname()
            args["logout"] = users.create_logout_url("/")
        else:
            args["login"] = users.create_login_url("/")
        self.render_template("index.html", args)

class PostHandler(BaseHandler):
    def get(self, topic_id):
        user = users.get_current_user()
        if user:
            args = {}
            topic = Topic.get_by_id(int(topic_id))
            args["topic"] = topic
            args["username"] = user.nickname()
            args["comments"] = Comment.query(Comment.deleted==False and Comment.the_topic_id==int(topic_id)).order(Comment.created).fetch()
        self.render_template("topic.html", args)

    def post(self, topic_id):
        author = users.get_current_user().nickname()
        content = self.request.get("content")

        if content:
            c = Comment(
                author = author,
                content = content,
                the_topic_id = int(topic_id)
            ).put()
            topic = Topic.get_by_id(int(topic_id)) # wtf now?
            topic.num_comments = topic.num_comments+1
            topic.put()
            self.redirect("/topic/" + str(topic_id))

class NewTopicHandler(BaseHandler):
    def get(self):
        args = {}
        user = users.get_current_user()
        if user:
            args["username"] = user.nickname()
            args["logout"] = users.create_logout_url("/")
        else:
            args["login"] = users.create_login_url("/")
        self.render_template("new-topic.html", args)

    def post(self):
        title = self.request.get("title")
        content = self.request.get("content")
        tags = self.request.get("all-tags").split(",")
        author = users.get_current_user().nickname()
        if title and content and tags:
            t = Topic(title = title, content = content, author=author, tags=tags)
            t.put()
            self.redirect("/")