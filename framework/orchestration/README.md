# Orchestration Framework

The `framework.orchestration` package defines reusable tools for describing and progressing ordered workflows made of distributed `Action` objects.

Orchestration answers:

> **Which action should exist now, and which action should be released next?**

It is deliberately separate from distributed communication, agent lifecycle management, and application execution.

The public API is:

```python id="q61u9c"
from framework.orchestration import (
    OrchestrationStep,
    OrchestrationDefinition,
    Orchestrator,
    ActionDispatcher,
)
```

The package supports two related responsibilities:

```text id="n5wpgu"
DISTRIBUTED SEQUENCE
    │
    └── OrchestrationStep
        OrchestrationDefinition
        Orchestrator

LOCAL EXECUTION ROUTING
    │
    └── ActionDispatcher
```

---

# Purpose

A distributed application may consist of several operations that must happen in a defined order.

For example:

```text id="whr0za"
inspect
   │
   ▼
design
   │
   ▼
fabricate
```

Each operation may be executed by a different distributed agent.

The orchestration framework describes this sequence and releases the corresponding distributed actions one step at a time:

```text id="mujnnp"
OrchestrationDefinition
        │
        ▼
      step 0
        │
        ▼
Action PENDING
        │
        │ executed through communication framework
        ▼
Action COMPLETED
        │
        ▼
Orchestrator.advance()
        │
        ▼
      step 1
        │
        ▼
next Action PENDING
```

Only the currently released step becomes an actionable distributed `Action`.

Later steps remain definitions until the orchestration is advanced.

---

# Responsibility

The orchestration package provides:

- reusable orchestration step definitions;
- ordered sequential workflow definitions;
- creation of the first distributed action;
- release of successor actions;
- orchestration identity metadata;
- validation that actions belong to the expected orchestration;
- idempotent successor release;
- local routing of an `Action` to a registered execution handler.

It does **not**:

- claim distributed actions;
- poll agents;
- communicate over the network;
- mark actions as running;
- synchronize execution state;
- automatically observe action completion;
- automatically call `advance()`;
- execute application-specific operations itself;
- define project-specific orchestration definitions.

These responsibilities remain in the communication or application layers.

---

# Package Structure

```text id="agx0ze"
orchestration/
├── __init__.py
├── step.py
├── definition.py
├── orchestrator.py
└── action_dispatcher.py
```

The main relationship is:

```text id="gtrpr5"
OrchestrationStep
       │
       ▼
OrchestrationDefinition
       │
       ▼
Orchestrator
       │
       ▼
ActionStore
       │
       ▼
distributed communication
```

`ActionDispatcher` sits at a different boundary:

```text id="zw3rvi"
received Action
      │
      ▼
ActionDispatcher
      │
      ▼
registered local handler
      │
      ▼
application operation
```

---

# OrchestrationStep

```python id="mfn7xj"
@dataclass(frozen=True)
class OrchestrationStep
```

`OrchestrationStep` describes one step in an orchestration.

A step defines:

```text id="quq3zu"
step_id
    │
    └── identity of the orchestration step

action
    │
    └── Action.action to create

target
    │
    └── agent role eligible to execute it

payload
    │
    └── default Action payload
```

It contains no storage, communication, or execution behavior.

---

## Constructor

```python id="4kbz9m"
OrchestrationStep(
    step_id: str,
    action: str,
    target: str,
    payload: dict = {},
)
```

Example:

```python id="4e4mnr"
from framework.orchestration import (
    OrchestrationStep,
)

step = OrchestrationStep(
    step_id="inspect",
    action="inspect_material",
    target="sensing",
    payload={
        "source": "scan_001",
    },
)
```

`step_id`, `action`, and `target` are:

- required;
- stripped;
- normalized to lowercase.

The payload must be a dictionary.

---

## Public attributes

Because `OrchestrationStep` is a frozen dataclass, its public fields define the step after construction:

```python id="18gtw9"
step.step_id
step.action
step.target
step.payload
```

