# Communication Core

The `framework.communication.core` package defines the fundamental data models used by the distributed communication framework.

These models are **transport-independent**. They describe distributed work and agent capabilities without depending on TCP, sockets, filesystem storage, deployment addresses, or project-specific operations.

The package provides three public objects:

```python
from framework.communication.core import (
    Action,
    ActionStatus,
    Agent,
)
```

## Responsibility

The communication core defines:

- what a distributed action is;
- the lifecycle states an action can hold;
- how an agent is identified;
- which roles an agent can perform;
- JSON-serializable representations of actions and agents.

It does **not**:

- persist actions;
- claim actions;
- execute actions;
- communicate over TCP;
- poll for work;
- coordinate workflows;
- define project-specific operations.

Those responsibilities belong to other framework layers.

---

# ActionStatus

```python
class ActionStatus(str, Enum)
```

`ActionStatus` defines the lifecycle states available to a distributed `Action`.

## States

| Status | Value | Meaning |
|---|---|---|
| `PENDING` | `"pending"` | The action exists but has not been claimed. |
| `CLAIMED` | `"claimed"` | An agent has claimed responsibility for the action. |
| `RUNNING` | `"running"` | Execution of the action has started. |
| `COMPLETED` | `"completed"` | Execution finished successfully. |
| `FAILED` | `"failed"` | Execution terminated with a failure. |
| `CANCELLED` | `"cancelled"` | Execution was cancelled. |

The core model defines the available states but does not itself enforce transitions between them. Lifecycle transition rules are handled by higher communication layers.

A typical distributed lifecycle is:

```text
PENDING
   ↓
CLAIMED
   ↓
RUNNING
   ↓
COMPLETED
   or
FAILED
   or
CANCELLED
```

Because `ActionStatus` inherits from `str`, its values can be represented directly in JSON-compatible data.

Example:

```python
from framework.communication.core import ActionStatus

status = ActionStatus.RUNNING

print(status.value)
# running
```

---

# Action

```python
@dataclass
class Action
```

`Action` is the transport-independent description of a unit of work intended for a distributed agent.

An action identifies:

- **what** should be done;
- **which capability/role** should handle it;
- optional input data;
- its distributed lifecycle state;
- the agent that claimed it;
- optional framework or application metadata.

## Constructor

```python
Action(
    action: str,
    target: str,
    payload: dict = {},
    action_id: str = <generated UUID>,
    status: ActionStatus = ActionStatus.PENDING,
    claimed_by: str | None = None,
    metadata: dict = {},
)
```

Only `action` and `target` are required.

Example:

```python
from framework.communication.core import Action

action = Action(
    action="sense_timber",
    target="sensing",
)
```

A unique UUID string is generated automatically when `action_id` is not supplied.

---

## Fields

### `action`

```python
action: str
```

Identifies the operation requested by the action.

Example:

```python
"sense_timber"
```

The value is stripped of surrounding whitespace and normalized to lowercase.

It cannot be empty.

---

### `target`

```python
target: str
```

Identifies the capability or agent role required to handle the action.

Example:

```python
"sensing"
```

The value is stripped and normalized to lowercase.

The target is later compared against agent roles.

---

### `payload`

```python
payload: dict
```

Contains input data required by the operation.

Example:

```python
Action(
    action="process_entity",
    target="design",
    payload={
        "entity_id": "T-0001-WAR",
    },
)
```

The payload must be a dictionary.

The core does not interpret its contents.

---

### `action_id`

```python
action_id: str
```

Unique identifier for the action.

If no identifier is provided, a UUID is generated automatically.

Unlike `action` and `target`, the identifier is not converted to lowercase.

---

### `status`

```python
status: ActionStatus
```

Current distributed lifecycle state of the action.

The default is:

```python
ActionStatus.PENDING
```

A compatible string can also be supplied:

```python
Action(
    action="sense_timber",
    target="sensing",
    status="running",
)
```

It is converted internally to:

```python
ActionStatus.RUNNING
```

---

### `claimed_by`

```python
claimed_by: str | None
```

Identifies the agent that has claimed the action.

The default is:

```python
None
```

When present, the value is stripped and normalized to lowercase.

---

### `metadata`

```python
metadata: dict
```

Stores additional information associated with the action.

For example, orchestration layers can use metadata to associate an action with a larger orchestration without changing the generic action model.

The metadata must be a dictionary.

The communication core does not interpret its contents.

---

## `to_dict()`

```python
action.to_dict() -> dict
```

Returns a JSON-serializable representation of the action.

Example:

```python
action = Action(
    action="sense_timber",
    target="sensing",
)

data = action.to_dict()
```

The returned structure has the form:

```python
{
    "action_id": "...",
    "action": "sense_timber",
    "target": "sensing",
    "status": "pending",
    "claimed_by": None,
    "payload": {},
    "metadata": {},
}
```

`ActionStatus` is serialized using its string value.

---

## `from_dict()`

```python
Action.from_dict(data: dict) -> Action
```

Creates an `Action` from dictionary data.

Example:

```python
data = {
    "action_id": "action-001",
    "action": "sense_timber",
    "target": "sensing",
    "status": "pending",
    "claimed_by": None,
    "payload": {},
    "metadata": {},
}

action = Action.from_dict(data)
```

If `action_id` is absent, a new UUID is generated.

If `status` is absent, the action defaults to:

```python
ActionStatus.PENDING
```

Missing `payload` or `metadata` values default to empty dictionaries.

---

## Validation and normalization

During initialization:

```text
action       → required, stripped, lowercase
target       → required, stripped, lowercase
action_id    → required, stripped, case preserved
claimed_by   → stripped, lowercase when present
payload      → must be dict
metadata     → must be dict
status       → converted to ActionStatus when necessary
```

Invalid values raise `ValueError` or `TypeError`.

---

# Agent

```python
@dataclass
class Agent
```

`Agent` represents the transport-independent identity and capabilities of a distributed agent.

An agent describes **who the agent is** and **which roles it can perform**.

It does not represent the running process, TCP server, poller, executor, or local persistent state of that agent.

## Constructor

```python
Agent(
    agent_id: str,
    roles: list[str] = [],
    metadata: dict = {},
)
```

Example:

```python
from framework.communication.core import Agent

agent = Agent(
    agent_id="sensing_pc_01",
    roles=["sensing"],
)
```

---

## Fields

### `agent_id`

```python
agent_id: str
```

Persistent identifier of the agent.

Example:

```python
"sensing_pc_01"
```

The value is stripped of surrounding whitespace but its case is preserved.

It cannot be empty.

---

### `roles`

```python
roles: list[str]
```

Defines the capabilities provided by the agent.

Example:

```python
["sensing"]
```

An agent can provide multiple roles:

```python
Agent(
    agent_id="agent_01",
    roles=[
        "sensing",
        "design",
    ],
)
```

Roles are:

- stripped;
- normalized to lowercase;
- deduplicated while preserving their original order.

A single string is also accepted and normalized internally to a list.

---

### `metadata`

```python
metadata: dict
```

Optional additional information describing the agent.

Example:

```python
Agent(
    agent_id="sensing_pc_01",
    roles=["sensing"],
    metadata={
        "location": "workshop",
    },
)
```

The metadata must be a dictionary.

The core model does not interpret its contents.

---

## `has_role()`

```python
agent.has_role(role: str) -> bool
```

Returns `True` when the agent provides the requested role.

Example:

```python
agent = Agent(
    agent_id="sensing_pc_01",
    roles=["sensing"],
)

agent.has_role("sensing")
# True

agent.has_role("design")
# False
```

The requested role is normalized before comparison.

---

## `can_handle()`

```python
agent.can_handle(target: str) -> bool
```

Returns whether the agent can handle an action target.

Internally, this checks whether the target exists among the agent's roles.

Example:

```python
action = Action(
    action="sense_timber",
    target="sensing",
)

agent = Agent(
    agent_id="sensing_pc_01",
    roles=["sensing"],
)

agent.can_handle(action.target)
# True
```

This establishes the basic relationship:

```text
Action.target
     │
     ▼
Agent.roles
```

An agent is capable of handling an action when its roles contain the action's target.

The core only defines this capability check. It does not claim or execute the action.

---

## `to_dict()`

```python
agent.to_dict() -> dict
```

Returns a JSON-serializable representation of the agent.

Example output:

```python
{
    "agent_id": "sensing_pc_01",
    "roles": [
        "sensing",
    ],
    "metadata": {},
}
```

---

## `from_dict()`

```python
Agent.from_dict(data: dict) -> Agent
```

Creates an `Agent` from dictionary data.

Example:

```python
data = {
    "agent_id": "sensing_pc_01",
    "roles": ["sensing"],
    "metadata": {},
}

agent = Agent.from_dict(data)
```

Missing `roles` and `metadata` values default to empty collections.

---

## Validation and normalization

During initialization:

```text
agent_id    → required, stripped, case preserved
roles       → stripped, lowercase, unique
metadata    → must be dict
```

Invalid values raise `ValueError` or `TypeError`.

---

# Relationship Between Action and Agent

`Action` and `Agent` intentionally remain simple and independent of transport and persistence.

Their primary relationship is capability matching:

```text
Action
├── action = "sense_timber"
└── target = "sensing"
              │
              │ capability match
              ▼
Agent
├── agent_id = "sensing_pc_01"
└── roles = ["sensing"]
```

For example:

```python
from framework.communication.core import (
    Action,
    Agent,
)

action = Action(
    action="sense_timber",
    target="sensing",
)

agent = Agent(
    agent_id="sensing_pc_01",
    roles=["sensing"],
)

if agent.can_handle(action.target):
    print("Agent can handle this action.")
```

Higher framework layers build on these models to provide persistence, claiming, lifecycle synchronization, polling, transport, and distributed execution.

---

# Package API

The supported package-level imports are:

```python
from framework.communication.core import (
    Action,
    ActionStatus,
    Agent,
)
```

These objects form the public API of `framework.communication.core`.

Implementation helpers such as internal normalization methods are not part of the public API.