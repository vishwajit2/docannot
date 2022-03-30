

from django.db import models
from django.db.models.fields import CharField, IntegerField, BooleanField, TextField, DateTimeField, EmailField
from django.db.models.fields.related import ForeignKey, OneToOneField
from datetime import datetime
import time
import pytz
import calendar
from django.utils import timezone
import hashlib
import uuid


class User(models.Model):
    email = EmailField(max_length=63, unique=True)
    firstname = CharField(max_length=63, blank=True, null=True)
    lastname = CharField(max_length=63, blank=True, null=True)
    pseudonym = CharField(max_length=63, blank=True, null=True)
    password = CharField(max_length=63, blank=True,
                         null=True)      # old; should be null
    # new secure authentication
    salt = CharField(max_length=32, blank=False, null=True)
    saltedhash = CharField(max_length=128, blank=False,
                           null=True)    # new secure authentication
    confkey = CharField(max_length=63, blank=True, null=True)
    guest = BooleanField(default=False)
    valid = BooleanField(default=False)

    def __unicode__(self):
        return "%s %s: %s %s <%s>" % (self.__class__.__name__, self.id,  self.firstname, self.lastname, self.email)

    # Returns 'True' if password is correct, 'False' othrewise
    def authenticate(self, password):
        user_hash = hashlib.sha512(password.encode(
            'ascii', 'xmlcharrefreplace') + self.salt.encode('ascii', 'xmlcharrefreplace')).hexdigest()
        return (self.saltedhash == user_hash)

    # Updates 'salt' and 'saltedhash' to correspond to new password
    # this method does notcall 'save'
    def set_password(self, password):
        self.salt = uuid.uuid4().hex
        self.saltedhash = hashlib.sha512(password.encode(
            'ascii', 'xmlcharrefreplace') + self.salt.encode('ascii', 'xmlcharrefreplace')).hexdigest()
        return


# old: ensemble
class Ensemble(models.Model):
    SECTION_ASSGT_NULL = 1
    SECTION_ASSGT_RAND = 2
    SECTION_ASSGT_TYPES = ((SECTION_ASSGT_NULL, "NULL"),
                           (SECTION_ASSGT_RAND, "RANDOM"))
    # old: name text
    name = CharField(max_length=255)
    description = CharField(max_length=255, default="No description available")
    allow_staffonly = BooleanField(
        default=True, verbose_name="Allow users to write 'staff-only' comments")
    allow_anonymous = BooleanField(
        default=True, verbose_name="Allow users to write anonymous comments")
    allow_tag_private = BooleanField(
        default=True, verbose_name="Allow users to make comments private to tagged users only")
    allow_guest = BooleanField(
        default=False, verbose_name="Allow guests (i.e. non-members) to access the site")
    invitekey = CharField(max_length=63,  blank=True, null=True)      # new
    use_invitekey = BooleanField(
        default=True, verbose_name="Allow users who have the 'subscribe link' to register by themselves")
    allow_download = BooleanField(
        default=True, verbose_name="Allow users to download the PDFs")
    allow_ondemand = BooleanField(
        default=False, verbose_name="Allow users to add any PDF accessible on the internet by pointing to its URL")
    default_pause = BooleanField(
        default=False, verbose_name="Pause on staff Video comments by default")
    section_assignment = IntegerField(
        choices=SECTION_ASSGT_TYPES, default=SECTION_ASSGT_NULL, null=True)
    # data in json format to help processing.
    metadata = TextField(null=True, blank=True)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.name)

    class Meta:
        ordering = ["id"]


class Folder(models.Model):
    parent = ForeignKey("self", on_delete=models.CASCADE, null=True)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    # old: name text
    name = CharField(max_length=255)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.name)


class Section(models.Model):
    name = CharField(max_length=255)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.name)


# TODO: Would be nice to remember the invite text and when it was sent.
class Invite(models.Model):                                                     # old: invite
    key = CharField(max_length=255)                             # old: id
    user = ForeignKey(User, on_delete=models.CASCADE)            # old: id_user
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    # old: admin integer
    admin = BooleanField(default=False)
    ctime = DateTimeField(null=True, default=datetime.now, db_index=True)
    section = ForeignKey(Section, null=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.key)


