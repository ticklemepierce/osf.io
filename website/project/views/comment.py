# -*- coding: utf-8 -*-
import collections
import httplib as http

from flask import request
from modularodm import Q

from framework.exceptions import HTTPError
from framework.auth.decorators import must_be_logged_in
from framework.auth.utils import privacy_info_handle
from framework.forms.utils import sanitize

from website import settings
from website.filters import gravatar
from website.models import Guid, Comment, CommentPane
from website.project.decorators import must_be_contributor_or_public
from datetime import datetime
from website.project.model import has_anonymous_link
from website.project.views.node import _view_project

COMMENT_PANE_NAME = 'comment_pane_'

@must_be_contributor_or_public
def view_comments(**kwargs):
    """Collect file trees for all add-ons implementing HGrid views, then
    format data as appropriate.
    """
    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']

    serialized = _view_project(node, auth, primary=True)
    if kwargs.get('cid'):
        comment = kwargs_to_comment(kwargs)
        serialized_comment = serialize_comment(comment, auth)
        serialized.update({
            'comment': serialized_comment
        })
    return serialized

@must_be_contributor_or_public
def view_comment_thread(**kwargs):

    auth = kwargs['auth']
    node = kwargs['node'] or kwargs['project']
    comment = kwargs_to_comment(kwargs)
    serialized = _view_project(node, auth, primary=True)
    serialized_comment = serialize_comment(comment, auth)
    serialized.update({
        'comment': serialized_comment
    })
    return serialized

def get_comment_pane(node, page_name):
    """
    Get the current comment pane that the user is working on
    :param node: Project
    :param page_name: The page that contains the comment pane
    :return: The CommentPane object; By default, it returns the "overview" CommentPane
    """
    page_attr = COMMENT_PANE_NAME + str(page_name)
    comment_pane = getattr(node, page_attr, None)
    if not comment_pane:
        comment_pane = CommentPane.create(node=node)
        setattr(node, page_attr, comment_pane)
    if not getattr(node, COMMENT_PANE_NAME + 'total', None):
        setattr(node, COMMENT_PANE_NAME + 'total', CommentPane.create(node=node))
    node.update_total_comments()
    return comment_pane

def resolve_target(node, page_name, guid):

    if not guid:
        return get_comment_pane(node, page_name)
    target = Guid.load(guid)
    if target is None:
        raise HTTPError(http.BAD_REQUEST)
    return target.referent


def collect_discussion(target, users=None):

    users = users or collections.defaultdict(list)
    for comment in getattr(target, 'commented', []):
        if not comment.is_deleted:
            users[comment.user].append(comment)
        collect_discussion(comment, users=users)
    return users

# TODO get discussion from comment pane (in model)
@must_be_contributor_or_public
def comment_discussion(**kwargs):

    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    page_name = request.args.get('page')
    target = get_comment_pane(node, page_name)
    users = collect_discussion(target)
    anonymous = has_anonymous_link(node, auth)
    # Sort users by comment frequency
    # TODO: Allow sorting by recency, combination of frequency and recency
    sorted_users = sorted(
        users.keys(),
        key=lambda item: len(users[item]),
        reverse=True,
    )

    return {
        'discussion': [
            {
                'id': privacy_info_handle(user._id, anonymous),
                'url': privacy_info_handle(user.url, anonymous),
                'fullname': privacy_info_handle(user.fullname, anonymous, name=True),
                'isContributor': node.is_contributor(user),
                'gravatarUrl': privacy_info_handle(
                    gravatar(
                        user, use_ssl=True, size=settings.GRAVATAR_SIZE_DISCUSSION,
                    ),
                    anonymous
                ),

            }
            for user in sorted_users
        ]
    }


def serialize_comment(comment, auth, anonymous=False):
    return {
        'id': comment._id,
        'author': {
            'id': privacy_info_handle(comment.user._id, anonymous),
            'url': privacy_info_handle(comment.user.url, anonymous),
            'name': privacy_info_handle(
                comment.user.fullname, anonymous, name=True
            ),
            'gravatarUrl': privacy_info_handle(
                gravatar(
                    comment.user, use_ssl=True,
                    size=settings.GRAVATAR_SIZE_DISCUSSION
                ),
                anonymous
            ),
        },
        'dateCreated': comment.date_created.isoformat(),
        'dateModified': comment.date_modified.isoformat(),
        'content': comment.content,
        'hasChildren': bool(getattr(comment, 'commented', [])),
        'canEdit': comment.user == auth.user,
        'modified': comment.modified,
        'isDeleted': comment.is_deleted,
        'isAbuse': auth.user and auth.user._id in comment.reports,
    }


def serialize_comments(record, auth, anonymous=False):

    return [
        serialize_comment(comment, auth, anonymous)
        for comment in getattr(record, 'commented', []) or []
    ]


