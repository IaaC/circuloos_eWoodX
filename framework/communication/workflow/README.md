# Communication Workflow

The `framework.communication.workflow` package coordinates the distributed lifecycle of actions between an authoritative action store and agent-local execution state.

It connects the framework's core models, storage layer, and transport layer into a reusable distributed workflow:

```text
authoritative actions
        │
        ▼
eligible agent claims work
        │
        ▼
action persisted locally
        │
        ▼
local executor consumes action
        │
        ▼
RUNNING reported
        │
        ▼
operation executes
        │
        ▼
terminal result stored locally
        │
        ▼
terminal result reported
        │
        ▼
local action released
```

The public API is:

```python
from framework.communication.workflow import (
    Coordinator,
    WorkflowHandler,
    WorkflowClient,
    AgentWorkflowHandler,
    AgentPoller,
)
```

## Responsibility

The workflow layer provides:

- discovery and claiming of eligible pending actions;
- workflow request handling around an authoritative `ActionStore`;
- agent-side workflow communication;
- persistence of remotely claimed actions into an `AgentActionStore`;
- polling for new work;
- local action consumption;
- synchronization of `RUNNING` state;
- synchronization of terminal outcomes.

It does **not**:

- define project-specific operations;
- execute the operation represented by an action;
- define orchestration sequences;
- create project-specific actions;
- implement TCP socket mechanics;
- define persistent workspace or entity structures.

Those responsibilities belong to other framework or application layers.

---

# Package Structure

```text
workflow/
├── __init__.py
├── coordinator.py
├── handler.py
├── client.py
├── agent_handler.py
└── agent_poller.py
```

The components divide naturally between the authoritative side and the agent side:

```text
AUTHORITATIVE SIDE

ActionStore
    │
    ▼
Coordinator
    │
    ▼
WorkflowHandler
    │
    │ transport
    ▼

AGENT SIDE

WorkflowClient
    │
    ├── AgentActionStore
    │
    ├── AgentPoller
    │
    └── AgentWorkflowHandler
```

---

# Distributed Workflow Model

The authoritative action lifecycle is:

```text
PENDING
   │
   │ claim
   ▼
CLAIMED
   │
   │ execution starts
   ▼
RUNNING
   │
   ├──────────────► COMPLETED
   ├──────────────► FAILED
   └──────────────► CANCELLED
```

The agent also maintains its own durable execution state:

```text
CLAIMED
   │
   │ executor consumes
   ▼
CONSUMED
   │
   │ RUNNING acknowledged
   ▼
RUNNING
   │
   │ executor finishes
   ▼
TERMINAL
   │
   │ terminal result acknowledged
   ▼
INACTIVE
```

`CONSUMED` is agent-local execution state and is not part of `ActionStatus`.

The workflow layer coordinates these two perspectives rather than merging them into one state representation.

---

# Coordinator

```python
class Coordinator
```

`Coordinator` performs authoritative distributed action coordination using an `ActionStore`.

Its current responsibility is intentionally small: find the next pending action that an agent can handle and claim it for that agent.

## Constructor

```python
Coordinator(
    action_store: ActionStore,
)
```

Example:

```python
from framework.communication.storage import (
    ActionStore,
)

from framework.communication.workflow import (
    Coordinator,
)

action_store = ActionStore(
    root="runtime/actions",
)

coordinator = Coordinator(
    action_store=action_store,
)
```

The supplied object must be an `ActionStore`.

---

## Public attributes

### `action_store`

```python
coordinator.action_store: ActionStore
```

The authoritative store used for action discovery and claiming.

---

## `claim_next()`

```python
coordinator.claim_next(
    agent: Agent,
) -> Action | None
```

Finds and claims the next pending action that the supplied agent can handle.

Example:

```python
from framework.communication.core import Agent

agent = Agent(
    agent_id="processing_pc_01",
    roles=["processing"],
)

action = coordinator.claim_next(
    agent
)
```