# TODO: port id_grader functionality (i.e. class sections)
# old: membership
class Membership(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    section = ForeignKey(Section, null=True, on_delete=models.SET_NULL)
    # old: admin integer
    admin = BooleanField(default=False)
    deleted = BooleanField(default=False)
    # Adding guest membership to remember section_id.
    guest = BooleanField(default=False)
    # FIXME Note: To preserve compatibility w/ previous production DB, I also added a default=false at the SQL level for the 'guest' field , so that we don't create null records if using the old framework

    def __unicode__(self):
        return "%s %s: (user %s, ensemble %s)" % (self.__class__.__name__, self.id,  self.user_id, self.ensemble_id)


class Source(models.Model):
    TYPE_PDF = 1
    TYPE_YOUTUBE = 2
    TYPE_HTML5VIDEO = 3
    TYPE_HTML5 = 4
    TYPES = ((TYPE_PDF, "PDF"), (TYPE_YOUTUBE, "YOUTUBE"),
             (TYPE_HTML5VIDEO, "HTML5VIDEO"), (TYPE_HTML5, "HTML5"))
    # old: title text
    title = CharField(max_length=255, default="untitled")
    submittedby = ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL)
    numpages = IntegerField(default=0)
    # old: ncols integer
    w = IntegerField(default=0)
    # old: nrows integer
    h = IntegerField(default=0)
    rotation = IntegerField(default=0)                               # new
    version = IntegerField(default=0)  # incremented when adding src
    type = IntegerField(choices=TYPES, default=TYPE_PDF)
    # x-coordinate of lower-left corner of trimbox
    x0 = IntegerField(default=0)
    # y-coordinate of lower-left corner of trimbox
    y0 = IntegerField(default=0)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.title)
    # FIXME Note: To preserve compatibility w/ previous production DB, I also added a default=1 at the SQL level for the 'type' field , so that we don't create null records if using the old framework


class YoutubeInfo(models.Model):
    source = OneToOneField(Source, on_delete=models.CASCADE)
    key = CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.key)


class HTML5Info(models.Model):
    source = OneToOneField(Source, on_delete=models.CASCADE)
    url = CharField(max_length=2048, blank=True, null=True)

    def __unicode__(self):
        return "%s %s: %s" % (self.__class__.__name__, self.id,  self.url)


class OnDemandInfo(models.Model):
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    source = OneToOneField(Source, on_delete=models.CASCADE)
    url = CharField(max_length=2048, blank=True, null=True)

# TODO: port history feature, so we can restore a file is an admin erases it by mistake.


# old: ownership
class Ownership(models.Model):
    source = ForeignKey(Source, on_delete=models.CASCADE)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    folder = ForeignKey(Folder, null=True, on_delete=models.SET_NULL)
    # old: published timestamp without time zone DEFAULT now()
    published = DateTimeField(default=datetime.now, db_index=True)
    deleted = BooleanField(default=False)
    assignment = BooleanField(default=False)
    due = DateTimeField(default=datetime.now, null=True)

    def __unicode__(self):
        return "%s %s: source %s in ensemble %s" % (self.__class__.__name__, self.id,  self.source_id, self.ensemble_id)


# old: nb2_location
class Location(models.Model):
    source = ForeignKey(Source, on_delete=models.CASCADE)
    version = IntegerField(default=1)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)
    section = ForeignKey(Section, null=True, on_delete=models.SET_NULL)
    x = IntegerField()
    y = IntegerField()
    w = IntegerField()
    h = IntegerField()
    page = IntegerField()
    duration = IntegerField(null=True)
    is_title = BooleanField(default=False)
    pause = BooleanField(default=False)

    def __unicode__(self):
        return "%s %s: on source %s - page %s " % (self.__class__.__name__, self.id,  self.source_id, self.page)


class HTML5Location(models.Model):
    location = OneToOneField(Location, on_delete=models.CASCADE)
    path1 = CharField(max_length=2048, blank=True, null=True)
    path2 = CharField(max_length=2048, blank=True, null=True)
    offset1 = IntegerField()
    offset2 = IntegerField()


# old: nb2_comment
class Comment(models.Model):
    TYPES = ((1, "Private"), (2, "Staff"), (3, "Class"), (4, "Tag Private"))
    location = ForeignKey(Location, on_delete=models.CASCADE)
    parent = ForeignKey('self', null=True, on_delete=models.SET_NULL)
    author = ForeignKey(User, on_delete=models.CASCADE)
    # old: ctime timestamp
    ctime = DateTimeField(default=datetime.now, db_index=True)
    body = TextField(blank=True, null=True)
    type = IntegerField(choices=TYPES)
    # old: signed integer DEFAULT 0,
    signed = BooleanField(default=True)
    # old: vis_status integer DEFAULT 0
    deleted = BooleanField(default=False)
    moderated = BooleanField(default=False)

    def __unicode__(self):
        return "%s %s: %s " % (self.__class__.__name__, self.id,  self.body[:50])

    @property
    def created(self):
        if (timezone.is_naive(self.ctime)):
            return str(calendar.timegm(pytz.utc.localize(self.ctime).timetuple()))
        else:
            return str(calendar.timegm(self.ctime.astimezone(pytz.utc).timetuple()))

