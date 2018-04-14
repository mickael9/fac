"""Helper classes to access the Factorio Mod API"""

import json

from urllib.parse import quote
from functools import lru_cache

import requests
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter

from fac.utils import JSONDict, JSONList
from fac.errors import ModNotFoundError, AuthError, OwnershipError

BASE_URL = 'https://mods.factorio.com/api/'
LOGIN_URL = 'https://auth.factorio.com/api-login'
DEFAULT_PAGE_SIZE = 25


class API:
    def __init__(self, base_url=BASE_URL, login_url=LOGIN_URL, session=None):
        self.base_url = base_url
        self.login_url = login_url
        self.url = base_url.rstrip('/') + '/mods'
        self.session = session or requests.session()
        adapter = HTTPAdapter(max_retries=Retry(status_forcelist=[500, 503]))
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def get_mods(self, progress=None, page_size='max'):
        resp = self.get(self.url, params=dict(page_size=page_size),
                        stream=True)
        resp.raise_for_status()
        content_length = int(resp.headers['content-length'])
        data = bytearray()

        for chunk in resp.iter_content(chunk_size=1024):
            data.extend(chunk)
            if progress:
                progress(resp.raw.tell(), content_length)

        return JSONList(json.loads(data.decode('utf-8'))['results'])

    @lru_cache()
    def get_mod(self, mod_name):
        resp = self.session.get('%s/%s' % (self.url, quote(mod_name)))
        if resp.status_code == 404:
            raise ModNotFoundError(mod_name)
        else:
            resp.raise_for_status()

        return JSONDict(resp.json())

    def login(self, username, password, require_ownership=False):
        resp = self.session.post(
            self.login_url,
            params=dict(require_game_ownership=int(require_ownership)),
            data=dict(username=username, password=password)
        )

        try:
            json = resp.json()
        except Exception:
            json = None

        try:
            resp.raise_for_status()
            return json[0]
        except requests.HTTPError:
            if isinstance(json, dict) and 'message' in json:
                if json['message'] == "Insufficient membership":
                    raise OwnershipError(json['message'])
                else:
                    raise AuthError(json['message'])
            else:
                raise

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)
