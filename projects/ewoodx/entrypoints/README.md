# eWoodX Entrypoints

The `projects.ewoodx.entrypoints` package defines application-level entrypoints for starting and coordinating eWoodX processes.

Entrypoints sit between the runtime environment and the concrete project operations. They determine how an operation is started, resolve the context required by that operation, and connect different execution modes to the same underlying project behavior.

The current sensing implementation provides **two distinct entry paths**:

1. **Direct sensing entrypoint** — runs the sensing process directly without requiring the distributed agent system.
2. **Distributed sensing agent entrypoint** — starts sensing through the Master/Sensing Agent distributed workflow and executes the same underlying sensing entrypoint after the distributed action is claimed.

This distinction is intentional.

```text
DIRECT EXECUTION                    DISTRIBUTED EXECUTION

sensing_entrypoint.py              sensing_agent_entrypoint.py
        │                                   │
        │                                   ▼
        │                            Sensing Agent
        │                                   │
        │                            distributed action
        │                                   │
        │                                   ▼
        └──────────────────────► EWoodXSensingEntrypoint
                                            │
                                            ▼
                                     sensing operation
```

The entrypoints package is under **continuous development**. The current implementation primarily establishes the sensing execution paths and is expected to expand as additional project workflows are developed.

---

# Package Structure

```text
projects/ewoodx/entrypoints/
├── __init__.py
├── sensing_entrypoint.py
└── sensing_agent_entrypoint.py
```

The responsibilities are:

| Module | Responsibility |
|---|---|
| `sensing_entrypoint.py` | Core/direct sensing entrypoint. Resolves workspace, sensing entry, equipment, entity persistence, and starts the selected sensing operation. |
| `sensing_agent_entrypoint.py` | Distributed sensing executor. Starts a sensing orchestration through the local Sensing Agent, waits for the distributed action, consumes it, dispatches it, and reports its terminal result. |
| `__init__.py` | Marks the package; currently does not re-export a consolidated public API. |

---

# Architectural Role

Entrypoints coordinate **how project operations are started**.

They do not normally implement the sensing, design, or fabrication algorithm itself.

Conceptually:

```text
Execution Context
       │
       ▼
   ENTRYPOINT
       │
       ├── resolve context
       ├── connect runtime components
       └── choose operation
               │
               ▼
           OPERATION
               │
               ▼
        actual project task
```

For sensing:

```text
EWoodXSensingEntrypoint
        │
        ├── workspace
        ├── sensing entry
        ├── EntityManager
        ├── equipment
        └── sensing operation
```

The concrete Timber sensing logic remains in:

```text
projects/ewoodx/operations/
```

---

# Package Public API

The current:

```text
projects/ewoodx/entrypoints/__init__.py
```

does not re-export entrypoint classes or functions.

Therefore, the package currently has **no consolidated package-level public API** through `entrypoints.__all__`.

Components are imported directly from their modules when required.

For example:

```python
from projects.ewoodx.entrypoints.sensing_entrypoint import (
    EWoodXSensingEntrypoint,
)
```

The distributed sensing entrypoint imports and reuses this same class.

---

# Two Sensing Entry Paths

The current architecture deliberately supports two ways of starting sensing.

```text
                         SENSING
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      DIRECT ENTRYPOINT           DISTRIBUTED ENTRYPOINT
              │                           │
              │                    Master / Agent
              │                           │
              └─────────────┬─────────────┘
                            ▼
                 EWoodXSensingEntrypoint
                            │
                            ▼
                    sensing operation
```

The two paths differ in **execution coordination**, not in the underlying sensing implementation.

---

# Direct Sensing Entrypoint

The direct path uses:

```text
sensing_entrypoint.py
```

directly.

Conceptually:

```text
User
 │
 ▼
sensing_entrypoint.py
 │
 ▼
EWoodXSensingEntrypoint
 │
 ├── resolve workspace
 ├── resolve sensing entry
 ├── resolve equipment
 └── create EntityManager
 │
 ▼
Timber sensing operation
```

This mode does not require:

```text
Master Agent
Sensing Agent
distributed Action
AgentPoller
distributed lifecycle synchronization
```

It is therefore useful when sensing should be executed directly on the local machine.

