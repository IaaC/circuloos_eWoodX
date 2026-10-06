# eWoodX Agents

The `projects.ewoodx.agents` package defines the current long-running distributed runtime processes used by eWoodX.

It composes reusable communication, storage, workflow, and orchestration components from the generic framework with eWoodX-specific configuration and request handlers.

The package currently provides two runtime applications:

- the **Master Agent**;
- the **Sensing Agent**.

These modules primarily perform **runtime composition**. They do not implement the underlying communication protocol, action lifecycle, persistence model, or project operations themselves.

The project and its agent architecture are under **continuous development**. The agents documented here represent the currently implemented distributed deployment and may evolve as additional project capabilities and machines are introduced.

---

# Package Structure

```text
projects/ewoodx/agents/
├── __init__.py
├── master_agent.py
└── sensing_agent.py
```

The responsibilities are:

| Module | Responsibility |
|---|---|
| `master_agent.py` | Composes and runs the authoritative eWoodX master communication and file-transfer runtime. |
| `sensing_agent.py` | Composes and runs the deployed sensing agent, including master polling and its local execution API. |
| `__init__.py` | Marks the package; currently does not re-export a consolidated public API. |

---

# Architectural Role

The agents package turns generic framework components into actual running eWoodX services.

Conceptually:

```text
                 eWoodX CONFIGURATION
                         │
                         ▼
                  eWoodX AGENTS
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
     MASTER                         SENSING AGENT
        │                                 │
        ▼                                 ▼
generic framework                 generic framework
components                       components
```

The framework provides reusable components such as:

```text
Agent
ActionStore
AgentActionStore
TCPClient
TCPServer
TCPFileServer
WorkflowClient
WorkflowHandler
AgentWorkflowHandler
AgentPoller
Orchestrator
```

The project agent modules determine:

```text
which components are instantiated
how they are connected
which project handlers are used
which ports are opened
where runtime state is stored
which roles an agent has
which long-running services are started
```

The distinction is:

```text
framework
    │
    └── reusable distributed mechanisms

projects.ewoodx.agents
    │
    └── deployed eWoodX runtime composition
```

---

# Package Public API

The current:

```text
projects/ewoodx/agents/__init__.py
```

does not re-export agent runtime functions.

Therefore, the package currently has **no consolidated package-level public API** through `agents.__all__`.

The two important runtime functions are imported directly from their modules when required:

```python
from projects.ewoodx.agents.master_agent import (
    run_master_agent,
)
```

and:

```python
from projects.ewoodx.agents.sensing_agent import (
    run_sensing_agent,
)
```

Both modules also provide:

```python
main()
```

for direct execution.

---

# Current Distributed Runtime

The current deployment contains:

```text
                         MASTER
                    authoritative side
                          │
                          │
                 workflow communication
                          │
                          ▼
                    SENSING AGENT
                     deployed agent
```

The Master owns the authoritative distributed action state.

The Sensing Agent maintains its own durable local execution state while communicating action lifecycle changes back to the Master.

The Sensing Agent also exposes a local API used by applications that execute work through that agent.

---

# Runtime Topology

The current runtime can be represented as:

```text
                           MASTER
              ┌─────────────────────────┐
              │                         │
              │  ActionStore            │
              │  WorkflowHandler        │
              │  Orchestrator           │
              │  EWoodXMasterHandler    │
              │                         │
              │  Command API            │
              │  File API               │
              └────────────┬────────────┘
                           │
                           │ TCP
                           │
              ┌────────────▼────────────┐
              │                         │
              │     SENSING AGENT       │
              │                         │
              │  Agent                  │
              │  AgentActionStore       │
              │  WorkflowClient         │
              │  AgentPoller            │
              │  AgentWorkflowHandler   │
              │  EWoodXAgentHandler     │
              │                         │
              │  Local API              │
              └────────────▲────────────┘
                           │
                           │ local TCP
                           │
                    local application
```

The actual sensing operation is started through the local execution side rather than being embedded directly in the long-running agent process.

---

# Master Agent

Defined in:

```text
master_agent.py
```

