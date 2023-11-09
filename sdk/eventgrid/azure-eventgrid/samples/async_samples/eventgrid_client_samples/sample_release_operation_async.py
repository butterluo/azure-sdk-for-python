# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import os
import asyncio
from azure.core.credentials import AzureKeyCredential
from azure.eventgrid.aio import EventGridClient
from azure.eventgrid.models import *
from azure.core.exceptions import HttpResponseError

EVENTGRID_KEY: str = os.environ["EVENTGRID_KEY"]
EVENTGRID_ENDPOINT: str = os.environ["EVENTGRID_ENDPOINT"]
TOPIC_NAME: str = os.environ["EVENTGRID_TOPIC_NAME"]
EVENT_SUBSCRIPTION_NAME: str = os.environ["EVENTGRID_EVENT_SUBSCRIPTION_NAME"]

# Create a client
client = EventGridClient(EVENTGRID_ENDPOINT, AzureKeyCredential(EVENTGRID_KEY))


async def run():
    # Release a LockToken
    try:
        async with client:
            tokens = ReleaseOptions(lock_tokens=["token"])
            release_events = await client.release_cloud_events(
                topic_name=TOPIC_NAME,
                event_subscription_name=EVENT_SUBSCRIPTION_NAME,
                release_delay_in_seconds=10,
                release_options=tokens,
            )
            print(release_events)
    except HttpResponseError:
        raise


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())