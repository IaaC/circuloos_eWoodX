# eWoodX Orchestration

The `projects.ewoodx.orchestration` package connects the generic orchestration and communication framework to eWoodX-specific workflows, data requests, and entity-file access.

It currently provides:

- the eWoodX sensing orchestration definition;
- master-side routing of project and generic workflow requests;
- master-side workspace and entity queries;
- agent-side forwarding of orchestration requests;
- semantic resolution of persistent entity files for generic file transfer.

The package does **not** implement the generic distributed action lifecycle itself. That responsibility remains in `framework.communication` and `framework.orchestration`.

Instead, this package gives those reusable mechanisms their eWoodX-specific meaning.

The project and its orchestration layer are under **continuous development**. The components documented here describe the current implementation and are expected to evolve as additional eWoodX workflows are introduced.

---

# Package Structure

```text
projects/ewoodx/orchestration/
├── __init__.py
├── definitions.py
├── master_handler.py
├── agent_handler.py
└── entity_file_resolver.py
```

The current responsibilities are:

| Module | Responsibility |
|---|---|
| `definitions.py` | Defines eWoodX workflows using the generic orchestration model. |
| `master_handler.py` | Handles eWoodX-specific master requests and delegates generic workflow requests. |
| `agent_handler.py` | Handles the project-specific agent-side request boundary and forwards orchestration requests to the master. |
| `entity_file_resolver.py` | Resolves semantic entity-file requests to authoritative workspace files. |
| `__init__.py` | Marks the package; currently does not re-export a consolidated public API. |

---

# Architectural Role

The package sits between the eWoodX application layer and the generic orchestration and communication framework.

```text
eWoodX Application
        │
        ▼
projects.ewoodx.orchestration
        │
        ├── project workflow definitions
        ├── project request routing
        ├── project data queries
        └── project file resolution
        │
        ▼
Generic Framework
        │
        ├── framework.orchestration
        ├── framework.communication
        └── framework.workspace
```

The distinction is:

```text
framework.orchestration
        │
        └── generic workflow structure
            and action progression

projects.ewoodx.orchestration
        │
        └── defines which workflows
            eWoodX currently uses
```

and:

```text
framework.communication
        │
        └── generic distributed
            execution protocol

projects.ewoodx.orchestration
        │
        └── connects project requests
            to that protocol
```

---

# Package Public API

The current:

```text
projects/ewoodx/orchestration/__init__.py
```

does not re-export orchestration classes or definitions.

Therefore, the package currently has **no consolidated package-level public API** through `orchestration.__all__`.

Components are imported directly from their modules when required.

For example:

```python
from projects.ewoodx.orchestration.definitions import (
    SENSING_ORCHESTRATION,
)
```

or:

```python
from projects.ewoodx.orchestration.master_handler import (
    EWoodXMasterHandler,
)
```

This README documents the important project-facing classes and definitions without implying a package-level API that does not currently exist.

---

# Current Components

The current package contains four primary project components:

```text
eWoodX ORCHESTRATION
        │
        ├── SENSING_ORCHESTRATION
        │
        ├── EWoodXMasterHandler
        │
        ├── EWoodXAgentHandler
        │
        └── EWoodXEntityFileResolver
```

Their responsibilities are deliberately different.

```text
SENSING_ORCHESTRATION
        │
        └── defines project workflow structure

EWoodXMasterHandler
        │
        └── owns master-side project request routing

EWoodXAgentHandler
        │
        └── provides agent-local project request routing

EWoodXEntityFileResolver
        │
        └── resolves semantic file requests
            to authoritative project files
```

---

# Sensing Orchestration Definition

Defined in:

```text
definitions.py
```

Current definition:

```python
SENSING_ORCHESTRATION = OrchestrationDefinition(
    name="sensing",
    steps=[
        OrchestrationStep(
            step_id="sense_timber",
            action="sense_timber",
            target="sensing",
        ),
    ],
)
```