Primary runtime function:

```python
run_master_agent() -> None
```

Direct executable entry:

```python
main() -> None
```

The Master Agent is the authoritative distributed runtime for the current eWoodX deployment.

Its main responsibilities are:

```text
persistent authoritative action state
generic workflow request handling
project orchestration
project data queries
command communication
entity-file download service
```

---

# Master Runtime Composition

The Master is assembled in the following order:

```text
ActionStore
    │
    ├──────────────► WorkflowHandler
    │
    └──────────────► Orchestrator
                         │
                         ▼
                 EWoodXMasterHandler
                         │
                         ▼
                     TCPServer
```

In parallel, the Master creates:

```text
EWoodXEntityFileResolver
          │
          ▼
    TCPFileServer
```

The resulting runtime therefore exposes two separate services:

```text
Master
   │
   ├── command / workflow API
   │
   └── file-transfer API
```

---

# Master Persistent Action State

The Master creates:

```python
ActionStore(
    root=master_runtime_root,
)
```

where:

```text
master_runtime_root
```

is:

```text
AGENTS_RUNTIME_ROOT/master/
```

Conceptually:

```text
agents_runtime/
└── master/
    └── authoritative action state
```

This `ActionStore` is shared by both:

```python
WorkflowHandler
```

and:

```python
Orchestrator
```

so distributed workflow handling and orchestration progression operate on the same authoritative action state.

---

# Master Workflow Handler

The generic:

```python
WorkflowHandler(
    action_store=action_store,
)
```

handles the reusable distributed workflow commands.

Its responsibilities belong to:

```text
framework.communication.workflow
```

rather than to the eWoodX agent implementation.

The Master Agent only creates and connects the handler.

---

# Master Orchestrator

The generic:

```python
Orchestrator(
    action_store=action_store,
)
```

uses the same authoritative `ActionStore`.

The orchestrator provides the generic mechanism for:

```text
starting workflow definitions
releasing actions
advancing sequential workflows
```

The eWoodX-specific workflow definitions themselves remain in:

```text
projects.ewoodx.orchestration
```

---

# eWoodX Master Handler

The Master composes:

```python
EWoodXMasterHandler(
    workflow_handler=workflow_handler,
    orchestrator=orchestrator,
)
```

This gives the running Master a single project-facing request handler that can route:

```text
project orchestration requests
workspace discovery
entity queries
generic workflow requests
```

The detailed request semantics are documented in:

```text
projects/ewoodx/orchestration/README.md
```

---

# Master Command Server

The primary Master communication server is:

```python
TCPServer(
    handler=master_handler.handle,
    host=MASTER_BIND_HOST,
    port=MASTER_PORT,
)
```

The current configured service is:

```text
MASTER_BIND_HOST : MASTER_PORT
0.0.0.0          : 5105
```

This service carries command-style communication including:

```text
workflow requests
orchestration requests
workspace queries
entity queries
```

The network mechanics remain the responsibility of the generic `TCPServer`.

---

# Master File Server

The Master also creates:

```python
EWoodXEntityFileResolver()
```

and connects it to:

```python
TCPFileServer(
    download_resolver=(
        entity_file_resolver.resolve_download
    ),
    host=MASTER_BIND_HOST,
    port=MASTER_FILE_PORT,
)
```

The current file service is:

```text
MASTER_BIND_HOST : MASTER_FILE_PORT
0.0.0.0          : 5106
```

This service is separate from the command API.

The division is:

```text
5105
 │
 └── structured commands / workflow

5106
 │
 └── file-transfer stream
```

---

# Why the Master Uses Two Services

Command communication and file transfer have different transport requirements.

A normal command exchanges structured request/response data.

A file transfer needs:

```text
request negotiation
        │
        ▼
file metadata
        │
        ▼
raw byte stream
```

The current runtime therefore keeps them as separate services while allowing both to operate under the same authoritative Master.

Conceptually:

```text
                   MASTER
                     │
           ┌─────────┴─────────┐
           │                   │
           ▼                   ▼
      Command API          File API
        :5105               :5106
```