The method first asks the authoritative store for pending actions matching the agent's roles:

```text
Agent.roles
    │
    ▼
ActionStore.find_pending(
    targets=agent.roles
)
```

If no eligible action exists:

```python
None
```

is returned.

If one or more eligible actions exist, the first returned action is claimed:

```text
pending actions
      │
      ▼
pending[0]
      │
      ▼
ActionStore.claim()
      │
      ▼
CLAIMED Action
```

The `ActionStore` remains responsible for enforcing whether the claim itself is valid.

---

# WorkflowHandler

```python
class WorkflowHandler
```

`WorkflowHandler` exposes generic authoritative workflow operations through dictionary requests and responses.

It contains no project-specific behavior.

The handler currently supports:

```text
claim_next
mark_running
mark_terminal
```

## Constructor

```python
WorkflowHandler(
    action_store: ActionStore,
)
```

Example:

```python
from framework.communication.storage import (
    ActionStore,
)

from framework.communication.workflow import (
    WorkflowHandler,
)

action_store = ActionStore(
    root="runtime/actions",
)

handler = WorkflowHandler(
    action_store=action_store,
)
```

The constructor also creates a `Coordinator` using the same `ActionStore`.

---

## Public attributes

```python
handler.action_store
handler.coordinator
```

`action_store` is the authoritative action store.

`coordinator` handles eligible action discovery and claiming.

---

## `handle()`

```python
handler.handle(
    request: dict,
) -> dict
```

Processes one workflow request.

The request must be a dictionary.

The `command` value is stripped and normalized to lowercase before routing.

If no command is provided:

```python
{
    "status": "error",
    "message": "Missing command.",
}
```

is returned.

Unknown commands similarly return an error response.

---

# `claim_next` Command

Request:

```python
{
    "command": "claim_next",
    "agent": {
        "agent_id": "processing_pc_01",
        "roles": ["processing"],
        "metadata": {},
    },
}
```

The handler reconstructs the `Agent` and passes it to:

```python
Coordinator.claim_next()
```

When an eligible action exists, the response is:

```python
{
    "status": "ok",
    "action": {
        ...
    },
}
```

The returned action is already authoritatively `CLAIMED`.

When no eligible action exists:

```python
{
    "status": "ok",
    "action": None,
}
```

is returned.

Errors encountered during processing are returned as:

```python
{
    "status": "error",
    "message": "...",
}
```

---

# `mark_running` Command

Request:

```python
{
    "command": "mark_running",
    "action_id": "action-001",
    "agent": {
        ...
    },
}
```

The handler delegates the transition to:

```python
ActionStore.mark_running()
```

The authoritative transition is:

```text
CLAIMED
   ↓
RUNNING
```

On success:

```python
{
    "status": "ok",
    "action": {
        ...
    },
}
```

is returned.

The `ActionStore` enforces ownership and lifecycle validity.

---

# `mark_terminal` Command

Request:

```python
{
    "command": "mark_terminal",
    "action_id": "action-001",
    "action_status": "completed",
    "agent": {
        ...
    },
}
```

`action_status` is converted to `ActionStatus` before being passed to:

```python
ActionStore.mark_terminal()
```

Valid terminal states are:

```text
completed
failed
cancelled
```

The normal authoritative transition is:

```text
RUNNING
   ↓
COMPLETED / FAILED / CANCELLED
```

On success, the serialized authoritative action is returned.

---

# WorkflowClient

```python
class WorkflowClient
```

`WorkflowClient` is the agent-side interface to a remote workflow handler.

It combines:

```text
TCPClient
    +
Agent
    +
AgentActionStore
```

to provide agent-side workflow operations.

## Constructor

```python
WorkflowClient(
    tcp_client: TCPClient,
    agent: Agent,
    local_store: AgentActionStore,
)
```

Example:

```python
from framework.communication.core import Agent
from framework.communication.storage import (
    AgentActionStore,
)
from framework.communication.transport import (
    TCPClient,
)
from framework.communication.workflow import (
    WorkflowClient,
)

agent = Agent(
    agent_id="processing_pc_01",
    roles=["processing"],
)

local_store = AgentActionStore(
    root="runtime/processing_pc_01",
    agent=agent,
)

tcp_client = TCPClient(
    host="127.0.0.1",
    port=5005,
)

workflow_client = WorkflowClient(
    tcp_client=tcp_client,
    agent=agent,
    local_store=local_store,
)
```

The `AgentActionStore` must belong to the same `agent_id` as the supplied `Agent`.

---

## Public attributes

```python
workflow_client.tcp_client
workflow_client.agent
workflow_client.local_store
```

These represent the remote transport client, agent identity, and durable local action store used by the workflow client.

---

## `claim_next()`

```python
workflow_client.claim_next() -> Action | None
```

Requests the next eligible action from the authoritative workflow handler.

The request is:

```python
{
    "command": "claim_next",
    "agent": workflow_client.agent.to_dict(),
}
```

If no action is available:

```python
None
```

is returned.

If an action is returned, the client:

```text
receives action dictionary
        │
        ▼
Action.from_dict()
        │
        ▼
AgentActionStore.save()
        │
        ▼
returns Action
```

Therefore a successfully claimed remote action is persisted locally before `claim_next()` returns it.

If the remote response reports an error, `RuntimeError` is raised.

---

## `mark_running()`

```python
workflow_client.mark_running(
    action_id: str,
) -> Action
```

Reports that a claimed action has started running.

The client sends:

```python
{
    "command": "mark_running",
    "action_id": "...",
    "agent": workflow_client.agent.to_dict(),
}
```

On success, the authoritative `RUNNING` action is reconstructed and returned.

This method reports remote state only.

It does not update `AgentActionStore.local_status`; that local acknowledgement is handled separately by the agent-local workflow logic.

---

## `mark_terminal()`

```python
workflow_client.mark_terminal(
    action_id: str,
    status: str,
) -> Action
```

Reports a terminal result to the authoritative workflow handler.

Accepted status values are:

```text
completed
failed
cancelled
```

Example:

```python
terminal_action = (
    workflow_client.mark_terminal(
        action_id="action-001",
        status="completed",
    )
)
```

On success, the authoritative terminal `Action` is returned.

An invalid terminal status is rejected before the request is sent.

---

# AgentWorkflowHandler

```python
class AgentWorkflowHandler
```

`AgentWorkflowHandler` provides the workflow interface used by software running locally on an agent.

It coordinates:

```text
local executor
      │
      ▼
AgentWorkflowHandler
      │
      ├── AgentActionStore
      │
      └── WorkflowClient
                │
                ▼
        authoritative workflow
```

The handler contains no transport-specific or project-specific execution logic.

Its current commands are:

```text
consume_action
mark_terminal
```

## Constructor

```python
AgentWorkflowHandler(
    local_store: AgentActionStore,
    workflow_client: WorkflowClient,
)
```

The local store and workflow client must belong to the same agent.

---

## Public attributes

```python
handler.local_store
handler.workflow_client
```

---

## `handle()`

```python
handler.handle(
    request: dict,
) -> dict
```

Routes an agent-local workflow request.

Example:

```python
response = handler.handle(
    {
        "command": "consume_action",
    }
)
```

Missing or unknown commands produce an error response.

---

# `consume_action` Command

`consume_action` exposes a locally claimed action to the local executor and synchronizes the start of execution with the authoritative side.

Request:

```python
{
    "command": "consume_action",
}
```

If no unconsumed local action exists:

```python
{
    "status": "ok",
    "trigger": False,
    "action": None,
}
```

is returned.

If an action is available, the sequence is:

```text
AgentActionStore.find_unconsumed()
        │
        ▼
local action found
        │
        ▼
mark_consumed()
        │
        ▼
local_status = consumed
        │
        ▼
WorkflowClient.mark_running()
        │
        ▼
authoritative status = RUNNING
        │
        ▼
mark_running_reported()
        │
        ▼
local_status = running
        │
        ▼
return trigger=True
```

The successful response contains the authoritative running action:

```python
{
    "status": "ok",
    "trigger": True,
    "action": {
        ...
    },
}
```

A key ordering rule is:

> The action is consumed locally before `RUNNING` is reported remotely.

This preserves the fact that the local executor took ownership of the work before the authoritative execution state advances.

---

# `mark_terminal` Agent Command

After execution finishes, the local executor reports its outcome through:

```python
{
    "command": "mark_terminal",
    "action_status": "completed",
}
```

Valid outcomes are:

```text
completed
failed
cancelled
```

The sequence is:

```text
find active local action
        │
        ▼
AgentActionStore.mark_terminal()
        │
        ▼
terminal outcome durable locally
terminal_reported = False
        │
        ▼
WorkflowClient.mark_terminal()
        │
        ▼
authoritative terminal state
        │
        ▼
AgentActionStore.mark_terminal_reported()
        │
        ▼
terminal_reported = True
        │
        ▼
local action becomes inactive
```

This ordering follows the execution-ownership principle:

> The executing side records its own outcome locally before reporting that outcome to the authoritative side.

The local action remains active until the terminal result has been acknowledged.

---

# AgentPoller

```python
class AgentPoller
```

`AgentPoller` continuously looks for distributed work on behalf of an agent.

Its most important rule is:

> Never claim another action while the agent still has an active local action.

The polling sequence is:

```text
check AgentActionStore.find_active()
        │
        ├── active action exists
        │       │
        │       └── return existing action
        │
        └── no active action
                │
                ▼
        WorkflowClient.claim_next()
                │
                ├── no action → None
                │
                └── action claimed
                        │
                        ▼
                  persisted locally
```

## Constructor

```python
AgentPoller(
    workflow_client: WorkflowClient,
    local_store: AgentActionStore,
    interval: float = 1.0,
)
```

Example:

```python
from framework.communication.workflow import (
    AgentPoller,
)

poller = AgentPoller(
    workflow_client=workflow_client,
    local_store=local_store,
    interval=1.0,
)
```

The workflow client and local store must belong to the same agent.

`interval` must be greater than zero.

---

## Public attributes

```python
poller.workflow_client
poller.local_store
poller.interval
```

Threading state such as `_thread`, `_stop_event`, and `_lock` is internal implementation state and is not part of the public API.

---

## `poll_once()`

```python
poller.poll_once() -> dict | None
```

Performs one polling cycle.

It can return:

1. the existing active local action;
2. a newly claimed and locally persisted action;
3. `None` when no action is available.

The local store is always checked first:

```text
find_active()
    │
    ├── found → return it
    │
    └── none  → ask authoritative side
```

This is what prevents an agent from claiming additional work while its current action is:

- claimed;
- consumed;
- running;
- terminal but not yet acknowledged.

Only after the previous local action is terminal and `terminal_reported=True` can polling claim another action.

---

## `start()`

```python
poller.start() -> bool
```

Starts the background polling thread.

The thread is created as a daemon thread.

Returns:

```text
True     a new polling thread was started
False    a polling thread is already running
```

The background loop repeatedly calls:

```python
poller.poll_once()
```

and waits for `interval` seconds between cycles.

Polling exceptions are printed but do not terminate the background loop.

---

## `stop()`

```python
poller.stop(
    join_timeout: float = 2.0,
) -> bool
```

Requests the background polling thread to stop.

Returns:

```text
True     an active polling thread was asked to stop
False    no active polling thread existed
```

The method signals the internal stop event and waits up to `join_timeout` seconds for the thread.

---

# Complete Distributed Flow

The workflow components work together as follows:

```text
AUTHORITATIVE SIDE                         AGENT SIDE

ActionStore
    │
    │ PENDING
    ▼
WorkflowHandler
    ▲
    │                                  AgentPoller
    │                                      │
    │        claim_next                    │
    │◄─────────────────────────────────────┤
    │                                      │
Coordinator                                │
    │                                      │
    ▼                                      │
ActionStore.claim()                        │
    │                                      │
    │ CLAIMED Action                       │
    ├─────────────────────────────────────►│
    │                                      ▼
    │                              AgentActionStore
    │                                      │
    │                              local CLAIMED
    │                                      │
    │                              local executor
    │                                      │
    │                              consume_action
    │                                      │
    │                              local CONSUMED
    │                                      │
    │        mark_running                  │
    │◄─────────────────────────────────────┤
    │                                      │
ActionStore.mark_running()                 │
    │                                      │
    │ RUNNING acknowledgement              │
    ├─────────────────────────────────────►│
    │                                      │
    │                              local RUNNING
    │                                      │
    │                              operation executes
    │                                      │
    │                              local TERMINAL
    │                                      │
    │        mark_terminal                 │
    │◄─────────────────────────────────────┤
    │                                      │
ActionStore.mark_terminal()                │
    │                                      │
    │ terminal acknowledgement             │
    ├─────────────────────────────────────►│
                                           │
                                   terminal_reported=True
                                           │
                                           ▼
                                      INACTIVE
```

---

# Separation of Responsibilities

The workflow package deliberately separates several responsibilities.

## Coordinator

```text
Which pending action can this agent claim?
```

## WorkflowHandler

```text
How are authoritative workflow commands exposed?
```

## WorkflowClient

```text
How does an agent request and report workflow state remotely?
```

## AgentActionStore

```text
What execution state must this agent remember durably?
```

## AgentWorkflowHandler

```text
How does a local executor consume work and report its outcome?
```

## AgentPoller

```text
When is this agent free to ask for another action?
```

Keeping these responsibilities separate prevents transport, persistence, execution, and application logic from becoming one monolithic agent service.

---

# Workflow Boundary

The workflow layer coordinates distributed execution state, but it does not perform the application operation itself.

The intended boundary is:

```text
distributed coordination
        │
        ▼
AgentWorkflowHandler
        │
        │ returns executable Action
        ▼
APPLICATION EXECUTOR
        │
        │ performs operation
        ▼
AgentWorkflowHandler
        │
        │ terminal result
        ▼
distributed coordination
```

This allows the executor to change independently of the communication protocol.

A local executor may be:

- a Python application;
- another local service;
- a visual programming environment;
- a robotic control process;
- another application capable of communicating with the agent.

The workflow framework only coordinates the action lifecycle around that execution.

---

# Important State Ownership Rule

The workflow architecture follows this principle:

> **Status ownership follows execution ownership.**

The authoritative store owns distributed action state.

The executing agent owns its local execution outcome first.

Therefore terminal synchronization follows:

```text
executor finishes
      ↓
persist terminal outcome locally
      ↓
report terminal outcome
      ↓
authoritative side accepts
      ↓
persist acknowledgement locally
```

This is why a terminal local action remains active until:

```python
terminal_reported == True
```

The agent should not accept new work before that synchronization completes.

---

# Package API

The supported package-level imports are:

```python
from framework.communication.workflow import (
    Coordinator,
    WorkflowHandler,
    WorkflowClient,
    AgentWorkflowHandler,
    AgentPoller,
)
```

| Object | Purpose |
|---|---|
| `Coordinator` | Find and claim the next eligible authoritative action for an agent. |
| `WorkflowHandler` | Handle generic authoritative workflow commands. |
| `WorkflowClient` | Agent-side client for claiming work and reporting lifecycle state. |
| `AgentWorkflowHandler` | Coordinate action consumption and terminal reporting for a local executor. |
| `AgentPoller` | Poll for new work only when no active local action exists. |

Internal command-specific handler methods and polling thread implementation details are not part of the public API.