For example:

```python id="1dy50e"
print(step.step_id)
# inspect

print(step.action)
# inspect_material

print(step.target)
# sensing
```

The step object itself is immutable after initialization.

---

# OrchestrationDefinition

```python id="ft0czs"
class OrchestrationDefinition
```

`OrchestrationDefinition` defines an ordered sequence of `OrchestrationStep` objects.

It describes structure only.

It does not create actions or execute the orchestration.

Example structure:

```text id="2brj22"
OrchestrationDefinition
        │
        ├── [0] inspect
        ├── [1] design
        └── [2] fabricate
```

---

## Constructor

```python id="l7xdn7"
OrchestrationDefinition(
    name: str,
    steps: list[OrchestrationStep],
)
```

Example:

```python id="2pd2a2"
from framework.orchestration import (
    OrchestrationDefinition,
    OrchestrationStep,
)

definition = OrchestrationDefinition(
    name="material_process",
    steps=[
        OrchestrationStep(
            step_id="inspect",
            action="inspect_material",
            target="sensing",
        ),
        OrchestrationStep(
            step_id="design",
            action="generate_design",
            target="design",
        ),
        OrchestrationStep(
            step_id="fabricate",
            action="execute_fabrication",
            target="robot_control",
        ),
    ],
)
```

The definition name is stripped and normalized to lowercase.

The step collection must:

- be a list;
- contain at least one step;
- contain only `OrchestrationStep` objects;
- contain unique `step_id` values.

---

## Public attributes

### `name`

```python id="4rfn4k"
definition.name: str
```

Normalized orchestration definition name.

### `steps`

```python id="2lb5vq"
definition.steps: list[OrchestrationStep]
```

Ordered copy of the supplied step list.

The order defines the orchestration sequence.

---

## `get_step()`

```python id="4clm12"
definition.get_step(
    index: int,
) -> OrchestrationStep
```

Returns the step at the requested index.

Example:

```python id="3u6z37"
first_step = definition.get_step(0)
```

An invalid index raises `IndexError`.

A non-integer index raises `TypeError`.

Negative indexing is deliberately not supported.

---

## `get_next_step()`

```python id="cww2mr"
definition.get_next_step(
    index: int,
) -> OrchestrationStep | None
```

Returns the step after the supplied index.

Example:

```python id="3u4f09"
next_step = definition.get_next_step(0)
```

For:

```text id="p27pgm"
0 inspect
1 design
2 fabricate
```

calling:

```python id="shc6e3"
definition.get_next_step(0)
```

returns the `design` step.

Calling it for the final step:

```python id="pyw6xf"
definition.get_next_step(2)
```

returns:

```python id="ftprr1"
None
```

An invalid source index raises `IndexError`.

---

## `len()`

The number of steps can be obtained using:

```python id="71ogqx"
len(definition)
```

For a three-step orchestration:

```python id="icruxv"
len(definition) == 3
```

---

# Orchestrator

```python id="eb3wss"
class Orchestrator
```

`Orchestrator` releases distributed `Action` objects from an `OrchestrationDefinition`.

Its central responsibility is:

> **Decide which orchestration action becomes eligible next.**

It uses an authoritative `ActionStore` for persistence.

---

## Constructor

```python id="9qz9og"
Orchestrator(
    action_store: ActionStore,
)
```

Example:

```python id="l51h47"
from framework.communication.storage import (
    ActionStore,
)

from framework.orchestration import (
    Orchestrator,
)

action_store = ActionStore(
    root="runtime/actions",
)

orchestrator = Orchestrator(
    action_store=action_store,
)
```

---

## Public attributes

### `action_store`

```python id="x1u79p"
orchestrator.action_store: ActionStore
```

The authoritative store into which orchestration actions are released.

---

# Starting an Orchestration

## `start()`

```python id="d2zjm6"
orchestrator.start(
    definition: OrchestrationDefinition,
    payload: dict | None = None,
    metadata: dict | None = None,
) -> Action
```