---

# Distributed Sensing Entrypoint

The distributed path uses:

```text
sensing_agent_entrypoint.py
```

together with the running distributed agent system.

Conceptually:

```text
User
 │
 ▼
sensing_agent_entrypoint.py
 │
 ▼
Sensing Agent local API
 │
 ▼
Master
 │
 ▼
start sensing orchestration
 │
 ▼
sense_timber Action
 │
 ▼
Sensing Agent Poller
 │
 ▼
claim Action
 │
 ▼
sensing_agent_entrypoint.py
 │
 ▼
consume Action
 │
 ▼
EWoodXSensingEntrypoint
 │
 ▼
Timber sensing operation
 │
 ▼
report terminal result
```

This path participates in the complete distributed action lifecycle.

---

# Shared Sensing Core

The most important relationship between the two entry paths is:

```text
Direct
  │
  ▼
EWoodXSensingEntrypoint
```

and:

```text
Distributed
     │
     ▼
distributed lifecycle
     │
     ▼
EWoodXSensingEntrypoint
```

The distributed entrypoint does **not** contain a second implementation of the Timber sensing workflow.

Instead, it eventually executes:

```python
entrypoint = EWoodXSensingEntrypoint()

entrypoint.run()
```

This keeps sensing behavior consistent between direct and distributed execution.

---

# `EWoodXSensingEntrypoint`

Defined in:

```text
sensing_entrypoint.py
```

Primary class:

```python
EWoodXSensingEntrypoint
```

Constructor:

```python
EWoodXSensingEntrypoint(
    workspace: WorkspacePaths | None = None,
    entry: EntryPaths | None = None,
    equipment: str | None = None,
)
```

The entrypoint accepts optional runtime context.

The current configurable context is:

```text
workspace
entry
equipment
```

If context is supplied programmatically, it is reused.

If context is missing, the entrypoint resolves it interactively.

---

# Programmatic and Interactive Context

The class is designed to support both:

```text
interactive/manual execution
```

and:

```text
programmatic execution
```

For example:

```python
entrypoint = EWoodXSensingEntrypoint()

entrypoint.run()
```

causes missing context to be resolved interactively.

Alternatively:

```python
entrypoint = EWoodXSensingEntrypoint(
    workspace=workspace,
    entry=entry,
    equipment="webcam",
)

entrypoint.run()
```

uses the supplied context directly.

This allows the same entrypoint to remain useful as higher-level orchestration evolves.

---

# Constructor Validation

The constructor validates supplied context.

If `workspace` is supplied, it must be:

```python
WorkspacePaths
```

If `entry` is supplied, it must be:

```python
EntryPaths
```

An entry cannot be supplied without its workspace.

Conceptually:

```text
entry supplied?
     │
     ├── NO ──► valid
     │
     └── YES
          │
          ▼
    workspace supplied?
        │       │
       YES      NO
        │       │
      valid    error
```

This prevents an entry from being used without its required workspace context.

---

# Sensing Entrypoint Workflow

The main public method is:

```python
run() -> None
```

The current sequence is:

```text
resolve workspace
       │
       ▼
resolve sensing entry
       │
       ▼
create EntityManager
       │
       ▼
resolve equipment
       │
       ▼
construct equipment-specific operation
       │
       ▼
operation.run()
```

Each missing piece of context is resolved only when necessary.

---

# Workspace Resolution

The public method:

```python
resolve_workspace() -> WorkspacePaths
```

provides the interactive workspace selection.

The current menu supports:

```text
[1] Use last workspace
[2] Open workspace by name
[3] Create new workspace
[4] Exit
```

Conceptually:

```text
Workspace
   │
   ├── continue last
   ├── open named workspace
   ├── create workspace
   └── exit
```

---

# Use Last Workspace

The first option calls:

```python
load_workspace(
    project_root=EWOODX_REPOSITORY_ROOT,
)
```

without explicitly supplying a workspace name.

The generic workspace framework resolves the last workspace according to its existing behavior.

If no appropriate workspace can be loaded, the error is shown and the selection loop continues.

---

# Open Workspace by Name

The second option asks for:

```text
Workspace name
```

and loads it through:

```python
load_workspace(
    project_root=EWOODX_REPOSITORY_ROOT,
    workspace_name=workspace_name,
)
```

An empty workspace name is rejected.

If the named workspace cannot be found, the error is reported and the user can choose again.

---

# Create New Workspace

The third option asks for a new workspace name.

The expected location is:

```text
<repository>/
└── workspaces/
    └── <workspace_name>/
```

If the path already exists, the entrypoint does not silently reuse it.

Instead, it instructs the user to open the existing workspace through the corresponding menu option.

A new workspace is created through:

```python
init_workspace(
    project_root=EWOODX_REPOSITORY_ROOT,
    workspace_name=workspace_name,
    layout=EWOODX_WORKSPACE_LAYOUT,
)
```

The actual workspace mechanism remains part of:

```text
framework.workspace
```

while the selected layout comes from:

```text
projects.ewoodx.config
```

---

# Workspace Exit

Selecting:

```text
[4] Exit
```

raises:

```python
SystemExit(0)
```

In direct execution, this terminates the sensing process normally.

In distributed execution, this same `SystemExit` is intercepted by the distributed sensing entrypoint and translated into:

```text
CANCELLED
```

for the active distributed action.

This is an important example of how the same sensing entrypoint behaves correctly in both execution modes.

---

# Sensing Entry Resolution

The public method:

```python
resolve_entry(
    workspace: WorkspacePaths,
) -> EntryPaths
```

resolves the persistent sensing entry used by the operation.

It first creates:

```python
DomainManager(
    workspace=workspace,
)
```

and ensures the configured sensing domain:

```python
SENSING_DOMAIN
```

exists.

Conceptually:

```text
Workspace
    │
    ▼
Sensing Domain
    │
    ▼
Sensing Entry
```

---

# Entry Manager

Once the sensing domain exists, the entrypoint creates:

```python
EntryManager(
    domain=sensing_domain,
)
```

This generic framework component manages entries under the sensing domain.

The project entrypoint then creates:

```python
EWoodXEntryAllocator(
    entry_manager=entry_manager,
)
```

to apply the eWoodX-specific entry naming/allocation convention.

---

# `EWoodXEntryAllocator`

The current sensing entrypoint uses the project operation:

```python
EWoodXEntryAllocator
```

from:

```text
projects.ewoodx.operations.entry_allocator
```

The distinction is:

```text
EntryManager
    │
    └── generic entry persistence/management

EWoodXEntryAllocator
    │
    └── eWoodX-specific entry allocation convention
```

This keeps project naming behavior outside the generic workspace framework.

---

# Sensing Entry Menu

The current entry menu supports:

```text
[1] Continue latest entry
[2] Select existing entry
[3] Create new entry
[4] Exit
```

If no managed sensing entries currently exist, the latest-entry option reports that none are available.

---

# Continue Latest Entry

The entrypoint obtains the latest project-managed entry through:

```python
entry_allocator.latest_entry()
```

If one exists, it is presented as:

```text
Continue latest entry: <entry_name>
```

and can be reused for the new sensing process.

This allows multiple sensing operations to continue within the same persistent entry when desired.

---

# Select Existing Entry

The entrypoint obtains existing sensing entries through:

```python
entry_manager.list_entries()
```

and presents them as an indexed interactive list.

The selected:

```python
EntryPaths
```

is then used as the persistence context for the sensing operation.

---

# Create New Entry

A new project entry name is allocated through:

```python
entry_allocator.allocate()
```

and created through:

```python
entry_manager.ensure_entry(
    entry_name
)
```

Conceptually:

```text
EWoodXEntryAllocator
        │
        ▼
project entry name
        │
        ▼
EntryManager
        │
        ▼
persistent sensing entry
```

The new entry is returned immediately as the active sensing entry.

---

# Entry Exit

Selecting:

```text
[4] Exit
```

during entry selection raises:

```python
SystemExit(0)
```

As with workspace exit:

```text
Direct execution
      │
      └── exits process

Distributed execution
      │
      └── becomes CANCELLED action
```

because the distributed wrapper owns the distributed execution outcome.

---

# Equipment Resolution

The public method:

```python
resolve_equipment() -> str
```

provides the current interactive equipment selection.

