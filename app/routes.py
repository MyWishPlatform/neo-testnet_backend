from app import app, db_restrictions, responses, mywish_session
from settings_local import FAUCET_CLI, CAPTCHA_SECRET
from flask import request, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from flask_jsonrpc.proxy import ServiceProxy
from flask_jsonrpc import exceptions
from app.models import TokenType
import requests
import traceback

try:
    from urllib.parse import urlencode, parse_qs
except ImportError:
    from urllib import urlencode

dblimits = db_restrictions.DatabaseRestrictions()
limiter = Limiter(app, key_func=get_ipaddr)
cli = ServiceProxy(FAUCET_CLI)

asset_neo = "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b"
asset_gas = "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7"
asset_amount = app.config['DROP_AMOUNT']
limit_on = app.config['RATELIMIT_ENABLED']
github_client_id = app.config['GITHUB_CLIENT_ID']
github_client_secret = app.config['GITHUB_CLIENT_SECRET']


@app.route('/api/request', methods=['POST'])
# restrict number of requests by IP - 1 request for IP per day
# @limiter.limit("1 per day")
def request_main():
    user = mywish_session.get_github_user()
    if user is None:
        return responses.login_fail(url_for("login"))
    account = user.get('login')
    # fetch captcha key and validate
    response = request.get_json()
    captcha_check = captcha_verify(response['g-recaptcha-response'])
    # captcha_check={"success":1}

    if not captcha_check["success"]:
        return responses.captcha_fail(captcha_check)
    else:
        neo_address = response['address']
        neo_asset = response['asset']
        ip = request.headers.getlist(
            "X-Forwarded-For")[0] if request.headers.getlist(
                "X-Forwarded-For") else request.remote_addr

        if limit_on:
            neo_query = find_address(neo_address, neo_asset)
            if neo_query and not dblimits.is_enough_time(
                    neo_query.last_request_date):
                return responses.db_limit()

            ip_query = dblimits.find_ip_address(ip)
            if ip_query and neo_query and not dblimits.is_enough_time(
                    ip_query.last_request_date):
                return responses.ip_limit()

        ret = {}
        if neo_asset == "NEO":
            ret = cli.sendtoaddress(asset_neo, neo_address, asset_amount)
        elif neo_asset == "GAS":
            ret = cli.sendtoaddress(asset_gas, neo_address, asset_amount)
        if 'error' in ret and ret['error'] and ret['error']['code'] != 0:
            return responses.balance_fail(ret['error']['message'])

        tokentype = TokenType.NEO if neo_asset == "NEO" else TokenType.GAS
        if limit_on:
            db_save_address(neo_query, neo_address, neo_asset)
            db_save_ip(ip_query, ip)

        db_save_request_log(neo_address, account, asset_amount,
                            tokentype.value, ip)
        return responses.send_success(neo_address)


@app.route("/api/login")
def login():
    '''
    redirect to github login page
    '''
    return authorize()


@app.route('/api/github/callback')
def authorized():
    '''
    github callback address, with "code" query string
    '''
    code = request.args.get("code")
    token = get_token_by_code(code)
    mywish_session.set_github_token(
        "%s %s" % (token["token_type"], token["access_token"]))

    user = get_github_user()
    if user is not None:
        mywish_session.set_github_user(user)
    next_url = request.args.get('next') or "/"
    return redirect(next_url)


@app.route("/api/login-user")
def login_user():
    user = mywish_session.get_github_user()
    if user is None:
        return responses.login_fail(url_for("login"))
    return responses.success(user)