Starts a new instance of an orchestration.

Important:

> `start()` creates and persists **only the first step**.

It does not create all orchestration actions in advance.

Example:

```python id="jzx33f"
first_action = orchestrator.start(
    definition=definition,
)
```

For:

```text id="ynft3l"
inspect
   ↓
design
   ↓
fabricate
```

the result is:

```text id="05m4wy"
inspect     → PENDING Action created
design      → not created
fabricate   → not created
```

The returned action begins with:

```python id="d94jfp"
ActionStatus.PENDING
```

and is immediately persisted in the `ActionStore`.

---

# Orchestration Identity

Every call to:

```python id="c1ywyj"
orchestrator.start(...)
```

creates a new orchestration instance with a generated UUID.

The generated action receives orchestration metadata:

```python id="6o19wv"
{
    "orchestration_id": "...",
    "orchestration_name": "...",
    "orchestration_step_id": "...",
    "orchestration_step_index": 0,
}
```

This metadata connects otherwise independent distributed `Action` objects into one orchestration instance.

For example:

```text id="yk2l6u"
Action A
orchestration_id = abc
step_index = 0

Action B
orchestration_id = abc
step_index = 1

Action C
orchestration_id = abc
step_index = 2
```

All three belong to the same orchestration instance.

Starting the same definition again creates a different `orchestration_id`.

---

# Payload Composition

Each `OrchestrationStep` can define a default payload:

```python id="i2z3qi"
OrchestrationStep(
    step_id="inspect",
    action="inspect_material",
    target="sensing",
    payload={
        "source": "scan_001",
    },
)
```

Additional payload can be supplied when starting or advancing:

```python id="khnryv"
action = orchestrator.start(
    definition=definition,
    payload={
        "request_id": "request_001",
    },
)
```

The resulting action payload combines both:

```python id="lyb8cb"
{
    "source": "scan_001",
    "request_id": "request_001",
}
```

The supplied runtime payload updates the step's default payload when the same key exists.

---

# Additional Metadata

Application metadata can also be supplied:

```python id="czos29"
action = orchestrator.start(
    definition=definition,
    metadata={
        "request_source": "operator",
    },
)
```

The orchestrator combines this with its required orchestration metadata.

Conceptually:

```text id="dhg2i5"
application metadata
        +
orchestration metadata
        │
        ▼
Action.metadata
```

The orchestrator-controlled fields identify the orchestration instance and step.

---

# Advancing an Orchestration

## `advance()`

```python id="uqfww2"
orchestrator.advance(
    definition: OrchestrationDefinition,
    completed_action: Action,
    payload: dict | None = None,
    metadata: dict | None = None,
) -> Action | None
```

Releases the next action after a completed orchestration action.

The previous action must already have:

```python id="ocmclv"
status == ActionStatus.COMPLETED
```

Example:

```python id="j1yocv"
next_action = orchestrator.advance(
    definition=definition,
    completed_action=completed_action,
)
```

The transition is:

```text id="1p6eas"
step 0 Action COMPLETED
        │
        ▼
Orchestrator.advance()
        │
        ▼
step 1 Action PENDING
```

The newly released action is persisted immediately in the authoritative `ActionStore`.

---

# Completion Is Required

Only `COMPLETED` actions advance an orchestration.

The following do not advance it:

```text id="d0ib89"
PENDING
CLAIMED
RUNNING
FAILED
CANCELLED
```

For example:

```python id="bupvmw"
orchestrator.advance(
    definition=definition,
    completed_action=running_action,
)
```

raises `RuntimeError`.

This means the current sequential orchestration model follows:

```text id="r3p22a"
successful completion
        │
        ▼
release next step
```

It does not currently define alternative branches for failure or cancellation.

---

# Final Step

When the completed action represents the final step:

```python id="evjs1v"
next_action = orchestrator.advance(
    definition=definition,
    completed_action=final_action,
)
```