The menu is:

```text
[1] Arducam
[2] Webcam
[3] Exit
```

The current returned equipment identifiers are:

```text
arducam
webcam
```

These identifiers are project-side execution choices.

---

# Equipment Selection and Operations

After equipment resolution, `run()` selects the corresponding operation.

For:

```text
arducam
```

it creates:

```python
EWoodXTimberSegmentationArducam(
    entity_manager=entity_manager
)
```

For:

```text
webcam
```

it creates:

```python
EWoodXTimberSegmentationAngetube(
    entity_manager=entity_manager
)
```

The mapping is therefore:

```text
equipment
    │
    ├── arducam
    │      │
    │      ▼
    │   EWoodXTimberSegmentationArducam
    │
    └── webcam
           │
           ▼
        EWoodXTimberSegmentationAngetube
```

An unknown equipment identifier raises:

```python
ValueError
```

rather than silently selecting a default.

---

# Entity Persistence Context

Once workspace and entry are resolved, the sensing entrypoint creates:

```python
EntityManager(
    workspace=self.workspace,
    entry=self.entry,
    index_schema=TIMBER_ENTITY_INDEX,
)
```

This provides the selected sensing operation with its persistent entity context.

Conceptually:

```text
Workspace
    │
    ▼
Sensing Entry
    │
    ▼
EntityManager
    │
    ▼
Timber Sensing Operation
    │
    ▼
Persistent Timber Entity
```

The entrypoint creates the persistence context.

The operation creates and populates the actual Timber entities.

---

# Direct Execution

The module provides:

```python
main()
```

which creates:

```python
EWoodXSensingEntrypoint()
```

and calls:

```python
entrypoint.run()
```

The direct sensing entrypoint can therefore be started with:

```bash
python projects/ewoodx/entrypoints/sensing_entrypoint.py
```

This execution path is:

```text
Python Process
      │
      ▼
EWoodXSensingEntrypoint
      │
      ▼
interactive context resolution
      │
      ▼
sensing operation
```

No distributed Master or Sensing Agent is required for this path.

---

# Distributed Sensing Agent Entrypoint

Defined in:

```text
sensing_agent_entrypoint.py
```

This module provides the second sensing execution mode.

Unlike the direct entrypoint, it participates in the distributed agent lifecycle.

Its main responsibilities are:

```text
connect to local Sensing Agent
start sensing orchestration
wait for the action to be claimed
consume the local action
dispatch the action
run the shared sensing entrypoint
report terminal status
```

---

# Distributed Entrypoint Prerequisites

The distributed sensing entrypoint assumes that the distributed runtime is already available.

Conceptually:

```text
Master Agent       running
     ▲
     │
Sensing Agent      running
     ▲
     │
Distributed
Sensing Entrypoint
```

The entrypoint itself does not start the Master Agent or Sensing Agent processes.

It communicates with the already-running Sensing Agent local API.

---

# Local Agent Connection

The distributed entrypoint creates:

```python
TCPClient(
    host=SENSING_AGENT_HOST,
    port=SENSING_AGENT_PORT,
)
```

The current configuration points to the local Sensing Agent API.

Conceptually:

```text
sensing_agent_entrypoint.py
          │
          │ local TCP
          ▼
     Sensing Agent
          │
          │ distributed TCP
          ▼
        Master
```

The executor therefore does not need its own direct workflow implementation.

---

# Action Dispatcher

The distributed entrypoint creates:

```python
ActionDispatcher()
```

and registers:

```python
dispatcher.register(
    action="sense_timber",
    handler=run_sense_timber,
)
```

The mapping is:

```text
Action:
sense_timber
     │
     ▼
run_sense_timber(...)
     │
     ▼
EWoodXSensingEntrypoint
```

The generic dispatcher only maps the action name to the project execution handler.

It does not own communication, persistence, or lifecycle state.

---

# `run_sense_timber()`

The project action handler is:

```python
run_sense_timber(
    action: Action,
) -> None
```

It receives the complete distributed:

```python
Action
```

and reports basic action information to the terminal.

It then creates:

```python
EWoodXSensingEntrypoint()
```

and calls:

```python
entrypoint.run()
```