The definition uses the generic:

```python
OrchestrationDefinition
OrchestrationStep
```

from:

```text
framework.orchestration
```

but gives those structures eWoodX-specific semantics.

---

# Current Sensing Workflow

The current sensing orchestration contains one step:

```text
sensing
   │
   ▼
sense_timber
```

The step is defined as:

```text
step_id = sense_timber
action  = sense_timber
target  = sensing
```

Conceptually:

```text
SENSING_ORCHESTRATION
        │
        ▼
Orchestrator.start(...)
        │
        ▼
Action
        │
        ├── action = "sense_timber"
        └── target = "sensing"
```

The target:

```text
sensing
```

corresponds to the role used by the current sensing agent.

The orchestration definition itself does not know which specific machine will execute the action.

That is resolved through the generic distributed communication workflow.

---

# Workflow Definition Boundary

The project definition specifies:

```text
what action should exist
        +
which role should execute it
        +
where it belongs in the workflow
```

It does not specify:

```text
TCP communication
action claiming
local persistence
polling
execution-state synchronization
camera execution
Timber segmentation
```

Those responsibilities belong elsewhere.

The boundary is:

```text
eWoodX Orchestration Definition
        │
        └── what work should be released

Communication Framework
        │
        └── which eligible agent claims it

eWoodX Operation
        │
        └── how the work is actually performed
```

---

# Master-Side Handler

Defined in:

```text
master_handler.py
```

Primary class:

```python
EWoodXMasterHandler
```

Constructor:

```python
EWoodXMasterHandler(
    workflow_handler: WorkflowHandler,
    orchestrator: Orchestrator,
)
```

The constructor requires two generic framework components:

```text
WorkflowHandler
        │
        └── generic distributed workflow requests

Orchestrator
        │
        └── generic orchestration progression
```

The eWoodX handler composes them with project-specific commands.

---

# `EWoodXMasterHandler.handle()`

Primary request interface:

```python
handle(
    request: Dict[str, Any],
) -> Dict[str, Any]
```

The current project-specific commands are:

```text
list_workspaces
list_indexed_entries
query_entities
start_orchestration
```

Any other command is delegated to:

```python
WorkflowHandler.handle(...)
```

Conceptually:

```text
incoming request
      │
      ▼
EWoodXMasterHandler
      │
      ├── eWoodX command?
      │       │
      │       └── handle project-side
      │
      └── otherwise
              │
              ▼
       WorkflowHandler
              │
              └── generic workflow command
```

This keeps project request semantics outside the generic communication framework.

---

# Master Request Routing

The current routing behavior is:

```text
EWoodXMasterHandler
        │
        ├── list_workspaces
        │       └── project workspace discovery
        │
        ├── list_indexed_entries
        │       └── project entity-data discovery
        │
        ├── query_entities
        │       └── project entity query
        │
        ├── start_orchestration
        │       └── project workflow start
        │
        └── other command
                │
                ▼
          WorkflowHandler
```

This is an important architectural boundary.

The generic `WorkflowHandler` does not need to know:

```text
what "sensing" means
what a Timber is
where eWoodX workspaces live
which metadata Timber uses
```

Those remain project concerns.

---

# Starting an Orchestration

A project orchestration is requested with:

```json
{
    "command": "start_orchestration",
    "orchestration": "sensing"
}
```

The current implementation recognizes:

```text
sensing
```

and starts:

```python
SENSING_ORCHESTRATION
```

through:

```python
self.orchestrator.start(
    definition=SENSING_ORCHESTRATION,
)
```

A successful response contains:

```json
{
    "status": "ok",
    "orchestration": "sensing",
    "action": {
        "...": "..."
    }
}
```

The returned action is the first action released by the generic orchestrator.

---

# Unknown Orchestrations

The current handler explicitly rejects unknown project orchestration names.

Conceptually:

