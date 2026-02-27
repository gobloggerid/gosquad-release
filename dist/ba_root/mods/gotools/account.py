# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import babase
import bacommon.cloud
import bauiv1 as bui

if TYPE_CHECKING:
    pass


class AccountLogin:
    def __init__(self) -> None:
        self._proxyid: str | None = None
        self._proxykey: str | None = None

        # ---- login control ----
        self._login_start_time = time.monotonic()
        self._login_timeout = 60.0  # seconds
        self._poll_interval = 2.0

        # Start proxy login request
        babase.app.plus.cloud.send_message_cb(
            bacommon.cloud.LoginProxyRequestMessage(),
            on_response=babase.CallPartial(self._on_proxy_request_response),
        )

    def _on_proxy_request_response(
        self, response: bacommon.cloud.LoginProxyRequestResponse | Exception
    ) -> None:
        plus = bui.app.plus

        if isinstance(response, Exception):
            print('Login proxy request failed. Falling back to V1 account.')
            self._fallback_to_v1()
            return

        address = plus.get_master_server_address() + response.url
        print('Open this link in your browser and allow:')
        print(address)

        self._proxyid = response.proxyid
        self._proxykey = response.proxykey

        # Start polling for status
        babase.apptimer(
            self._poll_interval,
            babase.CallStrict(self._ask_for_status),
        )

    def _ask_for_status(self) -> None:
        # ---- timeout check ----
        if time.monotonic() - self._login_start_time > self._login_timeout:
            print('Login timed out. Falling back to V1 account.')
            self._fallback_to_v1()
            return

        if self._proxyid is None or self._proxykey is None:
            print('Invalid proxy state. Falling back to V1 account.')
            self._fallback_to_v1()
            return

        babase.app.plus.cloud.send_message_cb(
            bacommon.cloud.LoginProxyStateQueryMessage(
                proxyid=self._proxyid,
                proxykey=self._proxykey,
            ),
            on_response=babase.CallPartial(self._got_status),
        )

    def _got_status(
        self, response: bacommon.cloud.LoginProxyStateQueryResponse | Exception
    ) -> None:
        plus = bui.app.plus

        # ---- server error ----
        if isinstance(response, Exception):
            babase.apptimer(
                self._poll_interval,
                babase.CallStrict(self._ask_for_status),
            )
            return

        # ---- login failed ----
        if response.state is response.State.FAIL:
            print('Login failed. Falling back to V1 account.')
            self._fallback_to_v1()
            return

        # ---- login succeeded ----
        if response.state is response.State.SUCCESS:
            assert response.credentials is not None
            plus.accounts.set_primary_credentials(response.credentials)
            babase.apptimer(1.0, self._logged_in)
            return

        # ---- still waiting ----
        if response.state is response.State.WAITING:
            babase.apptimer(
                self._poll_interval,
                babase.CallStrict(self._ask_for_status),
            )

    def _fallback_to_v1(self) -> None:
        plus = bui.app.plus
        plus.accounts.set_primary_credentials(None)
        plus.sign_in_v1('Local')

    def _logged_in(self) -> None:
        plus = bui.app.plus
        print('Logged in as: ' + plus.get_v1_account_display_string())