This is the point where the distributed path converges with the direct sensing path.

---

# Starting the Distributed Sensing Workflow

The distributed entrypoint first sends:

```json
{
    "command": "start_orchestration",
    "orchestration": "sensing"
}
```

to the local Sensing Agent.

The request path is:

```text
sensing_agent_entrypoint.py
        │
        ▼
Sensing Agent local API
        │
        ▼
EWoodXAgentHandler
        │
        ▼
Master
        │
        ▼
EWoodXMasterHandler
        │
        ▼
Orchestrator
        │
        ▼
SENSING_ORCHESTRATION
        │
        ▼
sense_timber Action
```

The authoritative action is created on the Master.

---

# Created Action Identity

After starting the orchestration, the distributed entrypoint reads:

```text
action_id
```

from the returned action.

This ID is retained so the entrypoint can later verify that the action consumed from the Sensing Agent is the same action that was created for this sensing request.

Conceptually:

```text
start orchestration
      │
      ▼
created action ID
      │
      ▼
wait for local action
      │
      ▼
consumed action ID
      │
      ▼
compare
```

A mismatch raises:

```python
RuntimeError
```

rather than executing a different action.

---

# Waiting for Agent Claim

Creating the action on the Master and having it available locally are separate events.

The sequence is:

```text
Master creates action
       │
       ▼
PENDING
       │
       ▼
AgentPoller sees action
       │
       ▼
CLAIMED
       │
       ▼
persisted locally
```

The distributed entrypoint therefore waits for the Sensing Agent to claim the newly created action.

---

# Action Wait Configuration

The current module defines:

```python
SENSING_ACTION_WAIT_INTERVAL = 0.25
SENSING_ACTION_WAIT_TIMEOUT = 10.0
```

The values are expressed in seconds.

The entrypoint repeatedly sends:

```json
{
    "command": "consume_action"
}
```

until:

```json
{
    "trigger": true
}
```

is returned or the timeout is reached.

---

# Why Consume Is Retried

Immediately after orchestration creation, the Sensing Agent poller may not yet have completed:

```text
poll
  ↓
claim
  ↓
local persistence
```

The executor therefore cannot assume that the action is already locally available.

The retry loop bridges this short asynchronous interval:

```text
start orchestration
       │
       ▼
action created
       │
       ▼
consume_action
       │
       ├── not ready
       │       │
       │       ▼
       │      wait
       │       │
       │       └── retry
       │
       └── trigger = true
               │
               ▼
             execute
```

If no action becomes available before the configured deadline, the entrypoint raises:

```python
TimeoutError
```

---

# Consuming the Action

When:

```text
consume_action
```

succeeds, the generic agent workflow performs the transition from locally claimed work into execution.

Conceptually:

```text
CLAIMED
   │
   ▼
local consume
   │
   ▼
report running
   │
   ▼
RUNNING
```

The distributed entrypoint receives the resulting action data and reconstructs:

```python
Action.from_dict(
    action_data
)
```

before dispatch.

---

# Action Identity Validation

Before execution, the entrypoint checks:

```python
action.action_id == action_id
```

where:

```text
action_id
```

is the action created by the orchestration request.

This ensures:

```text
requested action
       =
consumed action
```

If the Sensing Agent returns another action, execution stops with an error.

---

# Distributed Execution

Once the correct action has been consumed, the entrypoint calls:

```python
dispatcher.dispatch(
    action
)
```

The registered action handler then executes:

```text
run_sense_timber
        │
        ▼
EWoodXSensingEntrypoint
        │
        ▼
selected Timber sensing operation
```

The actual sensing implementation remains independent of the distributed lifecycle.

---

# Successful Completion

If the dispatched sensing operation returns normally, the distributed entrypoint sends:

```json
{
    "command": "mark_terminal",
    "action_status": "completed"
}
```

to the Sensing Agent.

Conceptually:

```text
operation returns normally
        │
        ▼
mark_terminal
        │
        ▼
COMPLETED
```

If the terminal update is rejected, the entrypoint raises an error rather than assuming synchronization succeeded.

---

# Cancellation

The shared sensing entrypoint uses:

```python
SystemExit(0)
```

when the user explicitly chooses an Exit option during interactive context selection.