returns:

```python id="1khftw"
None
```

No additional action is created.

Therefore:

```text id="utsp7u"
final action COMPLETED
        │
        ▼
advance()
        │
        ▼
None
        │
        ▼
orchestration finished
```

---

# Successor Relationship

Every non-initial action receives:

```python id="2q35s8"
metadata[
    "previous_action_id"
]
```

containing the ID of the completed action that released it.

Example:

```text id="t84pnp"
Action A
    │
    │ previous_action_id relationship
    ▼
Action B
    │
    ▼
Action C
```

More explicitly:

```text id="p5i7fd"
Action A
action_id = A

Action B
previous_action_id = A

Action C
previous_action_id = B
```

Together with `orchestration_id`, this provides a persistent relationship between sequential actions.

---

# Advancement Validation

Before releasing a successor, `Orchestrator.advance()` validates that the supplied action is consistent with the requested definition.

It checks:

```text id="j4dy7h"
completed_action.status
        │
        └── must be COMPLETED

orchestration_id
        │
        └── must exist

orchestration_name
        │
        └── must match definition.name

orchestration_step_index
        │
        └── must be a valid integer

orchestration_step_id
        │
        └── must match the definition
```

This prevents an unrelated completed action from advancing the wrong orchestration definition.

---

# Idempotent Advancement

A completed action may release at most one successor.

This is an important persistence rule.

Consider:

```text id="k9qz8v"
Action A COMPLETED
        │
        ▼
advance(A)
        │
        ▼
Action B created
```

If the same call is repeated:

```text id="ed60u2"
advance(A)
```

the orchestrator does **not** create another Action B.

Instead, it searches the `ActionStore` for an existing action whose:

```python id="xf1v6z"
metadata["previous_action_id"]
    == completed_action.action_id
```

If a valid successor already exists, that existing action is returned.

Therefore:

```text id="y7plqe"
first advance(A)
      │
      ▼
Action B

retry advance(A)
      │
      ▼
same Action B
```

not:

```text id="o84n7x"
Action B
Action B duplicate
```

---

# Retry Arguments Do Not Replace an Existing Successor

If the first call creates:

```python id="xv4dhm"
action_b = orchestrator.advance(
    definition=definition,
    completed_action=action_a,
    payload={
        "attempt": "first",
    },
)
```

and a retry later supplies:

```python id="16wobc"
orchestrator.advance(
    definition=definition,
    completed_action=action_a,
    payload={
        "attempt": "retry",
    },
    metadata={
        "retry": True,
    },
)
```

the already persisted successor is returned unchanged.

The retry arguments do not mutate the existing action.

This preserves the first authoritative successor that was released.

---

# Multiple Successor Protection

If persistent storage somehow contains more than one successor for the same completed action:

```text id="1b3xy9"
completed Action A
       │
       ├──► Action B
       └──► Action C
```

the orchestrator raises `RuntimeError`.

It does not silently choose one.

The sequential orchestration invariant is:

> One completed action can release at most one successor action.

---

# Orchestration Does Not Automatically Advance

`Orchestrator` does not monitor the `ActionStore`.

It does not run a background thread.

It does not automatically react when an action becomes `COMPLETED`.

A higher-level application must decide when to call:

```python id="7i9mpa"
orchestrator.advance(
    definition=definition,
    completed_action=completed_action,
)
```

The boundary is:

```text id="oxl59w"
Action becomes COMPLETED
        │
        ▼
higher-level application
detects / receives completion
        │
        ▼
calls Orchestrator.advance()
        │
        ▼
next Action released
```

This keeps orchestration policy separate from communication and runtime service behavior.

---

# Orchestration and Communication

The orchestration and communication frameworks share the authoritative `ActionStore`, but they use it for different purposes.

```text id="m1qjgx"
ORCHESTRATION
     │
     │ creates/releases Actions
     ▼
ActionStore
     ▲
     │
     │ claims and updates Actions
COMMUNICATION
```