def authorize(scope=None, redirect_uri=None, state=None):
    """
    Redirect to GitHub and request access to a user's data.

    :param scope: List of `Scopes`_ for which to request access, formatted
                  as a string or comma delimited list of scopes as a
                  string. Defaults to ``None``, resulting in granting
                 read-only access to public information (includes public
                  user profile info, public repository info, and gists).
                  For more information on this, see the examples in
                  presented in the GitHub API `Scopes`_ documentation, or
                  see the examples provided below.
    :type scope: str
    :param redirect_uri: `Redirect URL`_ to which to redirect the user
                         after authentication. Defaults to ``None``,
                         resulting in using the default redirect URL for
                         the OAuth application as defined in GitHub.  This
                         URL can differ from the callback URL defined in
                         your GitHub application, however it must be a
                         subdirectory of the specified callback URL,
                         otherwise raises a :class:`GitHubError`.  For more
                             information on this, see the examples in presented
                         in the GitHub API `Redirect URL`_ documentation,
                             or see the example provided below.
    :type redirect_uri: str
    :param state: An unguessable random string. It is used to protect
                  against cross-site request forgery attacks.
    :type state: str

    For example, if we wanted to use this method to get read/write access
    to user profile information, in addition to read-write access to code,
    commit status, etc., we would need to use the `Scopes`_ ``user`` and
    ``repo`` when calling this method.

    .. code-block:: python

        github.authorize(scope="user,repo")

    Additionally, if we wanted to specify a different redirect URL
    following authorization.

    .. code-block:: python
        # Our application's callback URL is "http://example.com/callback"
        redirect_uri="http://example.com/callback/my/path"
        github.authorize(scope="user,repo", redirect_uri=redirect_uri)
    .. _Scopes: https://developer.github.com/v3/oauth/#scopes
    .. _Redirect URL: https://developer.github.com/v3/oauth/#redirect-urls

    """
    params = {'client_id': github_client_id}
    if scope:
        params['scope'] = scope
    if redirect_uri:
        params['redirect_uri'] = redirect_uri
    if state:
        params['state'] = state

    url = 'https://github.com/login/oauth/authorize?' + urlencode(params)
    return redirect(url)


def get_token_by_code(code):
    '''
    get github access token by callback code.
    \n
    reference: https://developer.github.com/apps/building-oauth-apps/authorizing-oauth-apps/
    \n
    Returns:
        `Dict` ,contains key:access_token,token_type,scope
    '''
    headers = {"Accept": "application/json"}
    params = {
        'code': code,
        'client_id': github_client_id,
        'client_secret': github_client_secret
    }
    response = requests.post("https://github.com/login/oauth/access_token",
                             json=params,
                             headers=headers,
                             verify=False)
    result = response.json()
    if "error" in result:
        raise Exception(result["error"] + "," + result["error_description"])
    return result


def get_github_user():
    '''
    get current login github user info
    '''
    token_headers = {"Authorization": mywish_session.get_github_token()}
    userResponse = requests.get("https://api.github.com/user",
                                headers=token_headers)
    return userResponse.json()


"""
# custom error through api for ip limiter
@app.errorhandler(429)
def limit_handler(error):
    return responses.ip_limit()
"""


# captcha response should be send from here
def captcha_verify(response):
    payload = {"secret": CAPTCHA_SECRET, "response": response}
    captcha_call = requests.post(
        'https://www.google.com/recaptcha/api/siteverify', payload)
    return captcha_call.json()


def relay_tx(address, asset):
    try:
        if asset == "NEO":
            cli.sendtoaddress(asset_neo, address, asset_amount)
        elif asset == "GAS":
            cli.sendtoaddress(asset_gas, address, asset_amount)
    except (exceptions.Error, -300) as e:
        traceback.print_exc()
        return responses.tx_fail(e)


def find_address(address, asset):

    # find address in database, if address exists and 24 hours passed since last
    # request update value in row, if address not founded - appending to new row
    if asset == "NEO":
        return dblimits.find_neo_address(address)
    elif asset == "GAS":
        return dblimits.find_gas_address(address)


def db_save_address(query, address, asset):
    if query:
        dblimits.update_request(query)
    else:
        if asset == "NEO":
            dblimits.store_address(dblimits.new_neo_entry(address))
        elif asset == "GAS":
            dblimits.store_address(dblimits.new_gas_entry(address))


def db_save_ip(query, ip):
    if query:
        dblimits.update_request(query)
    else:
        dblimits.store_address(dblimits.new_ip_entry(ip))


def db_save_request_log(addr, account, amount, tokentype, ip):
    new_request_log = dblimits.new_request_log(addr, account, amount,
                                               tokentype, ip)
    dblimits.store_address(new_request_log)