# Represents Users tagged in a comment


class Tag(models.Model):
    TYPES = ((1, "Individual"),)
    type = IntegerField(choices=TYPES)
    individual = ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
    last_reminder = DateTimeField(null=True)

# Those aren't used anymore (threadmarks are used instead)


class Mark(models.Model):                                                       # old: nb2_mark
    TYPES = ((1, "answerplease"), (3, "approve"),
             (5, "reject"), (7, "favorite"), (9, "hide"))
    # old: id_type integer NOT NULL
    type = IntegerField(choices=TYPES)
    # old: ctime timestamp
    ctime = DateTimeField(default=datetime.now)
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
    user = ForeignKey(User, on_delete=models.CASCADE)


class ThreadMark(models.Model):
    TYPES = ((1, "question"), (2, "star"), (3, "summarize"))
    type = IntegerField(choices=TYPES)
    active = BooleanField(default=True)
    ctime = DateTimeField(default=datetime.now, db_index=True)
    location = ForeignKey(Location, on_delete=models.CASCADE)
    # this is optional
    comment = ForeignKey(Comment, null=True, on_delete=models.SET_NULL)
    user = ForeignKey(User, on_delete=models.CASCADE)

    def resolved(self):
        return self.replyrating_set.filter(status__gt=ReplyRating.TYPE_UNRESOLVED).exists()


class ReplyRating(models.Model):
    # Rep invarient: TYPE_UNRESOLVED < TYPE_RESOLVED < TYPE_THANKS
    TYPE_UNRESOLVED = 1
    TYPE_RESOLVED = 2
    TYPE_THANKS = 3
    TYPES = ((TYPE_UNRESOLVED, "unresolved"),
             (TYPE_RESOLVED, "resolved"), (TYPE_THANKS, "thanks"))
    threadmark = ForeignKey(ThreadMark, on_delete=models.CASCADE)
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now, db_index=True)
    status = IntegerField(choices=TYPES)


class ThreadMarkHistory(models.Model):
    TYPES = ((1, "question"), (2, "star"), (3, "summarize"))
    type = IntegerField(choices=TYPES)
    active = BooleanField(default=True)
    ctime = DateTimeField(default=datetime.now)
    location = ForeignKey(Location, on_delete=models.CASCADE)
    user = ForeignKey(User, on_delete=models.CASCADE)
    # this is optional
    comment = ForeignKey(Comment, null=True, on_delete=models.SET_NULL)


# old: nb2_processqueue
class Processqueue(models.Model):
    source = ForeignKey(Source, null=True, on_delete=models.CASCADE)
    # old: submitted timestamp without time zone DEFAULT now(),
    submitted = DateTimeField(default=datetime.now)
    # old: started timestamp without time zone,
    started = DateTimeField(null=True)
    # old: completed timestamp without time zone
    completed = DateTimeField(null=True)


# TODO: Continue migratedbscript from here.
class Session(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now)
    lastactivity = DateTimeField(default=datetime.now, null=True)
    ip = CharField(max_length=63, blank=True, null=True)
    clienttime = DateTimeField(blank=True, null=True)


class CommentSeen(models.Model):
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
    session = ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    # duplicate (cf session) but inlined for performance
    user = ForeignKey(User, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now)


class PageSeen(models.Model):
    source = ForeignKey(Source, on_delete=models.CASCADE)
    page = IntegerField()
    session = ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    # duplicate (cf session) but inlined for performance
    user = ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ctime = DateTimeField(default=datetime.now)


class AnalyticsVisit(models.Model):
    source = ForeignKey(Source, on_delete=models.CASCADE)
    user = ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ctime = DateTimeField(default=datetime.now)


class AnalyticsClick(models.Model):
    source = ForeignKey(Source, on_delete=models.CASCADE)
    user = ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ctime = DateTimeField(default=datetime.now)
    control = CharField(max_length=30)
    value = CharField(max_length=30)


class Landing(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now)
    ip = CharField(max_length=63, blank=True, null=True)
    client = CharField(max_length=1023, blank=True, null=True)
    referer = CharField(max_length=1023, blank=True, null=True)
    path = CharField(max_length=1023, blank=True, null=True)


class Idle(models.Model):
    session = ForeignKey(Session, on_delete=models.CASCADE)
    t1 = DateTimeField()
    t2 = DateTimeField()

# NB-wide settings (i.e. not ensemble-based).