Orchestration answers:

```text id="dd38v2"
What action should exist next?
```

Communication answers:

```text id="f3smw7"
Which agent can claim it?
Has execution started?
What was the execution result?
```

For example:

```text id="l1w2c0"
Orchestrator.start()
        │
        ▼
Action PENDING
        │
        ▼
communication framework
        │
        ├── claim
        ├── RUNNING
        └── COMPLETED
        │
        ▼
Orchestrator.advance()
        │
        ▼
next Action PENDING
```

Neither layer needs to take over the other's responsibility.

For distributed lifecycle details, see:

[`../communication/README.md`](../communication/README.md)

---

# Sequential Model

The current `Orchestrator` implements a sequential model:

```text id="6gztl2"
STEP 0
  │
  ▼
STEP 1
  │
  ▼
STEP 2
  │
  ▼
...
```

It does not currently provide:

- parallel branches;
- conditional branches;
- loops;
- dependency graphs;
- automatic retries;
- rollback logic;
- failure branches.

These behaviors can be introduced by higher-level application logic or future orchestration components without changing the responsibility of the existing sequential orchestrator.

---

# ActionDispatcher

```python id="ue00wp"
class ActionDispatcher
```

`ActionDispatcher` maps an `Action.action` name to a local callable.

It provides a small execution-routing boundary:

```text id="dm7fnc"
Action
   │
   │ action="inspect_material"
   ▼
ActionDispatcher
   │
   ▼
registered handler
   │
   ▼
local operation
```

It does not manage action lifecycle state.

It does not communicate with distributed services.

---

## Constructor

```python id="4wqrs2"
ActionDispatcher()
```

Example:

```python id="5b3j8a"
from framework.orchestration import (
    ActionDispatcher,
)

dispatcher = ActionDispatcher()
```

The registered handler mapping is maintained internally.

---

# Registering an Action Handler

## `register()`

```python id="fll7jc"
dispatcher.register(
    action: str,
    handler: Callable[[Action], Any],
) -> None
```

Registers one callable for an action name.

Example:

```python id="2byd80"
def handle_inspection(action):
    print(
        "Executing:",
        action.action,
    )

dispatcher.register(
    action="inspect_material",
    handler=handle_inspection,
)
```

Action names are stripped and normalized to lowercase.

The handler must be callable.

Only one handler may be registered for each action name.

Attempting to register another handler for the same action raises `ValueError`.

---

# Dispatching an Action

## `dispatch()`

```python id="jys0fw"
dispatcher.dispatch(
    action: Action,
) -> Any
```

Finds the registered handler using:

```python id="avc3s3"
action.action
```

and calls:

```python id="8fk0li"
handler(action)
```

The complete `Action` object is passed to the handler.

Example:

```python id="mr5gwq"
from framework.communication.core import Action

action = Action(
    action="inspect_material",
    target="sensing",
    payload={
        "equipment": "camera",
    },
)

result = dispatcher.dispatch(
    action
)
```

The dispatcher's return value is whatever the registered handler returns.

Therefore:

```text id="v44xf9"
handler returns X
       │
       ▼
dispatch() returns X
```

---

# Unknown Actions

If no handler is registered for:

```python id="k34b58"
action.action
```

`dispatch()` raises `KeyError`.

For example:

```text id="5nt2xz"
Action.action = "generate_design"

registered:
    "inspect_material"

result:
    KeyError
```

The dispatcher does not provide a fallback handler.

---

# ActionDispatcher Boundary

The dispatcher performs only:

```text id="m4yidn"
Action.action
      │
      ▼
handler lookup
      │
      ▼
handler(Action)
```

It does not:

- claim the action;
- mark it as running;
- mark it completed;
- persist it;
- communicate with another machine;
- retry execution;
- interpret orchestration metadata.

A typical integration is:

```text id="kbb4z3"
communication framework
        │
        │ executable Action
        ▼
ActionDispatcher
        │
        ▼
local handler
        │
        ▼
application operation
        │
        │ outcome
        ▼
communication framework
```

