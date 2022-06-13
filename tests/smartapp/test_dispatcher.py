# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,wildcard-import:

import os
from unittest.mock import MagicMock

import pytest

from smartapp.converter import CONVERTER
from smartapp.dispatcher import SmartAppConfigPage, SmartAppDefinition, SmartAppDispatcher, SmartAppEventHandler
from smartapp.interface import *
from tests.testutil import load_data

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures/samples")
REQUEST_DIR = os.path.join(FIXTURE_DIR, "request")


@pytest.fixture
def requests():
    return load_data(REQUEST_DIR)


@pytest.fixture
def definition():
    return SmartAppDefinition(
        id="id",
        name="name",
        description="description",
        target_url="target_url",
        permissions=["permission"],
        config_pages=[
            SmartAppConfigPage(
                page_name="First page",
                sections=[
                    ConfigSection(
                        name="Section 1",
                        settings=[
                            ParagraphSetting(
                                id="paragraph-id",
                                name="paragraph-name",
                                description="paragraph-description",
                                default_value="paragraph-text",
                            ),
                        ],
                    )
                ],
            ),
            SmartAppConfigPage(
                page_name="Second page",
                sections=[
                    ConfigSection(
                        name="Section 2",
                        settings=[
                            DecimalSetting(
                                id="decimal-id",
                                name="decimal-name",
                                description="decimal-description",
                                required=False,
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


@pytest.fixture
def event_handler() -> SmartAppEventHandler:
    return MagicMock()


@pytest.fixture
def dispatcher(definition: SmartAppDefinition, event_handler: SmartAppEventHandler) -> SmartAppDispatcher:
    return SmartAppDispatcher(definition=definition, event_handler=event_handler)


# noinspection PyUnresolvedReferences
class TestSmartAppDispatcher:

    # Most of the lifecycle events are very similar and don't do much, so they're
    # grouped together in a single test.  Configuration is more complicated and is
    # tested separately.

    def test_json_exception(self, dispatcher):
        # We only need to test this for one case, since error handling is the same everywhere
        status, response_json = dispatcher.dispatch(headers={}, request_json="bogus")
        assert status == 500
        assert response_json == ""

    def test_handler_exception(self, requests, dispatcher):
        # We only need to test this for one case, since error handling is the same everywhere
        request_json = requests["CONFIRMATION.json"]
        dispatcher.event_handler.handle_confirmation.side_effect = Exception("Hello")
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 500
        assert response_json == ""

    def test_confirmation(self, requests, dispatcher):
        request_json = requests["CONFIRMATION.json"]
        request = CONVERTER.from_json(request_json, ConfirmationRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(ConfirmationResponse(target_url="target_url"))
        dispatcher.event_handler.handle_confirmation.assert_called_once_with(request)

    def test_install(self, requests, dispatcher):
        request_json = requests["INSTALL.json"]
        request = CONVERTER.from_json(request_json, InstallRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(InstallResponse())
        dispatcher.event_handler.handle_install.assert_called_once_with(request)

    def test_update(self, requests, dispatcher):
        request_json = requests["UPDATE.json"]
        request = CONVERTER.from_json(request_json, UpdateRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(UpdateResponse())
        dispatcher.event_handler.handle_update.assert_called_once_with(request)

    def test_uninstall(self, requests, dispatcher):
        request_json = requests["UNINSTALL.json"]
        request = CONVERTER.from_json(request_json, UninstallRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(UninstallResponse())
        dispatcher.event_handler.handle_uninstall.assert_called_once_with(request)

    def test_oauth_callback(self, requests, dispatcher):
        request_json = requests["OAUTH_CALLBACK.json"]
        request = CONVERTER.from_json(request_json, OauthCallbackRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(OauthCallbackResponse())
        dispatcher.event_handler.handle_oauth_callback.assert_called_once_with(request)

    def test_event(self, requests, dispatcher):
        request_json = requests["EVENT-DEVICE.json"]
        request = CONVERTER.from_json(request_json, EventRequest)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(EventResponse())
        dispatcher.event_handler.handle_event.assert_called_once_with(request)


# noinspection PyUnresolvedReferences
class TestSmartAppDispatcherConfig:
    def test_configuration_initialize(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id", phase=ConfigPhase.INITIALIZE, page_id="", previous_page_id="", config={}
            ),
        )
        response = ConfigurationInitResponse(
            configuration_data=ConfigInitData(
                # this is all from the provided SmartApp definition
                initialize=ConfigInit(
                    id="id",
                    name="name",
                    description="description",
                    permissions=["permission"],
                    first_page_id="1",
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(request)

    def test_configuration_page_1of2(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id",
                phase=ConfigPhase.PAGE,
                page_id="1",
                previous_page_id="",
                config={},  # TODO: not 100% clear what comes across in these page requests, examples are odd
            ),
        )
        response = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                # most of this comes from the provided SmartApp definition, but some is derived
                page=ConfigPage(
                    page_id="1",
                    name="First page",
                    previous_page_id=None,
                    next_page_id="2",
                    complete=False,
                    sections=[
                        ConfigSection(
                            name="Section 1",
                            settings=[
                                ParagraphSetting(
                                    id="paragraph-id",
                                    name="paragraph-name",
                                    description="paragraph-description",
                                    default_value="paragraph-text",
                                ),
                            ],
                        )
                    ],
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(request)

    def test_configuration_page_2of2(self, dispatcher):
        request = ConfigurationRequest(
            lifecycle=LifecyclePhase.CONFIGURATION,
            execution_id="execution_id",
            locale="locale",
            version="version",
            configuration_data=ConfigRequestData(
                installed_app_id="installed_app_id",
                phase=ConfigPhase.PAGE,
                page_id="2",
                previous_page_id="",
                config={},  # TODO: not 100% clear what comes across in these page requests, examples are odd
            ),
        )
        response = ConfigurationPageResponse(
            configuration_data=ConfigPageData(
                # most of this comes from the provided SmartApp definition, but some is derived
                page=ConfigPage(
                    page_id="2",
                    name="Second page",
                    previous_page_id="1",
                    next_page_id=None,
                    complete=True,
                    sections=[
                        ConfigSection(
                            name="Section 2",
                            settings=[
                                DecimalSetting(
                                    id="decimal-id",
                                    name="decimal-name",
                                    description="decimal-description",
                                    required=False,
                                ),
                            ],
                        )
                    ],
                )
            )
        )
        request_json = CONVERTER.to_json(request)
        status, response_json = dispatcher.dispatch(headers={}, request_json=request_json)
        assert status == 200
        assert response_json == CONVERTER.to_json(response)
        dispatcher.event_handler.handle_configuration.assert_called_once_with(request)