```text
start_orchestration
        │
        ▼
"sensing"?
   │         │
  YES        NO
   │         │
   ▼         ▼
 start     error
```

This prevents the generic framework from having to interpret project-specific workflow names.

As additional workflows become established, they can be introduced at this project boundary.

---

# Workspace Discovery

The master handler currently supports:

```text
list_workspaces
```

The command discovers managed eWoodX workspaces under:

```text
<repository>/workspaces/
```

A directory is returned as a workspace only when it contains:

```text
workspace.json
```

Conceptually:

```text
workspaces/
├── workspace_A/
│   └── workspace.json    ✓
│
├── workspace_B/
│   └── workspace.json    ✓
│
└── unrelated_folder/
                         ✗
```

A successful response follows:

```json
{
    "status": "ok",
    "workspaces": [
        "workspace_A",
        "workspace_B"
    ]
}
```

This gives remote applications workspace names without exposing direct filesystem traversal as their interface.

---

# Entity Manager Resolution

Both master-side entity querying and entity-file resolution require access to the workspace-level entity index.

The current project implementation loads the requested workspace and searches its managed domains and entries.

Conceptually:

```text
workspace
   │
   ▼
DomainManager
   │
   ▼
managed domains
   │
   ▼
EntryManager
   │
   ▼
first existing managed entry
   │
   ▼
EntityManager
```

The first existing entry is used only because the current `EntityManager` constructor requires an `EntryPaths` context.

It does **not** mean that subsequent entity queries are restricted to that entry.

The entity index remains workspace-wide.

This distinction is important:

```text
constructor context
        ≠
query scope
```

---

# Indexed Entry Discovery

The master handler supports:

```text
list_indexed_entries
```

A request identifies the workspace:

```json
{
    "command": "list_indexed_entries",
    "workspace": "example_workspace"
}
```

The handler queries the workspace entity index and derives the domain and entry associated with each indexed entity.

The result contains entries represented by indexed entities together with their entity counts.

Conceptually:

```text
workspace entity index
        │
        ▼
all indexed entities
        │
        ▼
derive domain / entry
        │
        ▼
group and count
        │
        ▼
indexed entries
```

A response follows the structure:

```json
{
    "status": "ok",
    "workspace": "example_workspace",
    "entries": [
        {
            "domain": "sensing",
            "entry": "day...",
            "entity_count": 4
        }
    ]
}
```

This command therefore reports entries represented in the indexed entity data.

It is not a generic listing of every filesystem entry regardless of whether it contains indexed entities.

---

# Entity Queries

The master handler supports:

```text
query_entities
```

This allows remote applications to query the authoritative entity database indirectly through the master.

The client does not access:

```text
entities.db
```

directly.

Instead:

```text
Remote Application
        │
        │ semantic query
        ▼
Master
        │
        ▼
EWoodXMasterHandler
        │
        ▼
EntityManager
        │
        ▼
workspace entity index
```

This preserves the master-side authority boundary.

---

# Query Request

A query request can specify:

```text
workspace
filters
entries
```

For example:

```json
{
    "command": "query_entities",
    "workspace": "example_workspace",
    "filters": {
        "entity_type": "timber",
        "availability_status": "available",
        "length_mm": {
            "gte": 1200.0
        }
    }
}
```

The actual indexed filtering is performed by the generic:

```python
EntityManager.query_entities(...)
```

The project handler does not duplicate the generic comparison/query implementation.

---

# Entry-Scoped Queries

Queries can optionally be restricted to selected entries.

The current entry selection format is:

```json
{
    "entries": [
        {
            "domain": "sensing",
            "entry": "day..."
        }
    ]
}
```

Multiple entries can be supplied.

The current query sequence is:

```text
generic indexed filters
        │
        ▼
EntityManager.query_entities(...)
        │
        ▼
matching entities
        │
        ▼
optional eWoodX entry-scope filtering
        │
        ▼
serialized result
```