The distributed wrapper catches:

```python
SystemExit
```

and reports:

```json
{
    "command": "mark_terminal",
    "action_status": "cancelled"
}
```

The resulting distributed outcome is:

```text
CANCELLED
```

Conceptually:

```text
User selects Exit
       │
       ▼
EWoodXSensingEntrypoint
       │
       ▼
SystemExit
       │
       ▼
distributed wrapper catches it
       │
       ▼
mark_terminal("cancelled")
```

This preserves the distinction between:

```text
user cancellation
```

and:

```text
execution failure
```

---

# Failure

If the sensing operation raises another exception, the distributed wrapper sends:

```json
{
    "command": "mark_terminal",
    "action_status": "failed"
}
```

and then re-raises the original execution error.

Conceptually:

```text
operation exception
       │
       ▼
mark FAILED
       │
       ▼
re-raise original error
```

If reporting the terminal failure itself fails, the response is printed before the original execution error is re-raised.

---

# Terminal State Ownership

The distributed entrypoint is the execution boundary around the sensing operation.

It therefore determines whether the execution resulted in:

```text
COMPLETED
FAILED
CANCELLED
```

This follows the framework principle:

> **Status ownership follows execution ownership.**

The orchestration layer creates the work.

The agent distributes and persists the work.

The executor runs the operation and determines its outcome.

---

# Direct vs Distributed Lifecycle

The two sensing entry paths can be compared as follows:

| Responsibility | Direct Entrypoint | Distributed Agent Entrypoint |
|---|---|---|
| Resolve workspace | Yes | Through shared sensing entrypoint |
| Resolve sensing entry | Yes | Through shared sensing entrypoint |
| Resolve equipment | Yes | Through shared sensing entrypoint |
| Create `EntityManager` | Yes | Through shared sensing entrypoint |
| Execute sensing operation | Yes | Through shared sensing entrypoint |
| Require Master | No | Yes |
| Require Sensing Agent | No | Yes |
| Create distributed action | No | Requests Master orchestration |
| Wait for agent claim | No | Yes |
| Consume distributed action | No | Yes |
| Dispatch action | No | Yes |
| Report `COMPLETED` | No | Yes |
| Report `FAILED` | No | Yes |
| Report `CANCELLED` | No | Yes |

The sensing functionality is shared.

The execution coordination is different.

---

# Direct Execution Flow

The complete direct path is:

```text
USER
 │
 ▼
sensing_entrypoint.py
 │
 ▼
EWoodXSensingEntrypoint
 │
 ├── resolve workspace
 │
 ├── resolve sensing entry
 │
 ├── create EntityManager
 │
 └── resolve equipment
 │
 ▼
EWoodXTimberSegmentationArducam
              OR
EWoodXTimberSegmentationAngetube
 │
 ▼
sensing
 │
 ▼
persistent Timber entities
```

This is the shortest path to the sensing operation.

---

# Distributed Execution Flow

The complete distributed path is:

```text
USER
 │
 ▼
sensing_agent_entrypoint.py
 │
 │ local TCP
 ▼
SENSING AGENT
 │
 │ start_orchestration
 ▼
MASTER
 │
 ▼
Orchestrator
 │
 ▼
sense_timber
PENDING
 │
 ▼
Sensing Agent Poller
 │
 ▼
CLAIMED
 │
 ▼
sensing_agent_entrypoint.py
 │
 ▼
consume_action
 │
 ▼
RUNNING
 │
 ▼
ActionDispatcher
 │
 ▼
run_sense_timber
 │
 ▼
EWoodXSensingEntrypoint
 │
 ├── workspace
 ├── sensing entry
 ├── EntityManager
 └── equipment
 │
 ▼
Timber Sensing Operation
 │
 ▼
COMPLETED / FAILED / CANCELLED
 │
 ▼
SENSING AGENT
 │
 ▼
MASTER
```

This path adds distributed coordination around the same sensing implementation.

---

# Why Both Entrypoints Exist

The two entrypoints serve different operational needs.

The direct entrypoint provides:

```text
simple local execution
rapid development/testing
manual sensing
operation without distributed infrastructure
```

The distributed entrypoint provides:

```text
Master-controlled workflow creation
agent-based execution
durable local action state
distributed status synchronization
future multi-machine deployment
```

Keeping both paths avoids forcing the distributed system onto every sensing use case while still allowing the same sensing capability to participate in distributed workflows.

---

# Shared Behavior, Different Coordination

The intended architecture is:

```text
                 SENSING CAPABILITY
                         │
                         ▼
              EWoodXSensingEntrypoint
                         ▲
                         │
             ┌───────────┴───────────┐
             │                       │
             │                       │
       DIRECT MODE             DISTRIBUTED MODE
             │                       │
       local execution         action lifecycle
                                     │
                               Master + Agent
```

This prevents the project from maintaining:

```text
one sensing implementation for local use
        +
another sensing implementation for distributed use
```

Instead, only the execution boundary changes.

---

# Relationship with Agents

The distributed entrypoint is an **executor/client of the Sensing Agent**, not the Sensing Agent itself.

```text
sensing_agent.py
      │
      └── long-running agent runtime

sensing_agent_entrypoint.py
      │
      └── starts and executes one sensing request
```

This distinction is important.

The agent remains alive across individual sensing executions.

The distributed entrypoint is associated with one requested sensing execution.

---

# Relationship with Orchestration

The distributed entrypoint does not create an `Action` directly.

Instead, it requests:

```text
start_orchestration("sensing")
```

and the Master uses:

```text
SENSING_ORCHESTRATION
```

to create the authoritative action.

The distinction is:

```text
ENTRYPOINT
    │
    └── requests work

ORCHESTRATION
    │
    └── creates/releases authoritative work
```

This preserves Master-side workflow authority.

---

# Relationship with Operations

Entrypoints coordinate operations but do not implement their algorithms.

For example:

```text
EWoodXSensingEntrypoint
       │
       └── selects
             │
             ▼
EWoodXTimberSegmentationAngetube
```

The operation owns:

```text
camera acquisition
Timber segmentation
measurement
visualization
entity creation
artifact persistence
```

The entrypoint owns:

```text
runtime context
operation selection
operation startup
```

---

# Relationship with Workspace

The direct/shared sensing entrypoint uses the generic workspace framework to resolve:

```text
Workspace
Domain
Entry
EntityManager
```

The current hierarchy for sensing execution is:

```text
Workspace
    │
    ▼
sensing Domain
    │
    ▼
Entry
    │
    ▼
EntityManager
    │
    ▼
Timber entities
```

The entrypoint establishes this context before starting the operation.

---

# Relationship with Configuration

The sensing entrypoints consume project configuration including:

```text
EWOODX_REPOSITORY_ROOT
EWOODX_WORKSPACE_LAYOUT
SENSING_DOMAIN
TIMBER_ENTITY_INDEX

SENSING_AGENT_HOST
SENSING_AGENT_PORT
```

The entrypoints therefore do not hard-code project workspace or agent deployment details that are already established in:

```text
projects.ewoodx.config
```

---

# Relationship with the Framework

The entrypoints compose several generic framework capabilities.

The direct sensing entrypoint uses:

```text
framework.workspace
    │
    ├── WorkspacePaths
    ├── EntryPaths
    ├── DomainManager
    ├── EntryManager
    ├── EntityManager
    ├── init_workspace
    └── load_workspace
```

The distributed sensing entrypoint additionally uses:

```text
framework.communication
    │
    ├── Action
    └── TCPClient

framework.orchestration
    │
    └── ActionDispatcher
```

The project entrypoints combine these reusable mechanisms without moving eWoodX-specific workflow into the framework.

---

# Current Responsibility Matrix

| Responsibility | Owner |
|---|---|
| Generic workspace persistence | `framework.workspace` |
| eWoodX workspace layout | `projects.ewoodx.config` |
| eWoodX entry naming/allocation | `EWoodXEntryAllocator` |
| Workspace selection UI | `EWoodXSensingEntrypoint` |
| Sensing entry selection UI | `EWoodXSensingEntrypoint` |
| Equipment selection UI | `EWoodXSensingEntrypoint` |
| `EntityManager` construction | `EWoodXSensingEntrypoint` |
| Timber sensing algorithm | `projects.ewoodx.operations` |
| Master distributed state | Master Agent |
| Agent-local distributed state | Sensing Agent |
| Sensing orchestration definition | `projects.ewoodx.orchestration` |
| Request one distributed sensing run | `sensing_agent_entrypoint.py` |
| Action-to-handler dispatch | `ActionDispatcher` |
| Distributed sensing outcome | `sensing_agent_entrypoint.py` |
| Actual sensing behavior | `EWoodXSensingEntrypoint` + selected operation |