---

# Master File Resolution

The file server itself does not understand eWoodX entity semantics.

Instead:

```text
TCPFileServer
      │
      ▼
EWoodXEntityFileResolver
      │
      ▼
authoritative entity file
```

The resolver determines the valid server-side path.

The generic file server handles the byte transfer.

This preserves the separation between:

```text
project data semantics
```

and:

```text
generic transport mechanics
```

---

# Master Service Startup

The Master starts the file-transfer server in a daemon thread:

```python
file_server_thread = threading.Thread(
    target=file_server.start,
    daemon=True,
)
```

It then starts the main command server:

```python
file_server_thread.start()

server.start()
```

Conceptually:

```text
Master Process
     │
     ├── daemon thread
     │      │
     │      └── TCPFileServer
     │
     └── main blocking runtime
            │
            └── TCPServer
```

This allows both Master services to run concurrently within one process.

---

# Master Shutdown

The Master wraps runtime execution in:

```python
try:
    ...
finally:
    ...
```

During shutdown it calls:

```python
file_server.stop()
server.stop()
```

This ensures both communication services are asked to stop when the Master runtime exits.

---

# Running the Master

The module can be executed directly:

```bash
python projects/ewoodx/agents/master_agent.py
```

The module-level:

```python
main()
```

calls:

```python
run_master_agent()
```

At startup, the Master reports:

```text
runtime state location
Master API address
Master file API address
```

to the terminal.

---

# Sensing Agent

Defined in:

```text
sensing_agent.py
```

Primary runtime function:

```python
run_sensing_agent() -> None
```

Direct executable entry:

```python
main() -> None
```

The Sensing Agent is the current deployed eWoodX execution agent for actions targeted at the:

```text
sensing
```

role.

It is designed as a continuously running process.

---

# Sensing Agent Runtime Composition

The Sensing Agent assembles:

```text
Agent
  │
  ▼
AgentActionStore
  │
  ├──────────────► WorkflowClient
  │                    │
  │                    ▼
  │                AgentPoller
  │
  └──────────────► AgentWorkflowHandler
                         │
                         ▼
                  EWoodXAgentHandler
                         │
                         ▼
                     TCPServer
```

A:

```python
TCPClient
```

provides the connection from the agent to the Master.

---

# Agent Identity

The Sensing Agent creates:

```python
Agent(
    agent_id=SENSING_AGENT_ID,
    roles=SENSING_AGENT_ROLES,
)
```

The current configuration is:

```text
agent_id = sensing_pc_01
roles    = ["sensing"]
```

The distinction is important:

```text
agent ID
    │
    └── persistent deployed-agent identity

role
    │
    └── action claim eligibility
```

The ID identifies this deployed agent's local state.

The role determines which actions it can claim.

---

# Agent-Local Persistent State

The Sensing Agent creates:

```python
AgentActionStore(
    root=agent_runtime_root,
    agent=agent,
)
```

where:

```text
agent_runtime_root
```

is:

```text
AGENTS_RUNTIME_ROOT/<agent_id>/
```

For the current agent:

```text
agents_runtime/
└── sensing_pc_01/
    └── local durable action state
```

This storage is separate from the authoritative Master `ActionStore`.

---

# Master and Agent Storage

The current distributed persistence model is:

```text
agents_runtime/
│
├── master/
│     │
│     └── ActionStore
│         authoritative distributed state
│
└── sensing_pc_01/
      │
      └── AgentActionStore
          durable local execution state
```

These stores have different responsibilities.

```text
ActionStore
    │
    └── Master authority

AgentActionStore
    │
    └── local execution durability
```

The Sensing Agent does not directly modify the Master's store.

It communicates lifecycle changes through the workflow protocol.

---

# Master Connection

The Sensing Agent creates:

```python
TCPClient(
    host=MASTER_HOST,
    port=MASTER_PORT,
)
```

using the current configured Master connection:

```text
127.0.0.1:5105
```

This client is shared by the workflow and project request layers.

Conceptually:

```text
Sensing Agent
      │
      ▼
TCPClient
      │
      ▼
Master Command API
```