Therefore, property filtering remains generic while domain/entry selection is applied by the project handler.

---

# Query as Selection

The current data-access model treats the query itself as the entity selection mechanism.

For example, an application can request:

```text
all entities in a workspace
```

or:

```text
all entities in selected entries
```

or:

```text
entities matching properties
```

or:

```text
selected entries
        +
property filters
```

There is no additional generic interactive entity-selection layer in this package.

The requesting application determines the query appropriate to its workflow.

---

# Entity Serialization

The generic database determines **which entities match**.

The project handler then loads the canonical:

```text
entity.json
```

for each matching entity to return complete project information.

Conceptually:

```text
entities.db
    │
    └── discovery / filtering
            │
            ▼
      matching entity
            │
            ▼
        entity.json
            │
            └── canonical entity information
```

The current serialized result contains:

```text
entity_id
entity_type
domain
entry
created_at
availability_status
claimed_by
metadata
```

This preserves the distinction between:

```text
indexed discovery
```

and:

```text
canonical entity information
```

---

# Entity Location

The project handler derives an entity's domain and entry from its location relative to the workspace root.

The current expected structure is:

```text
workspace/
└── domain/
    └── entry/
        └── entity/
```

From this relative path, the handler extracts:

```text
domain
entry
```

for serialization and entry filtering.

This is project-side interpretation of the workspace structure.

---

# Agent-Side Handler

Defined in:

```text
agent_handler.py
```

Primary class:

```python
EWoodXAgentHandler
```

Constructor:

```python
EWoodXAgentHandler(
    agent_handler: AgentWorkflowHandler,
    master_client: TCPClient,
)
```

It combines:

```text
AgentWorkflowHandler
        │
        └── generic local workflow commands

TCPClient
        │
        └── connection to master
```

with the eWoodX project request boundary.

---

# `EWoodXAgentHandler.handle()`

Primary method:

```python
handle(
    request: Dict[str, Any],
) -> Dict[str, Any]
```

The current behavior is deliberately small.

```text
incoming local request
        │
        ▼
start_orchestration?
     │          │
    YES         NO
     │          │
     ▼          ▼
forward      delegate to
to master    AgentWorkflowHandler
```

The agent handler does not create project actions itself.

---

# Orchestration Forwarding

For:

```text
start_orchestration
```

the handler forwards the original request unchanged to the master:

```python
return self.master_client.send(
    request
)
```

Conceptually:

```text
Local Application
       │
       ▼
EWoodXAgentHandler
       │
       │ start_orchestration
       ▼
TCPClient
       │
       ▼
Master
       │
       ▼
EWoodXMasterHandler
       │
       ▼
Orchestrator
```

This keeps authoritative action creation on the master side.

---

# Why the Agent Does Not Create Actions

The project agent can receive the request that initiates a workflow, but it does not own authoritative orchestration state.

The separation is:

```text
REQUEST ORIGIN
      ≠
ACTION AUTHORITY
```

For example:

```text
sensing-side application
        │
        └── requests sensing
                 │
                 ▼
              Master
                 │
                 └── creates authoritative action
```

This allows an orchestration request to originate from an application near the equipment without transferring workflow authority away from the master.

---

# Generic Agent Workflow Delegation

Commands other than:

```text
start_orchestration
```

are delegated to the generic:

```python
AgentWorkflowHandler
```

This includes the local execution lifecycle provided by the communication framework.

The project handler therefore does not duplicate generic operations such as:

```text
consume action
report terminal state
```

The boundary remains:

```text
EWoodXAgentHandler
        │
        ├── project orchestration forwarding
        │
        └── generic local workflow delegation
```

---

# Entity File Resolver

Defined in:

```text
entity_file_resolver.py
```

Primary class:

```python
EWoodXEntityFileResolver
```

Its purpose is to translate a semantic entity-file request into an authoritative project filesystem path.

It is designed to work with the generic file-transfer transport.

---

# File Transfer Architecture

