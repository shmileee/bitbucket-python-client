from __future__ import print_function

import json
import os

import requests
from furl import furl
from requests.auth import AuthBase

BITBUCKET_URL = os.getenv("BITBUCKET_URL")

if BITBUCKET_URL is None:
    raise EnvironmentError("BITBUCKET_URL is not set.")

class TimeoutError(Exception):
    pass


class ConnectionError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class BitbucketAuth(AuthBase):
    def __init__(self, token=None):
        """

        Args:
            token (str, optional):
        """

        if token is not None:
            self._token = token
            return
        raise ValueError("Need token for authentication")

    @property
    def token(self):
        return self._token

    def __eq__(self, other):
        return self._token == getattr(other, "_token", None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer {}".format(self._token)
        return r


def parse_url(url):
    """Parses a url into the base url and the query params

    Args:
        url (str): url with query string, or not

    Returns:
        (str, `dict` of `lists`): url, query (dict of values)
    """
    f = furl(url)
    query = f.args
    query = {a[0]: a[1] for a in query.listitems()}
    f.remove(query=True).path.normalize()
    url = f.url

    return url, query


class Bitbucket(object):
    """Actual class for making API calls

    Args:
        token(str, optional):
        url(str, optional): Url of api
        version(str, optional): Api version (1.0)
    """

    def __init__(self, token=None, url=None, version="1.0"):

        self._version = version
        self._url = "{0}/{1}".format(
            url or BITBUCKET_URL, self.version
        )
        self._session = requests.Session()
        self._auth = None
        self._token = None
        self.login(token)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._session.close()

    @property
    def logged_in(self):
        return self.token is not None

    @property
    def version(self):
        return self._version

    @property
    def url(self):
        return self._url

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def _do_request(self, method, address, **kwargs):
        try:
            if "timeout" not in kwargs:
                kwargs["timeout"] = (5, 15)

            if "auth" not in kwargs:
                kwargs["auth"] = self._auth

            if "headers" not in kwargs:
                kwargs["headers"] = {"Content-Type": "application/json"}
            elif "Content-Type" not in kwargs["headers"]:
                kwargs["headers"]["Content-Type"] = "application/json"

            url, query = parse_url(address)
            if query:
                address = url
                if "params" in kwargs:
                    query.update(kwargs["params"])
                kwargs["params"] = query
            resp = self._session.request(method, address, **kwargs)

        except requests.exceptions.Timeout as e:
            raise TimeoutError("Connection Timeout. Download failed: {0}".format(e))
        except requests.exceptions.RequestException as e:
            raise ConnectionError("Connection Error. Download failed: {0}".format(e))
        else:
            try:
                resp.raise_for_status()
            except:
                print(resp.json())
                print(resp.headers)
                raise
            return resp

    def _do_requests_get(self, address, **kwargs):
        if "params" not in kwargs:
            kwargs["params"] = {}
        return self._do_request("GET", address, **kwargs)

    def _do_requests_post(self, address, json_data=None, **kwargs):
        return self._do_request("POST", address, json=json_data, **kwargs)

    def _do_requests_put(self, address, json_data=None, **kwargs):
        return self._do_request("PUT", address, json=json_data, **kwargs)

    def _do_requests_patch(self, address, json_data, **kwargs):
        return self._do_request("PATCH", address, json=json_data, **kwargs)

    def _do_requests_delete(self, address, **kwargs):
        return self._do_request("DELETE", address, **kwargs)

    def _iter_requests_get(self, address, **kwargs):
        return self._iter_requests_get_generator(address, **kwargs)

    def _iter_requests_get_generator(self, address, **kwargs):
        _next = None
        resp = self._do_requests_get(address, **kwargs)

        while True:
            if _next:
                resp = self._do_requests_get(_next)

            resp = resp.json()

            for i in resp["results"]:
                yield i

            if resp["next"]:
                _next = resp["next"]
                continue
            return

    def _api_url(self, path):
        return "{0}/{1}/".format(self.url, path)

    def login(self, token=None):
        """Logs into Bitbucket and gets a token

        Token should be specified

        Args:
            token (str, optional):

        Returns:

        """

        self._token = token
        if token is not None:
            # login with token
            self._auth = BitbucketAuth(token=token)
        else:
            # don't login
            return

        self._token = self._auth.token

    def create_pullrequest(
        self, project, repository, source_branch, target_branch, title, description
    ):
        """

        Args:
            project:
            repository:
            source_branch:
            target_branch:
            description:
            title:

        Returns:

        """

        url = self._api_url(
            "projects/{}/repos/{}/pull-requests".format(project, repository)
        )
        return self._do_requests_post(
            url,
            {
                "description": "{}".format(description),
                "closed": "False",
                "fromRef": {
                    "id": "refs/heads/{}".format(source_branch),
                    "repository": {
                        "name": "null",
                        "project": {"key": "{}".format(project)},
                        "slug": "{}".format(repository),
                    },
                },
                "state": "OPEN",
                "title": "{}".format(title),
                "locked": "False",
                "reviewers": [],
                "open": "True",
                "toRef": {
                    "id": "refs/heads/{}".format(target_branch),
                    "repository": {
                        "name": "null",
                        "project": {"key": "{}".format(project)},
                        "slug": "{}".format(repository),
                    },
                },
            },
        ).json()


if __name__ == "__main__":
    pass

__all__ = [
    "Bitbucket",
    "BitbucketAuth",
    "AuthenticationError",
    "ConnectionError",
    "TimeoutError",
]
