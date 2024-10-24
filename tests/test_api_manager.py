# === UCSF ChimeraX Copyright ===
# Copyright 2022 Regents of the University of California. All rights reserved.
# The ChimeraX application is provided pursuant to the ChimeraX license
# agreement, which covers academic and commercial uses. For more details, see
# <https://www.rbvi.ucsf.edu/chimerax/docs/licensing.html>
#
# You can also
# redistribute and/or modify it under the terms of the GNU Lesser General
# Public License version 2.1 as published by the Free Software Foundation.
# For more details, see
# <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>
#
# THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
# EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. ADDITIONAL LIABILITY
# LIMITATIONS ARE DESCRIBED IN THE GNU LESSER GENERAL PUBLIC LICENSE
# VERSION 2.1
#
# This notice must be embedded in or attached to all copies, including partial
# copies, of the software or any revisions or derivations thereof.
# === UCSF ChimeraX Copyright ===


from unittest.mock import Mock, patch

import pytest
import requests
from chimerax.core.errors import NonChimeraXError


@pytest.mark.parametrize(
    "status_code, expected_exception, expected_message",
    [
        pytest.param(400, None, "An error occurred while making the API call", id="status_400"),
        pytest.param(401, None, "An error occurred while making the API call", id="status_401"),
        pytest.param(403, None, "An error occurred while making the API call", id="status_403"),
        pytest.param(404, None, "An error occurred while making the API call", id="status_404"),
        pytest.param(500, NonChimeraXError, "Schol-AR server error occurred making the API call", id="status_500"),
        pytest.param(502, NonChimeraXError, "Schol-AR server error occurred making the API call", id="status_502"),
        pytest.param(503, NonChimeraXError, "Schol-AR server error occurred making the API call", id="status_503"),
        pytest.param(504, NonChimeraXError, "Schol-AR server error occurred making the API call", id="status_504"),
    ]
)
def test_try_api_request(test_production_session, status_code, expected_exception, expected_message):
    from chimerax.scholar.io import APIManager

    # Mock the response to simulate different status codes
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_response.status_code = status_code
    mock_response.url = "http://example.com"

    with patch('requests.get', return_value=mock_response):
        if expected_exception:
            with pytest.raises(expected_exception) as excinfo:
                APIManager.try_api_request(requests.get, "http://example.com")
            real_message = str(excinfo.value)
            assert expected_message in real_message
        else:
            result = APIManager.try_api_request(requests.get, "http://example.com")
            assert result is None