This keeps execution routing independent of distributed lifecycle management.

---

# Complete Example

Define the process:

```python id="c9bs92"
from framework.orchestration import (
    OrchestrationStep,
    OrchestrationDefinition,
)

definition = OrchestrationDefinition(
    name="material_process",
    steps=[
        OrchestrationStep(
            step_id="inspect",
            action="inspect_material",
            target="sensing",
        ),
        OrchestrationStep(
            step_id="design",
            action="generate_design",
            target="design",
        ),
        OrchestrationStep(
            step_id="fabricate",
            action="execute_fabrication",
            target="robot_control",
        ),
    ],
)
```

Create the authoritative store and orchestrator:

```python id="8ocgq7"
from framework.communication.storage import (
    ActionStore,
)

from framework.orchestration import (
    Orchestrator,
)

action_store = ActionStore(
    root="runtime/actions",
)

orchestrator = Orchestrator(
    action_store=action_store,
)
```

Start:

```python id="89mmqu"
action_1 = orchestrator.start(
    definition=definition,
)
```

At this point:

```text id="kic5qm"
inspect       PENDING
design        not created
fabricate     not created
```

The communication framework can now claim and execute `action_1`.

After it becomes `COMPLETED`:

```python id="c7ch6u"
completed_1 = action_store.load(
    action_1.action_id
)

action_2 = orchestrator.advance(
    definition=definition,
    completed_action=completed_1,
)
```

Now:

```text id="f86mkf"
inspect       COMPLETED
design        PENDING
fabricate     not created
```

After `action_2` completes:

```python id="wzcs9j"
completed_2 = action_store.load(
    action_2.action_id
)

action_3 = orchestrator.advance(
    definition=definition,
    completed_action=completed_2,
)
```

Finally, after `action_3` completes:

```python id="1rfwdi"
completed_3 = action_store.load(
    action_3.action_id
)

next_action = orchestrator.advance(
    definition=definition,
    completed_action=completed_3,
)

assert next_action is None
```

The orchestration is complete.

---

# Design Principle

The orchestration framework intentionally separates four questions:

```text id="u18vgf"
1. What is the process?
       │
       └── OrchestrationDefinition

2. What work becomes available next?
       │
       └── Orchestrator

3. How is that work distributed and synchronized?
       │
       └── communication framework

4. Which local function executes an action?
       │
       └── ActionDispatcher
```

This separation allows process definitions, distributed communication, and execution technologies to evolve independently.

---

# Public API

The supported package-level imports are:

```python id="89jmgl"
from framework.orchestration import (
    OrchestrationStep,
    OrchestrationDefinition,
    Orchestrator,
    ActionDispatcher,
)
```

| Object | Purpose |
|---|---|
| `OrchestrationStep` | Describe one step: action, target role, identity, and default payload. |
| `OrchestrationDefinition` | Define an ordered sequence of unique orchestration steps. |
| `Orchestrator` | Start an orchestration and release successor actions after completion. |
| `ActionDispatcher` | Route an `Action` to a registered local execution handler. |

Private helper methods such as successor lookup, action creation, action-name normalization, and internal handler storage are implementation details and are not part of the public API.

---

# Related Documentation

For the distributed action model, agents, persistence, TCP communication, polling, consumption, and lifecycle synchronization, see:

[`../communication/README.md`](../communication/README.md)

In particular:

- [`../communication/core/README.md`](../communication/core/README.md) — `Action`, `ActionStatus`, and `Agent`.
- [`../communication/storage/README.md`](../communication/storage/README.md) — authoritative `ActionStore` and agent-local persistence.
- [`../communication/workflow/README.md`](../communication/workflow/README.md) — claiming, polling, consumption, and lifecycle synchronization.

The orchestration package should be understood as the layer that **releases work**, while the communication package is the layer that **distributes and synchronizes that work**.