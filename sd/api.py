# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""This module provides the HaaS service's public API.

TODO: Spec out and document what sanitization is required.
"""
import importlib
import json
import logging

from haas import model
from haas.config import cfg
from haas.http import APIError, rest_call


class NotFoundError(APIError):
    """An exception indicating that a given resource does not exist."""
    status_code = 404 # Not Found


class DuplicateError(APIError):
    """An exception indicating that a given resource already exists."""
    status_code = 409 # Conflict


class BadArgumentError(APIError):
    """An exception indicating an invalid request on the part of the user."""


                            # Service Code #
                            ################

@rest_call('PUT', '/service/<service>')
def service_create(service, service_type, api, endpoint):
    """Create user with given password.

    If the user already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Service, service)
    api = _must_find(db, model.API, api)
    service = model.Service(service, service_type, api, endpoint)
    db.add(service)
    db.commit()


@rest_call('DELETE', '/service/<service>')
def service_delete(service):
    """Delete service.

    If the service does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    service = _must_find(db, model.Service, service)
    db.delete(service)
    db.commit()


                            # API Code #
                            ############

@rest_call('PUT', '/api/<api>')
def api_create(api):
    """Create api.

    If the api already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Group, api)
    api = model.API(api)
    db.add(api)
    db.commit()


@rest_call('DELETE', '/api/<api>')
def api_delete(api):
    """Delete api.

    If the api does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    api = _must_find(db, model.API, api)
    db.delete(api)
    db.commit()


    # Helper functions #
    ####################

def _assert_absent(session, cls, name):
    """Raises a DuplicateError if the given object is already in the database.

    This is useful for most of the *_create functions.

    Arguments:

    session - a sqlaclhemy session to use.
    cls - the class of the object to query.
    name - the name of the object in question.
    """
    obj = session.query(cls).filter_by(label=name).first()
    if obj:
        raise DuplicateError("%s %s already exists." % (cls.__name__, name))


def _must_find(session, cls, name):
    """Raises a NotFoundError if the given object doesn't exist in the datbase.
    Otherwise returns the object

    This is useful for most of the *_delete functions.

    Arguments:

    session - a sqlaclhemy session to use.
    cls - the class of the object to query.
    name - the name of the object in question.
    """
    obj = session.query(cls).filter_by(label=name).first()
    if not obj:
        raise NotFoundError("%s %s does not exist." % (cls.__name__, name))
    return obj

def _namespaced_query(session, obj_outer, cls_inner, name_inner):
    """Helper function to search for subobjects of an object."""
    return session.query(cls_inner) \
        .filter_by(owner = obj_outer) \
        .filter_by(label = name_inner).first()

def _assert_absent_n(session, obj_outer, cls_inner, name_inner):
    """Raises DuplicateError if a "namespaced" object, such as a node's nic, exists.

    Otherwise returns succesfully.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = _namespaced_query(session, obj_outer, cls_inner, name_inner)
    if obj_inner is not None:
        raise DuplicateError("%s %s on %s %s already exists" %
                             (cls_inner.__name__, name_inner,
                              obj_outer.__class__.__name__, obj_outer.label))

def _must_find_n(session, obj_outer, cls_inner, name_inner):
    """Searches the database for a "namespaced" object, such as a nic on a node.

    Raises NotFoundError if there is none.  Otherwise returns the object.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = _namespaced_query(session, obj_outer, cls_inner, name_inner)
    if obj_inner is None:
        raise NotFoundError("%s %s on %s %s does not exist." %
                            (cls_inner.__name__, name_inner,
                             obj_outer.__class__.__name__, obj_outer.label))
    return obj_inner