class DefaultSetting(models.Model):
    name = CharField(max_length=1023)
    description = TextField(blank=True, null=True)
    value = IntegerField()


class SettingLabel(models.Model):
    setting = ForeignKey(DefaultSetting, on_delete=models.CASCADE)
    value = IntegerField()
    label = TextField()


class UserSetting(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    setting = ForeignKey(DefaultSetting, on_delete=models.CASCADE)
    value = IntegerField()
    ctime = DateTimeField(default=datetime.now)


class SourceVersion(models.Model):
    title = CharField(max_length=255, default="untitled")
    submittedby = ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL)
    numpages = IntegerField(default=0)
    w = IntegerField(default=0)
    h = IntegerField(default=0)
    rotation = IntegerField(default=0)
    version = IntegerField(default=0)
    published = DateTimeField()


class FileDownload(models.Model):
    ctime = DateTimeField(default=datetime.now)
    user = ForeignKey(User, on_delete=models.CASCADE)
    source = ForeignKey(Source, on_delete=models.CASCADE)
    annotated = BooleanField(default=False)


class Notification(models.Model):
    type = CharField(max_length=127)
    atime = DateTimeField(null=True, default=datetime.now)


class GuestHistory(models.Model):
    """
    Records the period during which a user was a guest. t_end gets populated if the user ever converts their guest account into a regular account by registering (not using SSO).
    """
    user = ForeignKey(User, on_delete=models.CASCADE)
    t_start = DateTimeField(null=True, default=datetime.now)
    t_end = DateTimeField(null=True)


class GuestLoginHistory(models.Model):
    """
    Records the transition between a login as guest account and login as a exising  account. This data supplements the one in GuestHistory. i.e. for the cases where we have a transition from a guest to a existing user. Note that SSO (i.e. Google ID) users are always considered "existing" even if they weren't in the DB before (since their guest account id doesn't get recycled), so they appear here.
    """
    guest = ForeignKey(User, related_name="u1", on_delete=models.CASCADE)
    user = ForeignKey(User, related_name="u2", on_delete=models.CASCADE)
    ctime = DateTimeField(null=True, default=datetime.now)


class AssignmentGrade(models.Model):
    user = ForeignKey(User, related_name="u_grade", on_delete=models.CASCADE)
    grader = ForeignKey(User, related_name="g_grade", on_delete=models.PROTECT)
    ctime = DateTimeField(default=datetime.now)
    grade = IntegerField()
    source = ForeignKey(Source, on_delete=models.CASCADE)


class AssignmentGradeHistory(models.Model):
    user = ForeignKey(User, related_name="u_grade_h", on_delete=models.CASCADE)
    grader = ForeignKey(User, related_name="g_grade_h",
                        on_delete=models.PROTECT)
    ctime = DateTimeField(default=datetime.now)
    grade = IntegerField()
    source = ForeignKey(Source, on_delete=models.CASCADE)


class LabelCategory(models.Model):
    TYPE_USER = 1
    TYPE_ADMIN = 2
    TYPE_SUPERADMIN = 3
    TYPES = ((TYPE_USER, "USER"), (TYPE_ADMIN, "ADMIN"),
             (TYPE_SUPERADMIN, "SUPERADMIN"))
    TYPE_COMMENT = 1
    TYPE_THREAD = 2
    TYPES_SCOPE = ((TYPE_COMMENT, "COMMENT"), (TYPE_THREAD, "THREAD"),)
    visibility = IntegerField(choices=TYPES, default=TYPE_ADMIN)
    scope = IntegerField(choices=TYPES_SCOPE, default=TYPE_COMMENT)
    pointscale = IntegerField()
    name = CharField(max_length=1024)
    ensemble = ForeignKey(Ensemble, on_delete=models.CASCADE)


class LabelCategoryCaption(models.Model):
    category = ForeignKey(LabelCategory,  on_delete=models.CASCADE)
    grade = IntegerField()
    caption = CharField(max_length=127)


class CommentLabel(models.Model):
    """Used for finer grain grading or categorizing comments or threads"""
    grader = ForeignKey(User, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now)
    grade = IntegerField()
    # so we can grade different dimensions of a post.
    category = ForeignKey(LabelCategory, on_delete=models.CASCADE)
    comment = ForeignKey(Comment, on_delete=models.CASCADE)


class CommentLabelHistory(models.Model):
    grader = ForeignKey(User, on_delete=models.CASCADE)
    ctime = DateTimeField(default=datetime.now)
    grade = IntegerField()
    # so we can grade different dimensions of a post.
    category = ForeignKey(LabelCategory, on_delete=models.CASCADE)
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
