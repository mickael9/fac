'''Helper classes to access the Factorio Mod API'''

from urllib.parse import quote
from functools import lru_cache

import requests

from fac.utils import JSONDict

__all__ = ['API', 'ModNotFoundError', 'AuthError', 'OwnershipError']

BASE_URL = 'https://mods.factorio.com/api/'
LOGIN_URL = 'https://auth.factorio.com/api-login'
DEFAULT_PAGE_SIZE = 25
DEFAULT_ORDER = 'top'


class API:
    def __init__(self, base_url=BASE_URL, login_url=LOGIN_URL, session=None):
        self.base_url = base_url
        self.login_url = login_url
        self.url = base_url.rstrip('/') + '/mods'
        self.session = session or requests.session()

    def search(self,
               query, tags=[],
               order=DEFAULT_ORDER,
               page_size=DEFAULT_PAGE_SIZE,
               page=1,
               limit=0):

        count = 0

        while True:
            resp = self.session.get(self.url, params=dict(
                q=query,
                tags=','.join(tags),
                order=order,
                page_size=page_size,
                page=page,
            ))
            resp.raise_for_status()
            data = JSONDict(resp.json())
            pages = data.pagination.page_count

            for result in data.results:
                count += 1
                yield result
                if limit and limit == count:
                    return

            page += 1
            if page > pages:
                break

    @lru_cache()
    def get(self, mod_name):
        resp = self.session.get('%s/%s' % (self.url, quote(mod_name)))
        if resp.status_code == 404:
            raise ModNotFoundError(
                "'%s' is not on the mod portal" % mod_name)
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
        except:
            json = None

        try:
            resp.raise_for_status()
            return json[0]
        except requests.HTTPError:
            if isinstance(json, dict) and 'message' in json:
                if json['message'] == 'Insufficient membership':
                    raise OwnershipError(json['message'])
                else:
                    raise AuthError(json['message'])
            else:
                raise


class AuthError(Exception):
    pass


class OwnershipError(AuthError):
    pass


class ModNotFoundError(Exception):
    pass