The separation is:

```text
CLIENT
   │
   │ semantic request
   ▼
MASTER FILE SERVICE
   │
   ▼
EWoodXEntityFileResolver
   │
   │ resolves authoritative file
   ▼
Generic TCPFileServer
   │
   │ streams bytes
   ▼
CLIENT
```

The project resolver knows:

```text
workspace
entity identity
workspace structure
authoritative entity location
```

The generic file-transfer framework knows:

```text
TCP negotiation
file streaming
transport mechanics
```

This prevents project filesystem semantics from leaking into the generic transport layer.

---

# Semantic Download Request

The current resolver expects a request containing:

```json
{
    "operation": "download",
    "workspace": "example_workspace",
    "entity_id": "T-0001-K7M",
    "file": "measurements.json"
}
```

The important semantic fields are:

```text
workspace
entity_id
file
```

The client does **not** send an authoritative server filesystem path.

---

# Why Semantic File Requests Are Used

A remote application should not need to know that a file physically exists at something like:

```text
<server>/workspaces/.../sensing/.../T-0001-K7M/measurements.json
```

Instead, it asks:

```text
workspace = ...
entity_id = T-0001-K7M
file = measurements.json
```

The master side resolves that request.

Conceptually:

```text
semantic identity
      │
      ▼
project resolver
      │
      ▼
authoritative path
```

This allows the physical storage layout to remain a server-side implementation detail.

---

# `resolve_download()`

Primary public method:

```python
resolve_download(
    request: Dict[str, Any],
) -> Path
```

The resolution sequence is:

```text
request
   │
   ▼
validate workspace / entity / file
   │
   ▼
load workspace EntityManager
   │
   ▼
EntityManager.load_entity(entity_id)
   │
   ▼
authoritative entity root
   │
   ▼
resolve requested file
   │
   ▼
validate containment
   │
   ▼
validate file exists
   │
   ▼
return Path
```

The returned `Path` is then used by the generic file server.

---

# File Containment Validation

The resolver explicitly checks that the requested file remains inside the authoritative entity directory.

Conceptually:

```text
entity root
    │
    ├── entity.json           ✓
    ├── measurements.json     ✓
    ├── image.jpg             ✓
    │
    └── ../../outside.file    ✗
```

After resolving the requested path, the resolver verifies that it is either the entity root itself or has the entity root among its parents.

For the current file-oriented request, the final path must also satisfy:

```python
requested_path.is_file()
```

This prevents path traversal from being used to retrieve arbitrary files outside the entity directory.

---

# Authoritative Entity Resolution

The resolver uses:

```python
EntityManager.load_entity(
    entity_id
)
```

rather than reconstructing the entity path from assumptions supplied by the client.

Therefore:

```text
client-provided entity ID
        │
        ▼
workspace entity index
        │
        ▼
registered relative path
        │
        ▼
authoritative entity directory
```

The entity database remains the authority for locating the entity.

---

# Query and Download Relationship

Entity querying and file downloading are intentionally separate capabilities.

A typical application flow is:

```text
1. Query entities
       │
       ▼
2. Receive matching entity information
       │
       ▼
3. Select required entity/file
       │
       ▼
4. Request semantic file download
       │
       ▼
5. Master resolves authoritative file
       │
       ▼
6. Generic file transport streams it
```

For example:

```text
query_entities
      │
      ▼
T-0001-K7M
      │
      ▼
download:
workspace + entity_id + measurements.json
      │
      ▼
local file
```

The query response therefore does not need to expose server filesystem paths.

---

# Authority Boundary

The current architecture intentionally keeps workspace authority on the master side.

```text
REMOTE APPLICATION
        │
        │ query / semantic request
        ▼
      MASTER
        │
        ├── EntityManager
        ├── workspace files
        └── authoritative paths
```

Remote applications should not directly access:

```text
Master SQLite database
Master workspace filesystem
Master absolute entity paths
```

