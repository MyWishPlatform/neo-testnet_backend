from flask import session


def get_github_user():
    '''
    get current login github user
    '''
    return session.get("github_user")


def set_github_user(user):
    '''
    set current login github user
    '''
    session["github_user"] = user


def get_github_token():
    '''
    get current login github user token,for query github api
    '''
    return session.get("github_token")


def set_github_token(token):
    '''
    set current login github user
    '''
    session["github_token"] = token
