#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Migration script for Search-enabled Models.'''
from __future__ import absolute_import

import logging

from elasticsearch import helpers
from modularodm.query.querydialect import DefaultQueryDialect as Q

from website import settings
from framework.auth import User
from website.models import Node
from website.app import init_app
import website.search.search as search
from scripts import utils as script_utils
from website.search.elastic_search import es


logger = logging.getLogger(__name__)

def migrate_nodes(index):
    logger.info("Migrating nodes to index: {}".format(index))
    n_iter = 0
    nodes = Node.find(Q('is_public', 'eq', True) & Q('is_deleted', 'eq', False))
    for node in nodes:
        search.update_node(node, index=index)
        n_iter += 1

    logger.info('Nodes migrated: {}'.format(n_iter))


def migrate_users(index):
    logger.info("Migrating users to index: {}".format(index))
    n_migr = 0
    n_iter = 0
    for user in User.find():
        if user.is_active:
            search.update_user(user, index=index)
            n_migr += 1
        n_iter += 1

    logger.info('Users iterated: {0}\nUsers migrated: {1}'.format(n_iter, n_migr))


def migrate(delete, index=settings.ELASTIC_INDEX, app=None):
    app = app or init_app("website.settings", set_backends=True, routes=True)

    script_utils.add_file_logger(logger, __file__)
    ctx = app.test_request_context()
    ctx.push()
    new_index = set_up_index(index)

    migrate_nodes(new_index)
    migrate_users(new_index)

    set_up_alias(index, new_index)

    if delete:
        delete_old(new_index)

    ctx.pop()


def set_up_index(idx):
    alias = es.indices.get_aliases(index=idx)

    if not alias or not alias.keys() or idx in alias.keys():
        # Deal with empty indices or the first migration
        index = '{}_v1'.format(idx)
        search.create_index(index=index)
        logger.info("Reindexing {0} to {1}_v1".format(idx, idx))
        helpers.reindex(es, idx, index)
        logger.info("Deleting {} index".format(idx))
        es.indices.delete(index=idx)
        es.indices.put_alias(idx, index)
    else:
        # Increment version
        version = int(alias.keys()[0].split('_v')[1]) + 1
        logger.info("Incrementing index version to {}".format(version))
        index = '{0}_v{1}'.format(idx, version)
        search.create_index(index=index)
        logger.info("{} index created".format(index))
    return index


def set_up_alias(old_index, index):
    alias = es.indices.get_aliases(index=old_index)
    if alias:
        logger.info("Removing old aliases to {}".format(old_index))
        es.indices.delete_alias(index=old_index, name='_all', ignore=404)
    logger.info("Creating new alias from {0} to {1}".format(old_index, index))
    es.indices.put_alias(old_index, index)


def delete_old(index):
    old_version = int(index.split('_v')[1]) - 1
    if old_version < 1:
        logger.info("No index before {} to delete".format(index))
        pass
    else:
        old_index = index.split('_v')[0] + '_v' + str(old_version)
        logger.info("Deleting {}".format(old_index))
        es.indices.delete(index=old_index, ignore=404)


if __name__ == '__main__':
    migrate(False)