The current loopback address reflects the present configuration and can be changed through project configuration for deployment across machines.

---

# Workflow Client

The Sensing Agent creates:

```python
WorkflowClient(
    tcp_client=master_client,
    agent=agent,
    local_store=local_store,
)
```

The workflow client connects three important pieces:

```text
Master communication
        +
Agent identity
        +
Local persistent state
```

Conceptually:

```text
              WorkflowClient
              /      |      \
             /       |       \
            ▼        ▼        ▼
       TCPClient   Agent   AgentActionStore
```

It provides the agent-side distributed workflow operations required by the poller and local workflow handler.

---

# Master Polling

The Sensing Agent creates:

```python
AgentPoller(
    workflow_client=workflow_client,
    local_store=local_store,
    interval=SENSING_AGENT_POLL_INTERVAL,
)
```

The current configured interval is:

```text
1.0 second
```

The poller continuously checks whether the agent can obtain new work from the Master.

---

# Agent Busy Behavior

The generic `AgentPoller` respects the agent's local active state.

Conceptually:

```text
poll
 │
 ▼
local active action?
 │
 ├── YES ──► do not claim another action
 │
 └── NO
      │
      ▼
   ask Master
      │
      ▼
claim eligible action
```

This means the current Sensing Agent handles one active distributed action at a time through its local workflow state.

If another eligible action remains pending on the Master, it can be claimed after the current local action reaches synchronized terminal state.

This behavior is implemented by the generic communication framework; the project agent simply configures and starts the poller.

---

# Poller Startup

The Sensing Agent starts the poller before entering its local server loop:

```python
poller.start()
```

The poller runs independently while the local API remains available.

Conceptually:

```text
Sensing Agent Process
        │
        ├── AgentPoller
        │      │
        │      └── Master communication
        │
        └── Local TCPServer
               │
               └── local application communication
```

---

# Local Execution API

The Sensing Agent creates:

```python
AgentWorkflowHandler(
    local_store=local_store,
    workflow_client=workflow_client,
)
```

This generic handler exposes the agent-local workflow lifecycle to an executor.

It is then wrapped by:

```python
EWoodXAgentHandler(
    agent_handler=agent_handler,
    master_client=master_client,
)
```

The project handler adds eWoodX-specific request behavior while delegating generic local workflow commands to `AgentWorkflowHandler`.

---

# Local Server

The local API is exposed through:

```python
TCPServer(
    handler=project_handler.handle,
    host=SENSING_AGENT_HOST,
    port=SENSING_AGENT_PORT,
)
```

The current configured local service is:

```text
127.0.0.1:6105
```

Conceptually:

```text
Local Application
        │
        │ TCP
        ▼
127.0.0.1:6105
        │
        ▼
EWoodXAgentHandler
        │
        ├── project request
        │
        └── generic execution lifecycle
```

The local application does not need direct access to:

```text
AgentActionStore
WorkflowClient
AgentPoller
```

It interacts with the agent through this local API.

---

# Why the Agent Has a Local API

The long-running agent and the task executor are intentionally separated.

```text
LONG-RUNNING AGENT
       │
       ├── identity
       ├── polling
       ├── persistent local state
       ├── Master communication
       └── local execution API
               │
               ▼
         TASK EXECUTOR
               │
               └── performs project operation
```

This means the execution application can change without changing the distributed Master-agent protocol.

For example, an executor may currently be implemented in Python while a future application could communicate with the same agent boundary from another environment.

---

# Sensing Agent Request Routing

The local request flow is:

```text
Local Application
        │
        ▼
Local TCPServer
        │
        ▼
EWoodXAgentHandler
        │
        ├── start_orchestration
        │       │
        │       ▼
        │    Master
        │
        └── other workflow command
                │
                ▼
        AgentWorkflowHandler
```

This allows a local application to initiate a project workflow while preserving Master-side authority.

---

# Starting a Sensing Workflow

A local application can request:

```json
{
    "command": "start_orchestration",
    "orchestration": "sensing"
}
```

The request path is:

```text
Local Application
        │
        ▼
Sensing Agent
        │
        ▼
EWoodXAgentHandler
        │
        │ forwards unchanged
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
sense_timber Action
```

The Sensing Agent does not create the authoritative action itself.

---

# Claiming the Sensing Action

Once the Master has created the:

```text
sense_timber
```

action with target:

```text
sensing
```

the running `AgentPoller` can claim it because the current agent has:

```python
roles=["sensing"]
```

Conceptually:

```text
Master
  │
  │ PENDING sense_timber
  ▼
AgentPoller
  │
  │ claim_next
  ▼
Master validates role
  │
  ▼
CLAIMED
  │
  ▼
persist in AgentActionStore
```

The distributed claim behavior belongs to the generic workflow framework.

---

# Execution Boundary

Claiming an action does not itself perform Timber sensing.

The Sensing Agent establishes that the work is available locally.

A separate local executor then consumes and performs that work.

```text
AgentPoller
    │
    ▼
claimed local action
    │
    ▼
Local Execution API
    │
    ▼
Executor / Entrypoint
    │
    ▼
eWoodX Operation
```

This is an important architectural separation.

The agent is a distributed runtime.

The operation is the actual project task.

---

# Distributed Lifecycle

The current runtime participates in the generic lifecycle:

```text
PENDING
   │
   │ Master action
   ▼
CLAIMED
   │
   │ claimed by sensing agent
   ▼
CONSUMED locally
   │
   │ executor accepts work
   ▼
RUNNING
   │
   │ execution underway
   ▼
COMPLETED
FAILED
or
CANCELLED
```

`CONSUMED` is local execution state rather than a generic `ActionStatus`.

The detailed lifecycle semantics belong to:

```text
framework.communication
```

and are not reimplemented in the agent modules.

---

# Status Ownership

The current agent composition follows the principle:

> **Status ownership follows execution ownership.**

The Master owns authoritative distributed action state.

The Sensing Agent owns its durable local execution state.

The executor determines the operational outcome of the task and reports that outcome through the agent workflow.

Conceptually:

```text
MASTER
  │
  └── authoritative action state

SENSING AGENT
  │
  └── durable local execution state

EXECUTOR
  │
  └── actual operation outcome
```

---

# Sensing Agent Shutdown

Runtime execution is wrapped in:

```python
try:
    local_server.start()
finally:
    poller.stop()
    local_server.stop()
```

When the runtime exits, it stops:

```text
AgentPoller
Local TCPServer
```

before the process terminates.

---

# Running the Sensing Agent

The module can be executed directly:

```bash
python projects/ewoodx/agents/sensing_agent.py
```

The module-level:

```python
main()
```

calls:

```python
run_sensing_agent()
```

At startup, it reports:

```text
Agent ID
Agent roles
runtime state location
Master address
local API address
```

to the terminal.

---

# Current Network Services

The current eWoodX distributed runtime exposes three network endpoints:

| Service | Current Address | Purpose |
|---|---|---|
| Master command API | `0.0.0.0:5105` | Workflow, orchestration, and project query requests. |
| Master file API | `0.0.0.0:5106` | Entity-file transfer. |
| Sensing Agent local API | `127.0.0.1:6105` | Local execution and project requests through the sensing agent. |

For clients, the configured Master connection currently uses:

```text
127.0.0.1:5105
```

The bind address and client connection address intentionally serve different purposes.

---

# Current Runtime Storage

The current persistent runtime layout is conceptually:

```text
agents_runtime/
├── master/
│   └── authoritative distributed action state
│
└── sensing_pc_01/
    └── durable sensing-agent execution state
```

This runtime storage is separate from:

```text
workspaces/
```

which contains persistent project data and entities.

The distinction is:

```text
agents_runtime/
      │
      └── distributed execution state

workspaces/
      │
      └── project data
```

---

# Master Authority

The current architecture keeps authoritative distributed state and project data access on the Master side.

```text
                       MASTER
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ActionStore       Orchestrator    Project Data
                                         │
                                         ▼
                                   EntityManager
```

