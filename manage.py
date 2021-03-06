#!/usr/bin/env python

import click
from sqlalchemy import func, distinct
from flask.cli import FlaskGroup
from app import app, db
from app.models.user import User
from app.models.organization import Organization
from app.models.logger import Logger
from app.models.logger_role import LoggerRole


def create_app(info):
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """
    This is a management script for the Flask application.
    """
    # Adds the Flask commands like `run` and Flask CLI plugin commands, like the `db` group.
    # cli() is the default group, but adding other subgroups is possible.


@cli.command()
def print_org_logger_role_counts():
    """
    Creates the schema, adds some data, and prints organization LoggerRole counts
    """
    with app.app_context():
        db.create_all()
        db.session.commit()

        # Add some Organizations
        org_names = ['Apple', 'Google', 'Microsoft', 'Yahoo!']
        for org_name in org_names:
            organization = Organization(name=org_name)
            db.session.add(organization)
        db.session.commit()

        # Add some Users
        user_mappings = [
            ('Steve Jobs', 'Apple'),
            ('Tim Cook', 'Apple'),
            ('Phil Schiller', 'Apple'),
            ('Sundar Pichai', 'Google'),
            ('Eric Schmidt', 'Google'),
            ('Satya Nadella', 'Microsoft'),
            ('Marissa Mayer', 'Yahoo!'),
        ]
        for user_mapping in user_mappings:

            # Find one of the Organizations we added earlier
            organization = Organization.query.filter_by(name=user_mapping[1]).first()
            if not organization:
                click.echo('Could not find Organization with name "{}"!'.format(user_mapping[1]))
                continue

            # Add the User, mapping them to the found Organization
            user = User(name=user_mapping[0], organization=organization)
            db.session.add(user)

        db.session.commit()

        # Add some LoggerRoles
        logger_role_names = [
            'Owner',
            'Developer',
            'Reporter',
        ]
        for logger_role_name in logger_role_names:
            logger_role = LoggerRole(name=logger_role_name)
            db.session.add(logger_role)
        db.session.commit()

        # Add some Logger mappings (User <-> LoggerRole)
        logger_role_mappings = [
            ('Steve Jobs', 'Owner'),
            ('Tim Cook', 'Developer'),
            ('Phil Schiller', 'Reporter'),  # 'Apple' Users have 3 distinct LoggerRoles
            ('Sundar Pichai', 'Owner'),
            ('Eric Schmidt', 'Developer'),  # 'Google' Users have 2 distinct LoggerRoles
            ('Satya Nadella', 'Owner')  # 'Microsoft' Users have 1 distinct role
            # Yahoo! Users have 0 distinct roles
        ]
        for logger_role_mapping in logger_role_mappings:

            # Find one of the Users we added earlier
            user = User.query.filter_by(name=logger_role_mapping[0]).first()
            if not user:
                click.echo('Could not find User with name "{}"!'.format(logger_role_mapping[0]))
                continue

            # Find one of the LoggerRoles we added earlier
            logger_role = LoggerRole.query.filter_by(name=logger_role_mapping[1]).first()
            if not logger_role:
                click.echo('Could not find LoggerRole with name "{}"!'.format(logger_role_mapping[1]))
                continue

            # Add the Logger, mapping it to the found User and LoggerRole
            logger = Logger(user=user, logger_role=logger_role)
            db.session.add(logger)

        db.session.commit()

        # What I would like to do is join these two queries so that I have a count of how many different "LoggerRole" exist in each organization. Essentially I want to end up with something like:
        # "org_1": {'logger_role_1': 2, 'logger_role_2': 5, 'logger_role_3: 7 }

        # Note that outerjoin() is used to ensure that even Organizations with *no* LoggerRoles are still listed as 0.
        # Sample output:
        # [(u'Apple', 3), (u'Google', 2), (u'Microsoft', 1), (u'Yahoo!', 0)]
        click.echo(
            db.session.query(Organization.name, func.count(distinct(LoggerRole.id))).outerjoin(User).outerjoin(Logger).outerjoin(LoggerRole).group_by(Organization.id).all()
        )

if __name__ == '__main__':
    cli()
