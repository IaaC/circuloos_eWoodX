# Communication Storage

The `framework.communication.storage` package provides persistent storage for distributed actions and agent-local execution state.

It builds on the transport-independent models defined in `framework.communication.core` and provides two different storage responsibilities:

```python
from framework.communication.storage import (
    ActionStore,
    AgentActionStore,
)
```

The distinction between these stores is fundamental:

```text
ActionStore
    │
    └── authoritative distributed action state

AgentActionStore
    │
    └── durable local execution state for one agent
```

They intentionally do not represent the same state.

## Responsibility

The communication storage layer provides:

- persistent JSON storage for distributed actions;
- authoritative action lifecycle transitions;
- action discovery and claiming;
- agent-local persistence of claimed work;
- local consumption state;
- local execution state;
- terminal synchronization tracking;
- protection against multiple simultaneously active local actions.

It does **not**:

- communicate over the network;
- poll remote services;
- execute actions;
- dispatch project-specific operations;
- define orchestration sequences.

Those responsibilities belong to other framework layers.

---

# Storage Model

Both stores use one JSON file per action:

```text
<root>/
├── <action_id_1>.json
├── <action_id_2>.json
└── ...
```

The root directory is created lazily when data is first saved.

Writes use a temporary file followed by replacement of the target file:

```text
<action_id>.json.tmp
        ↓
<action_id>.json
```

This prevents the normal write operation from directly overwriting the persistent file while JSON is still being written.

---

# ActionStore

```python
class ActionStore
```

`ActionStore` persists the authoritative distributed representation of `Action` objects.

It is responsible for storing actions and enforcing the main distributed lifecycle transitions:

```text
PENDING
   ↓ claim()
CLAIMED
   ↓ mark_running()
RUNNING
   ↓ mark_terminal()
COMPLETED / FAILED / CANCELLED
```

## Constructor

```python
ActionStore(
    root: str | Path,
)
```

Example:

```python
from framework.communication.storage import ActionStore

store = ActionStore(
    root="runtime/actions",
)
```

The supplied path is converted to an absolute resolved `Path`.

Creating an `ActionStore` does not itself create the directory.

---

## Public attributes

### `root`

```python
store.root: Path
```

Resolved root directory containing the stored action JSON files.

---

## `save()`

```python
store.save(
    action: Action,
) -> Path
```

Persists an `Action`.

Example:

```python
from framework.communication.core import Action
from framework.communication.storage import ActionStore

store = ActionStore(
    root="runtime/actions",
)

action = Action(
    action="process_data",
    target="processing",
)

path = store.save(action)
```

The resulting file is:

```text
runtime/actions/<action_id>.json
```

The method creates the storage directory if necessary.

The supplied object must be an `Action`.

---

## `load()`

```python
store.load(
    action_id: str,
) -> Action
```

Loads a stored action and reconstructs it as an `Action` object.

Example:

```python
action = store.load(
    action_id="action-001",
)
```

If the action does not exist, `FileNotFoundError` is raised.

---

## `exists()`

```python
store.exists(
    action_id: str,
) -> bool
```

Returns whether a stored action exists.

Example:

```python
if store.exists(action.action_id):
    print("Action exists.")
```

---

## `delete()`

```python
store.delete(
    action_id: str,
) -> bool
```

Deletes the stored action.

Returns:

```text
True     file existed and was deleted
False    no stored action existed
```

---

## `list_actions()`

```python
store.list_actions() -> list[Action]
```

Loads all actions stored in the root directory.

Files are processed in sorted filename order.

If the storage directory does not yet exist, an empty list is returned.

Example:

```python
actions = store.list_actions()

for action in actions:
    print(
        action.action_id,
        action.status,
    )
```

---

## `find_pending()`

```python
store.find_pending(
    targets: list[str] | None = None,
) -> list[Action]
```

Returns stored actions whose status is:

```python
ActionStatus.PENDING
```

Without a target filter:

```python
pending = store.find_pending()
```

all pending actions are returned.

A collection of targets can be supplied:

```python
pending = store.find_pending(
    targets=[
        "processing",
        "preview",
    ],
)
```