---

# Entrypoint Design Principle

The current entrypoint architecture follows a simple principle:

```text
Entrypoints coordinate.
Operations execute.
Agents communicate.
Orchestration releases work.
Framework components provide reusable mechanisms.
```

An entrypoint should therefore avoid becoming the implementation location for:

```text
camera algorithms
generic communication protocols
persistent storage internals
workflow state machines
```

Its purpose is to connect the required pieces for a particular application execution path.

---

# Adding Future Entrypoints

As additional eWoodX workflows become established, new entrypoints may be introduced for areas such as:

```text
design
robot control
fabrication
data retrieval
additional sensing workflows
```

Where useful, a similar pattern can be followed:

```text
core application entrypoint
          ▲
          │
   ┌──────┴──────┐
   │             │
direct use   distributed wrapper
```

However, this should not be imposed as a universal requirement.

Future entrypoints should follow the actual runtime requirements of their corresponding operations.

---

# Development Principles

When extending the eWoodX entrypoint layer:

1. Keep actual operational algorithms in `projects.ewoodx.operations`.
2. Keep generic communication behavior in `framework.communication`.
3. Keep generic orchestration mechanics in `framework.orchestration`.
4. Keep project workflow definitions and request semantics in `projects.ewoodx.orchestration`.
5. Keep deployment values in `projects.ewoodx.config`.
6. Let entrypoints coordinate the context required to start project operations.
7. Reuse the same underlying operation path across direct and distributed execution where practical.
8. Preserve Master authority when an entrypoint participates in the distributed workflow.
9. Keep user cancellation distinct from execution failure.
10. Avoid duplicating sensing logic in the distributed wrapper.
11. Support programmatic context where it allows the same entrypoint to be reused by higher-level workflows.
12. Introduce new entrypoints according to actual application requirements rather than speculative future structure.

---

# Ongoing Development

The current package establishes two sensing execution paths:

```text
Direct Sensing
        │
        └── sensing_entrypoint.py

Distributed Sensing
        │
        └── sensing_agent_entrypoint.py
```

Both ultimately use:

```text
EWoodXSensingEntrypoint
```

and therefore share the same underlying sensing operations and persistence behavior.

This provides a useful foundation for continued development because project operations can remain independent of whether they are launched:

```text
manually
locally
through an agent
through a distributed orchestration
```

The exact set of entrypoints is expected to evolve as design, robot-control, fabrication, and other project workflows become established.

---

# Summary

`projects.ewoodx.entrypoints` defines how current eWoodX application processes are started.

For sensing, the architecture intentionally provides **two execution paths**:

```text
                    eWoodX SENSING
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
        DIRECT PATH              DISTRIBUTED PATH
             │                         │
sensing_entrypoint.py    sensing_agent_entrypoint.py
             │                         │
             │                    Master + Agent
             │                         │
             └────────────┬────────────┘
                          ▼
               EWoodXSensingEntrypoint
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
         Workspace      Entry       Equipment
                          │
                          ▼
                    EntityManager
                          │
                          ▼
                  Sensing Operation
                          │
                          ▼
                 Persistent Timber
```

The direct path provides simple local execution.

The distributed path adds:

```text
orchestration
action creation
agent claiming
local consumption
action dispatch
terminal synchronization
```

around the same sensing process.

The central architectural boundary is:

```text
ENTRYPOINT
    │
    └── coordinates how work starts

OPERATION
    │
    └── performs the work

AGENT
    │
    └── provides distributed runtime

ORCHESTRATION
    │
    └── defines and releases distributed work

FRAMEWORK
    │
    └── provides reusable mechanisms
```

This allows the current sensing capability to operate both independently and as part of the distributed eWoodX system without maintaining separate sensing implementations.