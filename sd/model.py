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
"""core database objects for the HaaS"""

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from subprocess import call, check_call
import subprocess
from haas.config import cfg
from haas.dev_support import no_dry_run
import importlib
import uuid
import xml.etree.ElementTree
import logging

Base=declarative_base()
Session = sessionmaker()

# A joining table for services to apis, which have a many to many relationship:
service_api = Table('service_api', Base.metadata,
                    Column('service_id', Integer, ForeignKey('user.id')),
                    Column('api_id', Integer, ForeignKey('api.id')))


def init_db(create=False, uri=None):
    """Start up the DB connection.

    If `create` is True, this will generate the schema for the database.

    `uri` is the uri to use for the databse. If it is None, the uri from the
    config file will be used.
    """

    if uri == None:
        uri = cfg.get('database', 'uri')

    # We have to import this prior to doing create_all, so that any tables
    # defined by the driver will make it into the schema.
    driver_name = cfg.get('general', 'driver')
    driver = importlib.import_module('haas.drivers.' + driver_name)

    engine = create_engine(uri)
    if create:
        Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    driver.init_db(create=create)


class Model(Base):
    """All of our database models are descendants of this class.

    Its main purpose is to reduce boilerplate by doing things such as
    auto-generating table names.

    It also declares two columns which are common to every model:

        * id, which is an arbitrary integer primary key.
        * label, which is a symbolic name for the object.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False)
    label = Column(String, nullable=False)

    def __repr__(self):
        return '%s<%r>' % (self.__class__.__name__, self.label)

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()

class Service(Model):
    """a service in the directory"""
    service_type = Column(String, nullable=False)
    api =  relationship("API", secondary=service_api, backref="api")
    endpoint = Column(String, nullable=False)

    def __init__(self, label, service_type, api, endpoint)
        self.label = label
        self.service_type = service_type
        self.api = api
        self.endpoint = endpoint

class API(Model):
    """an api a service can use
       inherits id and label from Model"""
    def __init__(self, label)
        self.label = label