Instead, they use project communication interfaces.

This allows the physical location of persistent data to remain independent of the requesting application.

---

# Orchestration vs Data Access

Although these capabilities currently share the `projects.ewoodx.orchestration` package, they serve different project-level purposes.

```text
EWoodXMasterHandler
        │
        ├── workflow requests
        │
        └── data queries

EWoodXEntityFileResolver
        │
        └── semantic file access
```

The common architectural reason for their current placement is that they form part of the project-side boundary between remote/distributed applications and authoritative master-side project state.

This README documents the current organization rather than implying that this grouping can never evolve.

---

# Distributed Sensing Flow

The current sensing workflow can be summarized as:

```text
Sensing Application
        │
        │ start_orchestration("sensing")
        ▼
EWoodXAgentHandler
        │
        │ forwards request
        ▼
Master
        │
        ▼
EWoodXMasterHandler
        │
        ▼
Orchestrator.start(
    SENSING_ORCHESTRATION
)
        │
        ▼
PENDING sense_timber Action
        │
        ▼
Generic Communication Workflow
        │
        ▼
Sensing Agent claims Action
        │
        ▼
Local execution
        │
        ▼
eWoodX sensing operation
```

The project orchestration package owns only the eWoodX-specific portions of this flow.

---

# Action Lifecycle Boundary

The project orchestration layer does not redefine the generic action lifecycle.

The lifecycle remains:

```text
PENDING
   │
   ▼
CLAIMED
   │
   ▼
RUNNING
   │
   ▼
COMPLETED / FAILED / CANCELLED
```

Ownership is divided as follows:

```text
Orchestration
      │
      └── releases work

Communication
      │
      └── distributes and synchronizes work

Agent / Executor
      │
      └── executes work and reports outcome
```

The project package supplies the domain-specific meaning of the action.

---

# Status Ownership

The orchestration package follows the framework principle:

> **Status ownership follows execution ownership.**

The master-side orchestration definition creates the work to be performed.

The executing side owns the operational outcome and reports it through the communication workflow.

Therefore, the project orchestration handler should not independently mark an action complete simply because it created or routed the action.

---

# Relationship with Operations

The orchestration package determines **what work should happen**.

The operations package determines **how the work is performed**.

```text
ORCHESTRATION
      │
      │ sense_timber
      ▼
distributed action
      │
      ▼
execution boundary
      │
      ▼
OPERATION
      │
      └── actual Timber sensing
```

This separation allows the sensing operation to remain independent of the distributed action protocol.

---

# Relationship with Agents

Agents provide the long-running distributed runtime around project workflows.

```text
projects.ewoodx.agents
        │
        ├── constructs communication services
        ├── constructs workflow handlers
        ├── starts polling
        └── exposes local/master services
                │
                ▼
projects.ewoodx.orchestration
        │
        └── supplies project-specific routing
            and workflow definitions
```

The orchestration package does not itself start network servers or polling loops.

---

# Relationship with Workspace

The project orchestration layer uses the generic workspace framework for authoritative entity discovery.

```text
EWoodXMasterHandler
        │
        ▼
load_workspace
        │
        ▼
DomainManager / EntryManager
        │
        ▼
EntityManager
        │
        ▼
entities.db + entity.json
```

Similarly:

```text
EWoodXEntityFileResolver
        │
        ▼
EntityManager.load_entity(...)
        │
        ▼
authoritative entity directory
```

The workspace framework provides the persistence mechanism.

The eWoodX orchestration layer determines how remote project applications are allowed to access that information.

---

# Relationship with Generic File Transfer

The file resolver does not implement file streaming.

That responsibility belongs to:

```text
framework.communication.transport
```

The division is:

| Responsibility | Owner |
|---|---|
| Interpret `workspace` | eWoodX resolver |
| Interpret `entity_id` | eWoodX resolver + `EntityManager` |
| Determine authoritative entity root | Workspace framework |
| Validate requested entity file | eWoodX resolver |
| Open/stream file bytes | Generic file-transfer transport |
| Network transfer protocol | Generic communication framework |