Agents and external applications interact with that authority through defined communication interfaces rather than directly accessing Master-local runtime state.

---

# Runtime vs Agent Identity

The term **agent** has two related but distinct uses in the current architecture.

The generic:

```python
Agent
```

object represents:

```text
identity
roles
metadata
```

The project module:

```text
sensing_agent.py
```

constructs the complete running service around that identity.

Conceptually:

```text
Agent
  │
  └── identity / capability description

Sensing Agent Runtime
  │
  ├── Agent
  ├── AgentActionStore
  ├── TCPClient
  ├── WorkflowClient
  ├── AgentPoller
  ├── handlers
  └── TCPServer
```

An `Agent` object alone is therefore not the full deployed process.

---

# Agent vs Executor

The agent should also be distinguished from the executor.

```text
AGENT
  │
  ├── communicates
  ├── polls
  ├── persists local action state
  └── exposes execution API
          │
          ▼
      EXECUTOR
          │
          └── performs actual operation
```

For sensing:

```text
Sensing Agent
      │
      ▼
Sensing Entrypoint
      │
      ▼
Timber Sensing Operation
```

This separation allows the distributed architecture to remain stable while the implementation of the executor evolves.

---

# Relationship with Orchestration

The agents instantiate and expose the runtime components required by project orchestration.

The Master creates:

```text
Orchestrator
      │
      ▼
EWoodXMasterHandler
```

The Sensing Agent creates:

```text
EWoodXAgentHandler
```

The actual project workflow definitions remain in:

```text
projects/ewoodx/orchestration/
```

The agents therefore provide the runtime environment in which those definitions and handlers operate.

---

# Relationship with Operations

The agents do not contain sensing or projection algorithms.

For example:

```text
sensing_agent.py
```

does not implement:

```text
camera capture
ArUco detection
Timber segmentation
Timber measurement
entity creation
```

Those belong to:

```text
projects/ewoodx/operations/
```

The separation is:

```text
AGENT
    │
    └── makes distributed work available

ENTRYPOINT
    │
    └── connects execution request to operation

OPERATION
    │
    └── performs the actual task
```

---

# Relationship with Configuration

Agent deployment values are defined in:

```text
projects/ewoodx/config/communication.py
```

rather than hard-coded into the runtime composition.

The agent modules consume configuration such as:

```text
AGENTS_RUNTIME_ROOT

MASTER_BIND_HOST
MASTER_HOST
MASTER_PORT
MASTER_FILE_PORT

SENSING_AGENT_ID
SENSING_AGENT_ROLES
SENSING_AGENT_HOST
SENSING_AGENT_PORT
SENSING_AGENT_POLL_INTERVAL
```

This keeps runtime composition separate from project deployment values.

---

# Relationship with Generic Communication

Most of the agent runtime behavior is provided by:

```text
framework.communication
```

The current composition uses:

```text
core
 └── Agent

storage
 ├── ActionStore
 └── AgentActionStore

transport
 ├── TCPClient
 ├── TCPServer
 └── TCPFileServer

workflow
 ├── WorkflowClient
 ├── WorkflowHandler
 ├── AgentWorkflowHandler
 └── AgentPoller
```

The project agents should therefore remain relatively small.

If generic transport or lifecycle behavior needs to change, that behavior should normally be addressed in the framework rather than duplicated inside these runtime scripts.

---

# Current End-to-End Sensing Runtime

The current sensing execution path can be summarized as:

```text
                    MASTER AGENT
                         │
                         │
                 ActionStore
                         │
                 Orchestrator
                         │
                         ▼
                sense_timber
                    PENDING
                         │
                         ▼
                  AgentPoller
                         │
                         ▼
                   CLAIMED
                         │
                         ▼
                AgentActionStore
                         │
                         ▼
                 Local Agent API
                         │
                         ▼
              Sensing Entrypoint
                         │
                         ▼
               consume_action
                         │
                         ▼
                    RUNNING
                         │
                         ▼
             Timber Sensing Operation
                         │
                         ▼
             COMPLETED / FAILED /
                   CANCELLED
                         │
                         ▼
                    MASTER
```