Only pending actions whose `target` matches one of the supplied targets are returned.

Target values are stripped and normalized to lowercase before comparison.

This method performs discovery only. It does not claim the returned actions.

---

# Authoritative Lifecycle Operations

`ActionStore` also enforces the authoritative action lifecycle.

## `claim()`

```python
store.claim(
    action_id: str,
    agent: Agent,
) -> Action
```

Claims a pending action for an eligible agent.

The transition is:

```text
PENDING
   ↓
CLAIMED
```

The claim succeeds only when:

1. the supplied agent is an `Agent`;
2. the action is currently `PENDING`;
3. the agent can handle the action's `target`;
4. the action does not already have a claimant.

On success:

```python
action.status = ActionStatus.CLAIMED
action.claimed_by = agent.agent_id
```

and the updated action is persisted.

Example:

```python
from framework.communication.core import Agent

agent = Agent(
    agent_id="processing_pc_01",
    roles=["processing"],
)

claimed = store.claim(
    action_id=action.action_id,
    agent=agent,
)
```

An agent's eligibility is determined by the relationship:

```text
Action.target
     │
     ▼
Agent.roles
```

---

## `mark_running()`

```python
store.mark_running(
    action_id: str,
    agent: Agent,
) -> Action
```

Moves a claimed action into the running state.

```text
CLAIMED
   ↓
RUNNING
```

The transition succeeds only when:

- the action is currently `CLAIMED`;
- the supplied agent is the same agent recorded in `claimed_by`.

Example:

```python
running = store.mark_running(
    action_id=claimed.action_id,
    agent=agent,
)
```

A different agent cannot move the action to `RUNNING`.

---

## `mark_terminal()`

```python
store.mark_terminal(
    action_id: str,
    agent: Agent,
    status: ActionStatus,
) -> Action
```

Records the authoritative terminal result of a running action.

Accepted terminal states are:

```python
ActionStatus.COMPLETED
ActionStatus.FAILED
ActionStatus.CANCELLED
```

The normal transition is:

```text
RUNNING
   ↓
COMPLETED
   or
FAILED
   or
CANCELLED
```

The action must belong to the supplied agent.

Example:

```python
completed = store.mark_terminal(
    action_id=running.action_id,
    agent=agent,
    status=ActionStatus.COMPLETED,
)
```

### Idempotent terminal reporting

Reporting the **same terminal result again** is accepted.

For example:

```text
COMPLETED
    ↓ repeated COMPLETED report
COMPLETED
```

returns the existing action without changing it.

This supports retry when the authoritative transition succeeded but its response was lost before the reporting side received acknowledgement.

A different or invalid transition is not accepted.

---

# AgentActionStore

```python
class AgentActionStore
```

`AgentActionStore` persists durable execution state for **one specific agent**.

Unlike `ActionStore`, it does not represent the authoritative distributed lifecycle.

Its purpose is to allow an agent to remember:

- which action it currently owns;
- whether that action has been consumed by the local executor;
- its local execution status;
- whether its terminal outcome has been acknowledged by the authoritative side.

This separation allows local execution state to survive independently of communication.

## Constructor

```python
AgentActionStore(
    root: str | Path,
    agent: Agent,
)
```

Example:

```python
from framework.communication.core import Agent
from framework.communication.storage import AgentActionStore

agent = Agent(
    agent_id="processing_pc_01",
    roles=["processing"],
)

local_store = AgentActionStore(
    root="runtime/processing_pc_01",
    agent=agent,
)
```

---

## Public attributes

### `root`

```python
local_store.root: Path
```

Resolved directory containing the agent's local action records.

### `agent`

```python
local_store.agent: Agent
```

The agent whose execution state is represented by this store.

---

# Local Record Structure

When an action is first stored locally, its record has the following structure:

```python
{
    "agent_id": "processing_pc_01",

    "action": {
        "action_id": "...",
        "action": "process_data",
        "target": "processing",
        "status": "claimed",
        "claimed_by": "processing_pc_01",
        "payload": {},
        "metadata": {},
    },

    "local_status": "claimed",
    "consumed": False,
    "terminal_reported": False,
}
```

Three parts are important:

```text
action
    original distributed Action representation

local_status
    current local execution state

terminal_reported
    whether a terminal result has been acknowledged remotely
```

The embedded `action.status` and `local_status` should therefore not be treated as the same field.

The embedded action represents the distributed action that was persisted locally when claimed, while `local_status` tracks subsequent local execution progress.

---

## `save()`

```python
local_store.save(
    action: Action,
) -> Path
```

Persists a claimed action for the local agent.

The action must satisfy:

```python
action.claimed_by == local_store.agent.agent_id
```

Otherwise the action is rejected.

A newly saved action starts with:

```text
local_status      = "claimed"
consumed          = False
terminal_reported = False
```

### Single-active-action rule

The store allows only one active local action at a time.

If another active action already exists, saving a different action raises `RuntimeError`.

Saving the same active action again returns its existing path rather than creating another local action.

This rule provides the durable local basis for preventing an agent from accepting new work while previous work remains active.

---

## `load()`

```python
local_store.load(
    action_id: str,
) -> dict
```

Loads the complete local action record.

Unlike `ActionStore.load()`, this method returns a dictionary rather than an `Action`, because the record contains additional agent-local state around the embedded action.

If the record does not exist, `FileNotFoundError` is raised.

---

## `exists()`

```python
local_store.exists(
    action_id: str,
) -> bool
```

Returns whether a local action record exists.

---

## `delete()`

```python
local_store.delete(
    action_id: str,
) -> bool
```

Deletes a local action record.

Returns `True` if a file was deleted and `False` if no corresponding file existed.

---

# Local Execution Lifecycle

The local store tracks an execution lifecycle that is related to, but distinct from, the authoritative `ActionStatus` lifecycle.

A normal local sequence is:

```text
CLAIMED
   ↓ mark_consumed()
CONSUMED
   ↓ mark_running_reported()
RUNNING
   ↓ mark_terminal()
COMPLETED / FAILED / CANCELLED
   ↓ mark_terminal_reported()
terminal synchronization acknowledged
```

`CONSUMED` is a **local execution state**.

It is not a member of `ActionStatus`.

---

## `mark_consumed()`

```python
local_store.mark_consumed(
    action_id: str,
) -> dict
```

Records that the local executor has consumed the claimed action.

The transition is:

```text
claimed
   ↓
consumed
```

The method sets:

```python
data["consumed"] = True
data["local_status"] = "consumed"
```

Calling the method again when the action is already `consumed` is idempotent and returns the existing record.

Other source states are rejected.

---

## `mark_running_reported()`

```python
local_store.mark_running_reported(
    action_id: str,
) -> dict
```

Records that the running state has been accepted by the authoritative side.

The local state becomes:

```text
running
```

The method accepts local state:

```text
claimed
or
consumed
```

and changes it to:

```text
running
```

Calling it again when already `running` is idempotent.

This method does not itself perform communication. It only persists the local acknowledgement state.

---

## `mark_terminal()`

```python
local_store.mark_terminal(
    action_id: str,
    status: str,
) -> dict
```

Records the executor's terminal outcome locally.

Accepted values are:

```text
completed
failed
cancelled
```

The normal transition is:

```text
running
   ↓
completed / failed / cancelled
```

When a terminal state is recorded:

```python
data["local_status"] = status
data["terminal_reported"] = False
```

This is deliberate: the local execution outcome exists before confirmation that the authoritative side has accepted it.

Reporting the same terminal status repeatedly is idempotent.

---

## `mark_terminal_reported()`

```python
local_store.mark_terminal_reported(
    action_id: str,
) -> dict
```

Records that the locally stored terminal outcome has been accepted by the authoritative side.

The action must already have one of these local states:

```text
completed
failed
cancelled
```

The method then sets:

```python
data["terminal_reported"] = True
```

Repeated calls after acknowledgement are idempotent.

---

## `is_consumed()`

```python
local_store.is_consumed(
    action_id: str,
) -> bool
```

Returns the persistent value of the local `consumed` flag.

Example:

```python
if local_store.is_consumed(action_id):
    print("Action has already been consumed.")
```

---

## `find_unconsumed()`