This keeps transport reusable for other projects and other semantic file resolvers.

---

# Current Request Interfaces

The current project-side request interfaces can be summarized as:

| Command / Request | Handler | Purpose |
|---|---|---|
| `start_orchestration` | `EWoodXMasterHandler` / forwarded by `EWoodXAgentHandler` | Start an eWoodX workflow. |
| `list_workspaces` | `EWoodXMasterHandler` | Discover managed eWoodX workspaces. |
| `list_indexed_entries` | `EWoodXMasterHandler` | Discover entries represented by indexed entities. |
| `query_entities` | `EWoodXMasterHandler` | Query authoritative entity data. |
| Other workflow commands | `WorkflowHandler` / `AgentWorkflowHandler` | Generic distributed action lifecycle. |
| Semantic entity download | `EWoodXEntityFileResolver` | Resolve an entity file for generic transfer. |

---

# Error Handling

Project handlers generally return structured error responses for request-level failures.

For example:

```json
{
    "status": "error",
    "message": "..."
}
```

This applies to project master commands such as:

```text
start_orchestration
list_workspaces
list_indexed_entries
query_entities
```

The entity-file resolver instead raises errors such as:

```text
ValueError
FileNotFoundError
```

to the surrounding generic file-transfer service, which owns the transport-level response behavior.

This difference reflects their different integration boundaries.

---

# Development Principles

When extending the eWoodX orchestration layer:

1. Keep generic orchestration mechanics in `framework.orchestration`.
2. Keep generic distributed action lifecycle behavior in `framework.communication`.
3. Keep eWoodX workflow definitions in `projects.ewoodx.orchestration`.
4. Keep authoritative action creation on the master side.
5. Keep request origin separate from workflow authority.
6. Use `EntityManager` rather than directly querying the SQLite database from remote applications.
7. Use semantic entity/file requests rather than exposing master filesystem paths.
8. Keep byte-transfer mechanics in the generic transport layer.
9. Keep actual sensing/design/robot execution inside project operations.
10. Add abstractions only when established project behavior demonstrates that they are necessary.

---

# Ongoing Development

The current orchestration package is intentionally small.

At present, the established project workflow definition is:

```text
sensing
    │
    ▼
sense_timber
```

The package also provides the first master-side data-access capabilities required by external applications:

```text
workspace discovery
indexed-entry discovery
entity querying
entity-file retrieval
```

As eWoodX develops, additional workflows may be introduced for areas such as:

```text
design
robot control
fabrication
additional sensing processes
multi-step material workflows
```

Those workflows should be added when their actual operational behavior is established rather than introducing speculative generic abstractions in advance.

---

# Summary

`projects.ewoodx.orchestration` is the project-specific bridge between eWoodX application semantics and the reusable orchestration, communication, workspace, and transport framework.

Its current structure can be summarized as:

```text
                  eWoodX APPLICATION
                         │
                         ▼
              EWoodX ORCHESTRATION
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   Workflow          Data Query        File Resolution
   Definition        & Routing
        │                │                 │
        ▼                ▼                 ▼
  Orchestrator     EntityManager      TCPFileServer
        │                │                 │
        └────────────────┼─────────────────┘
                         │
                         ▼
                  GENERIC FRAMEWORK
```

The central architectural boundaries are:

```text
eWoodX defines
WHAT workflow is required

framework.orchestration determines
HOW workflow steps are released

framework.communication determines
HOW distributed execution is synchronized

eWoodX operations determine
HOW project work is physically performed

framework.workspace determines
HOW persistent entities are organized and indexed

eWoodX orchestration determines
HOW project applications query and access that authoritative data
```

This keeps eWoodX-specific semantics at the project layer while allowing the underlying framework to remain reusable beyond this project.