The agent layer is therefore the distributed bridge between authoritative workflow state and local project execution.

---

# Current Master Runtime

The current Master runtime can be summarized independently as:

```text
                   MASTER PROCESS
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
     Command Service               File Service
          │                             │
          ▼                             ▼
 EWoodXMasterHandler        EWoodXEntityFileResolver
          │                             │
     ┌────┴────┐                        ▼
     │         │                  TCPFileServer
     ▼         ▼
Workflow   Orchestrator
Handler
     │         │
     └────┬────┘
          ▼
      ActionStore
```

This makes the Master both:

```text
distributed workflow authority
```

and:

```text
authoritative gateway to current entity data/files
```

without requiring clients to access Master-local storage directly.

---

# Current Sensing Agent Runtime

The Sensing Agent can be summarized as:

```text
                SENSING AGENT PROCESS
                         │
                      Agent
                         │
                AgentActionStore
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
      AgentPoller                 Local API
          │                             │
          ▼                             ▼
    WorkflowClient            EWoodXAgentHandler
          │                             │
          │                     AgentWorkflowHandler
          │                             │
          └──────────────┬──────────────┘
                         ▼
                    TCPClient
                         │
                         ▼
                       Master
```

This process remains alive independently of an individual sensing operation.

---

# Adding Future Agents

Additional project agents should follow the same architectural principles when appropriate:

```text
Agent identity
      +
Agent-local persistent state
      +
Master connection
      +
WorkflowClient
      +
AgentPoller
      +
local execution API
```

However, this should not be treated as a requirement that every future process must have exactly the same runtime composition.

New agents should be introduced according to their actual execution and communication requirements.

Potential future project roles may include:

```text
design
robot_control
additional sensing
other distributed processes
```

but these should only become concrete agent implementations when their runtime behavior is established.

---

# Development Principles

When extending the eWoodX agent layer:

1. Keep reusable communication behavior in `framework.communication`.
2. Keep generic orchestration mechanics in `framework.orchestration`.
3. Keep eWoodX-specific runtime composition in `projects.ewoodx.agents`.
4. Keep deployment values in `projects.ewoodx.config`.
5. Keep project request semantics in `projects.ewoodx.orchestration`.
6. Keep physical/project algorithms in `projects.ewoodx.operations`.
7. Preserve Master authority over distributed action state.
8. Preserve durable agent-local execution state.
9. Keep agent identity separate from the complete runtime process.
10. Keep the long-running agent separate from the task executor where that separation supports distributed deployment.
11. Avoid duplicating framework lifecycle or transport logic in project agents.
12. Add new agent abstractions only when actual deployment requirements justify them.

---

# Ongoing Development

The current agent architecture contains:

```text
Master Agent
Sensing Agent
```

This is sufficient for the currently established distributed sensing workflow.

The architecture is intentionally extensible to additional deployed processes without requiring the current framework to predict all future agents in advance.

As additional project workflows become established, the agent layer may grow to include runtimes associated with:

```text
design
robot control
additional sensing equipment
fabrication
other external systems
```

The exact topology should follow the operational requirements of those workflows.

---

# Summary

`projects.ewoodx.agents` is the runtime composition layer for the current distributed eWoodX system.

```text
                         eWoodX AGENTS
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
             MASTER                    SENSING AGENT
                │                           │
       authoritative state             local state
       orchestration                    polling
       command API                      local API
       file API                         Master client
                │                           │
                └─────────────┬─────────────┘
                              │
                              ▼
                    GENERIC FRAMEWORK
```

The central boundaries are:

```text
FRAMEWORK
    │
    └── provides reusable distributed mechanisms

CONFIG
    │
    └── defines deployment-specific values

ORCHESTRATION
    │
    └── defines project workflows and request semantics

AGENTS
    │
    └── compose those pieces into running services

ENTRYPOINTS / OPERATIONS
    │
    └── perform actual project work
```

The Master and Sensing Agent therefore provide the persistent distributed runtime around eWoodX workflows without embedding the actual project operations into the communication services themselves.