import logging
import re
import sys

import requests
import vdf

ENDPOINT = 'https://help.steampowered.com/en/wizard/AjaxDoPackageRemove'
POST_APPID_KEY = 'appid'
POST_PACKAGEID_KEY = 'packageid'
POST_SESSIONID_KEY = 'sessionid'
COOKIES_SESSIONID_KEY = 'sessionid'
COOKIES_STEAM_LOGIN_KEY = 'steamLogin'
COOKIES_STEAM_LOGIN_SECURE_KEY = 'steamLoginSecure'
HEADER_CONTENT_TYPE_KEY = 'content-type'
HEADER_CONTENT_TYPE_JSON_PREFIX = 'application/json;'
LIB_HIDDEN_TAG = 'hidden'
LIB_HIDDEN_TRUE = '1'
PACKAGE_BLACKLIST = {'0'}  # package id 0 is reserved for Steam and it contains hundreds of app ids
LOG_FILE = 'dustman.log'


def dump():
    if len(sys.argv) < 6:
        print("Usage: python3 Dustman.py <steam_lib_category_file> <steam_lib_licenses_file> <sessionid> <steam_login> <steam_login_secure>")
        raise ValueError("Incomplete command-line arguments")

    category_file = sys.argv[1]
    licenses_file = sys.argv[2]
    sessionid = sys.argv[3]
    steam_login = sys.argv[4]
    steam_login_secure = sys.argv[5]

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    logging.info('==============================================')
    logging.info("Starting...")

    hidden_apps, visible_apps = get_hidden_and_visible_apps(category_file)
    packages_to_apps, apps_to_packages = build_app_package_dicts(licenses_file)

    with requests.Session() as session:
        session.cookies.update({
            COOKIES_SESSIONID_KEY: sessionid,
            COOKIES_STEAM_LOGIN_KEY: steam_login,
            COOKIES_STEAM_LOGIN_SECURE_KEY: steam_login_secure
        })

        for app in hidden_apps:
            if app in apps_to_packages:
                remove_app(app, apps_to_packages[app], sessionid, session, packages_to_apps, visible_apps)


# returns two sets: hidden apps, and visible apps
def get_hidden_and_visible_apps(steam_lib_category_file):
    hidden_apps = set()
    visible_apps = set()

    with open(steam_lib_category_file) as f:
        configs = vdf.load(f)
        apps = configs['UserRoamingConfigStore']['Software']['Valve']['Steam']['apps']
        for app, config in apps.items():
            if config.get(LIB_HIDDEN_TAG) == LIB_HIDDEN_TRUE:
                hidden_apps.add(app)
            else:
                visible_apps.add(app)

    return hidden_apps, visible_apps


# returns two dicts: package => apps, and app => packages
def build_app_package_dicts(steam_lib_licenses_file):
    package_pattern = re.compile('^License packageID (\d+)')
    apps_pattern = re.compile('^ *- Apps +: ((\d+, )+)')
    apps_to_packages = dict()
    packages_to_apps = dict()

    with open(steam_lib_licenses_file) as f:
        while True:
            # 1st line contains package id
            line = f.readline()
            if len(line) == 0:  # EOF
                break
            matches = package_pattern.search(line)
            if matches is None:
                continue
            package = matches.group(1)
            if package in PACKAGE_BLACKLIST:
                continue

            # skip 2nd line (state)
            f.readline()

            # 3nd line contains app ids
            line = f.readline()
            matches = apps_pattern.search(line)
            if matches is None:  # no apps in this package
                continue
            apps = matches.group(1).split(', ')[:-1]

            # skip 4th line (depots)
            f.readline()

            # collect
            packages_to_apps[package] = apps
            for app in apps:
                if app not in apps_to_packages:
                    apps_to_packages[app] = []
                apps_to_packages[app].append(package)

    return packages_to_apps, apps_to_packages


# app: id of app to be removed
# packages: ids of packages that contain the given app
# sessionid: current session id
# session: a Requests.Session object
# packages_to_apps: a dictionary mapping ids of packages to ids of their apps
# visible_apps: set of all non-hidden apps
def remove_app(app, packages, sessionid, session, packages_to_apps, visible_apps):
    for package in packages:
        package_apps = packages_to_apps[package]
        if len(package_apps) > 1:
            if any(app in visible_apps for app in package_apps):
                # we cannot just check if app is not in hidden_apps because hidden_apps does not contain DLCs or Tools,
                # and doing that would skip removing any package that contains DLCs or Tools
                logging.info("Skipping removing app %s in package %s because this package contains other non-hidden apps", app, package)
                continue
            logging.info("Removing app %s in package %s, which contains more than one app", app, package)
        remove_package(app, package, sessionid, session)


def remove_package(app, package, sessionid, session):
    data = {
        POST_APPID_KEY: app,
        POST_PACKAGEID_KEY: package,
        POST_SESSIONID_KEY: sessionid
    }
    r = session.post(ENDPOINT, data=data)

    # the only success scenario is when we receive a JSON object with `'success': true`;
    # note that in some cases, the endpoint responds with `'success': 15` to denote failure
    # and `not 15` evaluates to `False`!
    if not r.ok or not r.headers[HEADER_CONTENT_TYPE_KEY].startswith(HEADER_CONTENT_TYPE_JSON_PREFIX) \
            or r.json()['success'] is not True:
        logging.error("Failed to remove app %s from package %s", app, package)


if __name__ == '__main__':
    dump()