```python
local_store.find_unconsumed() -> dict | None
```

Returns the first local action belonging to the store's agent whose:

```python
consumed == False
```

If no such action exists, `None` is returned.

This is used to identify work that has been persisted locally but has not yet been consumed by an executor.

---

## `find_active()`

```python
local_store.find_active() -> dict | None
```

Returns the current active local action.

If no active action exists, it returns `None`.

The definition of **active** is important.

The following states are active:

```text
claimed
consumed
running
```

A terminal action is also still active when its terminal result has not yet been acknowledged:

```text
completed + terminal_reported=False
failed    + terminal_reported=False
cancelled + terminal_reported=False
```

Only a terminal action with:

```python
terminal_reported == True
```

is treated as inactive.

Therefore:

```text
terminal execution
      ≠
agent immediately available
```

Instead:

```text
terminal execution
      ↓
terminal result acknowledged
      ↓
action becomes inactive
```

This prevents an agent from accepting new work while the outcome of its previous work remains unsynchronized.

---

# Authoritative State vs Local State

The two stores deliberately represent different perspectives.

```text
                  DISTRIBUTED AUTHORITY
                         │
                         ▼
                    ActionStore
                         │
                  Action.status
                         │
        PENDING → CLAIMED → RUNNING → TERMINAL


                    LOCAL AGENT
                         │
                         ▼
                 AgentActionStore
                         │
                   local_status
                         │
       CLAIMED → CONSUMED → RUNNING → TERMINAL
                                      │
                                      ▼
                              terminal_reported
```

For example, after an action is persisted by an agent, the embedded action may contain:

```python
{
    "status": "claimed"
}
```

while later the same local record may contain:

```python
{
    "local_status": "running"
}
```

This is expected.

The embedded action is not automatically rewritten to mirror every local execution transition.

Consumers of `AgentActionStore` should use the local record fields for local execution state rather than assuming that the embedded `action.status` always represents the latest local state.

---

# Terminal Synchronization

The local storage model is designed to preserve terminal outcomes across communication failures.

Consider:

```text
local action RUNNING
        ↓
executor finishes
        ↓
local_status = COMPLETED
terminal_reported = False
        ↓
terminal result sent remotely
        ↓
authoritative Action becomes COMPLETED
        ↓
response is lost
```

At this point the authoritative action may already be terminal, but the local agent has not received acknowledgement.

The local record therefore remains:

```text
local_status      = completed
terminal_reported = False
```

and `find_active()` continues to treat it as active.

The same terminal result can then be retried.

After acknowledgement:

```text
local_status      = completed
terminal_reported = True
```

and `find_active()` no longer returns that action.

This behavior supports durable terminal-state synchronization without allowing new work to silently replace an unacknowledged terminal action.

---

# Typical Storage Sequence

A simplified interaction between the two storage perspectives is:

```text
Action created
     │
     ▼
ActionStore.save()
     │
     ▼
PENDING
     │
     ▼
ActionStore.claim()
     │
     ▼
CLAIMED
     │
     ├──────────────► AgentActionStore.save()
     │                        │
     │                        ▼
     │                 local CLAIMED
     │                        │
     │                        ▼
     │                 mark_consumed()
     │                        │
     │                        ▼
     │                 local CONSUMED
     │
     ▼
ActionStore.mark_running()
     │
     ▼
RUNNING
     │
     └──────────────► mark_running_reported()
                              │
                              ▼
                       local RUNNING
                              │
                              ▼
                       mark_terminal()
                              │
                              ▼
                       local TERMINAL
                              │
     ┌────────────────────────┘
     ▼
ActionStore.mark_terminal()
     │
     ▼
authoritative TERMINAL
     │
     └──────────────► mark_terminal_reported()
                              │
                              ▼
                    local action inactive
```

The communication workflow layer coordinates these operations. The storage layer itself only provides the persistent state and transition rules.

---

# Package API

The supported package-level imports are:

```python
from framework.communication.storage import (
    ActionStore,
    AgentActionStore,
)
```

These classes form the public API of `framework.communication.storage`.

Internal path and JSON-writing helpers are implementation details and are not part of the public API.