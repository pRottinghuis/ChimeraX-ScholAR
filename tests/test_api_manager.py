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
        pytest.param(500, NonChimeraXError, "Schol-AR server error occurred: 500", id="status_500"),
        pytest.param(502, NonChimeraXError, "Schol-AR server error occurred: 502", id="status_502"),
        pytest.param(503, NonChimeraXError, "Schol-AR server error occurred: 503", id="status_503"),
        pytest.param(504, NonChimeraXError, "Schol-AR server error occurred: 504", id="status_504"),
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
                APIManager.try_api_request(requests.get, True, "http://example.com")
            real_message = str(excinfo.value)
            assert expected_message in real_message
        else:
            result = APIManager.try_api_request(requests.get, True, "http://example.com")
            assert result is None