def kwargs_to_comment(kwargs, owner=False):

    comment = Comment.load(kwargs.get('cid'))
    if comment is None:
        raise HTTPError(http.BAD_REQUEST)

    if owner:
        auth = kwargs['auth']
        if auth.user != comment.user:
            raise HTTPError(http.FORBIDDEN)

    return comment


@must_be_logged_in
@must_be_contributor_or_public
def add_comment(**kwargs):

    auth = kwargs['auth']
    node = kwargs['node'] or kwargs['project']
    page = request.json.get('page')

    if not node.comment_level:
        raise HTTPError(http.BAD_REQUEST)

    if not node.can_comment(auth):
        raise HTTPError(http.FORBIDDEN)

    guid = request.json.get('target')
    target = resolve_target(node, page, guid)

    content = request.json.get('content').strip()
    content = sanitize(content)
    if not content:
        raise HTTPError(http.BAD_REQUEST)
    if len(content) > settings.COMMENT_MAXLENGTH:
        raise HTTPError(http.BAD_REQUEST)

    comment = Comment.create(
        auth=auth,
        node=node,
        target=target,
        user=auth.user,
        content=content,
    )
    comment.save()
    node.update_total_comments()

    return {
        'comment': serialize_comment(comment, auth)
    }, http.CREATED


@must_be_contributor_or_public
def list_comments(auth, page=None, **kwargs):
    node = kwargs['node'] or kwargs['project']
    if not page:
        page = request.args.get('page')
    anonymous = has_anonymous_link(node, auth)
    guid = request.args.get('target')
    target = resolve_target(node, page, guid)
    serialized_comments = serialize_comments(target, auth, anonymous)
    n_unread = 0

    if node.is_contributor(auth.user):
        if auth.user.comments_viewed_timestamp is None:
            auth.user.comments_viewed_timestamp = {}
            auth.user.save()
        n_unread = n_unread_comments(target, auth.user)
    return {
        'comments': serialized_comments,
        'nUnread': n_unread
    }


def n_unread_comments(node, user):
    """Return the number of unread comments on a node for a user."""
    default_timestamp = datetime(1970, 1, 1, 12, 0, 0)
    view_timestamp = user.comments_viewed_timestamp.get(node._id, default_timestamp)
    return Comment.find(Q('node', 'eq', node) &
                        Q('user', 'ne', user) &
                        Q('date_created', 'gt', view_timestamp) &
                        Q('date_modified', 'gt', view_timestamp)).count()

@must_be_logged_in
@must_be_contributor_or_public
def edit_comment(**kwargs):

    auth = kwargs['auth']

    comment = kwargs_to_comment(kwargs, owner=True)

    content = request.json.get('content').strip()
    content = sanitize(content)
    if not content:
        raise HTTPError(http.BAD_REQUEST)
    if len(content) > settings.COMMENT_MAXLENGTH:
        raise HTTPError(http.BAD_REQUEST)

    comment.edit(
        content=content,
        auth=auth,
        save=True
    )

    return serialize_comment(comment, auth)


@must_be_logged_in
@must_be_contributor_or_public
def delete_comment(**kwargs):

    auth = kwargs['auth']
    comment = kwargs_to_comment(kwargs, owner=True)
    comment.delete(auth=auth, save=True)

    return {}


@must_be_logged_in
@must_be_contributor_or_public
def undelete_comment(**kwargs):

    auth = kwargs['auth']
    comment = kwargs_to_comment(kwargs, owner=True)
    comment.undelete(auth=auth, save=True)

    return {}


@must_be_logged_in
@must_be_contributor_or_public
def update_comments_timestamp(auth, **kwargs):
    node = kwargs['node'] or kwargs['project']
    if node.is_contributor(auth.user):
        auth.user.comments_viewed_timestamp[node._id] = datetime.utcnow()
        auth.user.save()
        page = request.json.get('page')
        list_comments(page=page, **kwargs)
        return {node._id: auth.user.comments_viewed_timestamp[node._id].isoformat()}
    else:
        return {}


@must_be_logged_in
@must_be_contributor_or_public
def report_abuse(**kwargs):

    auth = kwargs['auth']
    user = auth.user

    comment = kwargs_to_comment(kwargs)

    category = request.json.get('category')
    text = request.json.get('text', '')
    if not category:
        raise HTTPError(http.BAD_REQUEST)

    try:
        comment.report_abuse(user, save=True, category=category, text=text)
    except ValueError:
        raise HTTPError(http.BAD_REQUEST)

    return {}


@must_be_logged_in
@must_be_contributor_or_public
def unreport_abuse(**kwargs):

    auth = kwargs['auth']
    user = auth.user

    comment = kwargs_to_comment(kwargs)

    try:
        comment.unreport_abuse(user, save=True)
    except ValueError:
        raise HTTPError(http.BAD_REQUEST)

    return {}