#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import asyncio
import uuid

from azure.servicebus.aio import ServiceBusClient, AutoLockRenewer
from azure.servicebus import ServiceBusMessage, NEXT_AVAILABLE_SESSION
from azure.servicebus.exceptions import OperationTimeoutError
from azure.identity.aio import DefaultAzureCredential


FULLY_QUALIFIED_NAMESPACE = os.environ["SERVICEBUS_FULLY_QUALIFIED_NAMESPACE"]
# Note: This must be a session-enabled queue.
SESSION_QUEUE_NAME = os.environ["SERVICEBUS_SESSION_QUEUE_NAME"]


async def message_processing(servicebus_client, queue_name):
    while True:
        try:
            # max_wait_time below is the maximum time the receiver will wait to connect to a session and to receive messages from the service
            async with servicebus_client.get_queue_receiver(
                queue_name, max_wait_time=1, session_id=NEXT_AVAILABLE_SESSION
            ) as receiver:
                renewer = AutoLockRenewer()
                renewer.register(receiver, receiver.session)
                await receiver.session.set_state("OPEN")
                async for message in receiver:
                    print("Message: {}".format(message))
                    print("Time to live: {}".format(message.time_to_live))
                    print("Sequence number: {}".format(message.sequence_number))
                    print("Enqueue Sequence number: {}".format(message.enqueued_sequence_number))
                    print("Partition Key: {}".format(message.partition_key))
                    print("Locked until: {}".format(message.locked_until_utc))
                    print("Lock Token: {}".format(message.lock_token))
                    print("Enqueued time: {}".format(message.enqueued_time_utc))
                    await receiver.complete_message(message)
                    if str(message) == "shutdown":
                        await receiver.session.set_state("CLOSED")
                        break
                await renewer.close()
        except OperationTimeoutError:
            print(
                "If timeout occurs during connecting to a session,"
                "It indicates that there might be no non-empty sessions remaining; exiting."
                "This may present as a UserError in the azure portal metric."
            )
            return


async def sample_session_send_receive_with_pool_async(fully_qualified_namespace, queue_name):

    concurrent_receivers = 5
    sessions = [str(uuid.uuid4()) for i in range(concurrent_receivers)]
    credential = DefaultAzureCredential()
    client = ServiceBusClient(fully_qualified_namespace, credential)

    for session_id in sessions:
        async with client.get_queue_sender(queue_name) as sender:
            await asyncio.gather(
                *[
                    sender.send_messages(ServiceBusMessage("Sample message no. {}".format(i), session_id=session_id))
                    for i in range(20)
                ]
            )
            await sender.send_messages(ServiceBusMessage("shutdown", session_id=session_id))

    receive_sessions = [message_processing(client, queue_name) for _ in range(concurrent_receivers)]
    await asyncio.gather(*receive_sessions)


if __name__ == "__main__":
    asyncio.run(sample_session_send_receive_with_pool_async(FULLY_QUALIFIED_NAMESPACE, SESSION_QUEUE_NAME))
