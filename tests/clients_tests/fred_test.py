# filepath: /tests/clients_tests/fred_test.py
#
# Copyright (c) 2026 Nikhil Sunder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import httpx
import respx

from fedfred.clients import Fred
from fedfred.models import Category


class TestFred:

    @respx.mock
    def test_get_category(self):
        """get_category issues the correct FRED request and returns a parsed Category."""
        payload = {
            "categories": [
                {"id": 125, "name": "Trade Balance", "parent_id": 13},
            ]
        }
        route = respx.get("https://api.stlouisfed.org/fred/category").mock(
            return_value=httpx.Response(200, json=payload)
        )

        fred = Fred(api_key="abcdefghijklmnopqrstuvwxyz123456")

        category = fred.get_category(125)

        # --- request shape: endpoint path + fully-injected query params ---------
        assert route.called
        request = route.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/fred/category"
        assert dict(request.url.params) == {
            "category_id": "125",
            "api_key": "abcdefghijklmnopqrstuvwxyz123456",
            "file_type": "json",
        }

        # --- parsed result -------------------------------------------------------
        assert isinstance(category, Category)
        assert category.id == 125
        assert category.name == "Trade Balance"
        assert category.parent_id == 13