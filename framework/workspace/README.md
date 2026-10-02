# Workspace Framework

The `framework.workspace` package provides persistent organization of operational data and optional indexed management of identifiable entities.

At its core, the package defines the organizational hierarchy:

```text
Workspace
    │
    └── Domain
          │
          └── Entry
```

An application may optionally extend an entry with framework-managed entities:

```text
Workspace
    │
    └── Domain
          │
          └── Entry
                │
                ├── Entity
                ├── Entity
                └── ...
```

The distinction is important:

```text
Workspace → Domain → Entry
    │
    └── core persistent organizational hierarchy

EntityManager
    │
    └── optional persistent entity/index layer
```

A project does **not** need to use `EntityManager` or SQLite in order to use the workspace framework.

This allows the same workspace structure to support different application architectures, including:

```text
runtime / application-driven data resolution

and

persistent indexed entity discovery
```

The package-level public API is:

```python
from framework.workspace import (
    DirectoryManager,
    WorkspacePaths,
    init_workspace,
    load_workspace,
    DomainManager,
    DomainPaths,
    EntryManager,
    EntryPaths,
    EntityManager,
    EntityPaths,
)
```

---

# Purpose

The workspace framework provides a consistent persistent structure for applications that generate, transform, and consume data across multiple operational domains.

The fundamental structure is:

```text
project/
│
├── workspaces/
│   └── session_001/
│       │
│       ├── workspace.json
│       │
│       ├── sensing/
│       │   ├── domain.json
│       │   └── entry_001/
│       │       ├── entry.json
│       │       └── application-defined data
│       │
│       ├── design/
│       │   └── ...
│       │
│       └── robot_control/
│           └── ...
│
└── .last_workspace
```

What exists below an entry depends on the application.

For example, an application may maintain runtime-oriented files and manifests:

```text
entry_001/
├── entry.json
├── processing_state.json
├── outputs/
├── results/
└── application-defined manifests
```

Another application may use persistent framework-managed entities:

```text
entry_001/
├── entry.json
├── entity_001/
│   ├── entity.json
│   └── application-defined files
└── entity_002/
    ├── entity.json
    └── application-defined files
```

When `EntityManager` is used, the workspace additionally contains:

```text
index/
└── entities.db
```

The exact domain names, entry naming conventions, runtime data structures, entity types, entity metadata, and artifact files are defined by the application.

The framework manages persistent organizational boundaries without assigning application-specific meaning to them.

---

# Responsibility

The core workspace layer provides:

- project workspace creation and loading;
- project-defined workspace directory layouts;
- persistent workspace manifests;
- functional domain creation and discovery;
- persistent entry creation and discovery.

The optional entity-management layer additionally provides:

- persistent entity creation;
- canonical entity manifests;
- workspace-wide entity registration;
- configurable entity metadata indexing;
- entity querying;
- entity availability and claiming state.

The workspace package does **not**:

- require applications to use entities;
- require applications to use SQLite;
- define application-specific runtime query semantics;
- define application-specific runtime-state formats;
- define application-specific domain names;
- define entry naming conventions;
- define entity types;
- define application-specific metadata schemas;
- determine which artifact files belong to an entity;
- transfer files across a network;
- define distributed actions or agents;
- orchestrate operational workflows.

Those decisions belong to the application or other framework layers.

---

# Package Structure

```text
workspace/
├── __init__.py
├── directory_manager.py
├── workspace_manager.py
├── domain_manager.py
├── entry_manager.py
└── entity_manager.py
```

The core dependency chain is:

```text
DirectoryManager
      │
      ▼
WorkspacePaths
      │
      ▼
DomainManager
      │
      ▼
DomainPaths
      │
      ▼
EntryManager
      │
      ▼
EntryPaths
```

The optional entity layer extends that hierarchy:

```text
EntryPaths
    │
    ▼
EntityManager
    │
    ▼
EntityPaths
```

---

# Hierarchy

## Workspace

A workspace represents the overall persistent operational context.

```text
Workspace
```

Examples could include:

- one project session;
- one experiment;
- one production run;
- one dataset;
- another application-defined working context.

The framework does not define what a workspace means semantically.

---

## Domain

A domain is a functional area inside a workspace.

```text
Workspace
    │
    ├── sensing
    ├── design
    └── robot_control
```

Possible domains include:

```text
sensing
design
planning
inspection
fabrication
robot_control
```

These are examples only.

`DomainManager` does not maintain a fixed list of valid domain names.

---

## Entry

An entry is a named persistent context within one domain.

```text
Workspace
    │
    └── sensing
          │
          ├── entry_001
          ├── entry_002
          └── entry_003
```

An application may use entries to represent:

- sessions;
- days;
- batches;
- iterations;
- acquisitions;
- processing runs.

The framework does not prescribe the naming or semantics.

An entry is the lowest required organizational level provided by the core workspace hierarchy.

Applications may organize their own files, manifests, runtime state, or other persistent data below it without using the entity layer.

---

## Entity

An entity is an **optional** individually identifiable persistent object associated with an entry.

```text
Workspace
    │
    └── Domain
          │
          └── Entry
                │
                ├── Entity A
                ├── Entity B
                └── Entity C
```

Entities are used when an application requires persistent object identity and workspace-wide discovery.

Each framework-managed entity has:

```text
entity directory
      │
      ├── entity.json
      └── application-defined files
```

The framework manages entity identity, canonical entity metadata, indexing, and availability state.

The application may place additional artifacts inside the entity directory.

Applications that do not require persistent indexed objects do not need to use entities.

---

# Data-Access Models

The workspace framework intentionally does not require every application to discover operational data in the same way.

Two important usage patterns are supported by the architecture.

## Runtime / Application-Driven Resolution

Some applications determine relevant data dynamically while the system is running.

In this model:

```text
Workspace
    ↓
Domain
    ↓
Entry
    ↓
runtime state / manifests / files
    ↓
application-specific logic
    ↓
requested data
```

The application may determine relevant data from:

- the active workspace;
- the current domain or entry;
- runtime state;
- application-specific manifests;
- generated output records;
- filesystem contents;
- another application-defined store.

For example:

```text
workspace/
└── processing/
    ├── domain.json
    └── run_001/
        ├── entry.json
        ├── processing_state.json
        └── outputs/
```

An application-specific handler may inspect the current state or output manifest to determine which result satisfies a request.

In this model, the workspace framework provides the persistent organizational context.

The actual runtime query or resolution logic belongs to the application.

No `EntityManager` or SQLite entity index is required.

---

## Persistent Indexed Entity Discovery

Other applications need persistent discovery of individually identifiable objects based on their properties.

In this model:

```text
Workspace
    ↓
Domain
    ↓
Entry
    ↓
Entity
    │
    ├── entity.json
    └── artifacts

          +

workspace/index/entities.db
          │
          ▼
EntityManager.query_entities()
```

`EntityManager` provides:

- persistent entity identity;
- canonical entity manifests;
- workspace-wide registration;
- indexed metadata;
- property-based queries;
- availability state;
- claiming.

This model is useful when later operations need questions such as:

```text
Which available entities satisfy these properties?

Where is entity X stored?

Which entities of this type exist?

Which entity is currently claimed?
```

---

## Combining the Models

The two approaches are not separate workspace frameworks.

They are different ways applications can use the same persistent organizational foundation:

```text
                         WORKSPACE
                             │
                           DOMAIN
                             │
                           ENTRY
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     runtime/application              EntityManager
         data model                       model
              │                             │
              ▼                             ▼
    runtime resolution              indexed discovery
    manifests / state               entity.json
    application stores              entities.db
```

An application may use only the runtime-oriented model.

An application may use only the indexed-entity model.

An application may also combine them when different parts of the workflow require different persistence or discovery semantics.

The framework therefore does **not** require:

```text
Workspace → Domain → Entry → Entity
```

for every application.

The core organizational hierarchy ends at:

```text
Workspace → Domain → Entry
```

`Entity` is an optional managed layer.

---

# Persistence Models

The workspace package does not impose one universal persistence mechanism for all application data.

## Core Filesystem Persistence

The core hierarchy uses directories and JSON manifests:

```text
workspace.json
domain.json
entry.json
```

Conceptually:

```text
FILESYSTEM / MANIFESTS
        │
        ▼
Workspace
        │
        ▼
Domain
        │
        ▼
Entry
        │
        ▼
application-defined data
```

This is sufficient for applications whose operational data are resolved by their own application logic.

No SQLite database is required by the core hierarchy.

---

## Optional Entity Persistence

When `EntityManager` is used, it adds canonical entity manifests:

```text
entity.json
```

and a workspace-level SQLite database:

```text
<workspace>/index/entities.db
```

The two representations serve different purposes:

```text
FILESYSTEM / JSON                     SQLITE

canonical hierarchy                   entity discovery index
canonical entity metadata             searchable columns
entity artifact location              relative entity path
       │                                   │
       └──────────────┬────────────────────┘
                      ▼
                  EntityManager
```

The SQLite database does not replace `entity.json`.

It is an indexed discovery mechanism associated specifically with the `EntityManager` model.

---

# Choosing a Data Model

A useful conceptual boundary is:

```text
Does the application require persistent,
property-based discovery of individually
identified objects?
              │
        ┌─────┴─────┐
        │           │
       NO          YES
        │           │
        ▼           ▼
Workspace /       Workspace /
Domain / Entry    Domain / Entry
        │           │
        ▼           ▼
application       EntityManager
runtime logic       +
                  entities.db
```

Use the core workspace hierarchy when data are naturally resolved from the current operational context.

Use `EntityManager` when objects require durable identity, indexed discovery, availability, or claiming.

The choice belongs to the application.

---

# Runtime Queries vs Entity Queries

The term **query** can refer to two different operations.

## Runtime Query

```text
request
   ↓
application logic
   ↓
current workspace / entry / runtime state
   ↓
application-defined result
```

The workspace framework does not prescribe how this query is evaluated.

Application logic may inspect:

```text
JSON manifests
runtime state
output records
filesystem contents
application-specific stores
```

The workspace package therefore supports the persistent context in which runtime querying can operate, but it does not currently provide a generic runtime-query manager.

---

## Entity Query

```text
filters
   ↓
EntityManager.query_entities()
   ↓
workspace/index/entities.db
   ↓
registered EntityPaths
```

This is a specific framework capability with a defined indexed query model.

Keeping these concepts separate prevents application-specific runtime semantics from being forced into the generic entity database.

---

# DirectoryManager

```python
class DirectoryManager
```

`DirectoryManager` manages a project-defined directory layout relative to a root directory.

The framework does not assign meaning to the directory keys.

---

## Constructor

```python
DirectoryManager(
    root: str | Path,
    layout: dict[str, str | Path],
)
```

Example:

```python
from framework.workspace import (
    DirectoryManager,
)

manager = DirectoryManager(
    root="workspace_001",
    layout={
        "sensing": "sensing",
        "design": "design",
        "robot_control": "robot_control",
    },
)
```

Paths in the layout must be relative and may not escape the workspace through `..`.

---

## Public Attributes

```python
manager.root
manager.layout
```

`root` is stored as a resolved `Path`.

`layout` contains the validated relative directory layout.

---

## `ensure_directories()`

```python
manager.ensure_directories() -> None
```

Creates the root and all configured directories.

Existing directories are preserved.

---

## `directory()`

```python
manager.directory(
    key: str,
) -> Path
```

Returns the resolved absolute path associated with one configured key.

Unknown keys raise `KeyError`.

---

## `directories()`

```python
manager.directories() -> dict[str, Path]
```

Returns all configured directory paths as resolved absolute `Path` objects.

---

## `relative_layout()`

```python
manager.relative_layout() -> dict[str, str]
```

Returns the configured layout in serializable relative form.

This representation is used in the workspace manifest.

---

# WorkspacePaths

```python
@dataclass
class WorkspacePaths
```

`WorkspacePaths` represents the paths belonging to one loaded or initialized workspace.

## Public Attributes

```python
workspace.root
workspace.workspace_name
workspace.directories
workspace.manifest
```

The fields contain:

| Attribute | Meaning |
|---|---|
| `root` | Workspace root directory. |
| `workspace_name` | Workspace name. |
| `directories` | Configured directory paths keyed by application-defined names. |
| `manifest` | Path to `workspace.json`. |

---

## `directory()`

```python
workspace.directory(
    key: str,
) -> Path
```

Returns one configured workspace directory.

Unknown keys raise `KeyError`.

---

# Creating a Workspace

## `init_workspace()`

```python
init_workspace(
    project_root: str | Path,
    workspace_name: str,
    layout: dict[str, str | Path],
) -> WorkspacePaths
```

Creates or initializes a named workspace.

Example:

```python
from framework.workspace import (
    init_workspace,
)

workspace = init_workspace(
    project_root="/path/to/project",
    workspace_name="session_001",
    layout={
        "sensing": "sensing",
        "design": "design",
        "robot_control": "robot_control",
    },
)
```

The resulting structure is:

```text
project/
├── .last_workspace
└── workspaces/
    ├── latest
    └── session_001/
        ├── workspace.json
        ├── sensing/
        ├── design/
        └── robot_control/
```

`latest` is normally a relative symbolic link.

If symbolic links are unavailable, the framework falls back to a text file containing the workspace path.

---

# Workspace Manifest

Initialization writes:

```text
workspace.json
```

containing information equivalent to:

```json
{
  "workspace_name": "session_001",
  "created_at": "2026-01-01T10:00:00",
  "directories": {
    "sensing": "sensing",
    "design": "design",
    "robot_control": "robot_control"
  },
  "platform": "..."
}
```

The stored directory layout allows the workspace to reconstruct its configured directories later.

---

# Recent Workspace

Workspace initialization also writes:

```text
<project_root>/.last_workspace
```

containing the latest workspace name.

This provides a simple persistent recent-workspace mechanism.

---

# Loading a Workspace

## `load_workspace()`

```python
load_workspace(
    project_root: str | Path,
    workspace_name: str | None = None,
    layout: dict[str, str | Path] | None = None,
) -> WorkspacePaths
```

Loads an existing workspace.

Explicit loading:

```python
workspace = load_workspace(
    project_root="/path/to/project",
    workspace_name="session_001",
)
```

If no workspace name is supplied, resolution follows:

```text
1. <project_root>/.last_workspace
              │
              ▼
2. <project_root>/workspaces/latest
```

If neither identifies a workspace, `FileNotFoundError` is raised.

---

# Workspace Layout Reconstruction

Normally `load_workspace()` reads the layout from:

```text
workspace.json
```

Therefore the caller does not need to supply the layout again.

If the manifest is missing:

```python
load_workspace(
    project_root=...,
    workspace_name=...,
    layout={
        ...
    },
)
```

requires an explicit layout.

Without either the manifest or supplied layout, loading fails.

---

# DomainPaths

```python
@dataclass(frozen=True)
class DomainPaths
```

Represents one managed workspace domain.

## Public Attributes

```python
domain.root
domain.domain_name
domain.manifest
```

| Attribute | Meaning |
|---|---|
| `root` | Domain root directory. |
| `domain_name` | Domain name. |
| `manifest` | Path to `domain.json`. |

---

# DomainManager

```python
class DomainManager
```

Manages functional domains inside an existing workspace.

## Constructor

```python
DomainManager(
    workspace: WorkspacePaths,
)
```

Example:

```python
from framework.workspace import (
    DomainManager,
)

domain_manager = DomainManager(
    workspace=workspace,
)
```

---

## Public Attributes

```python
domain_manager.workspace
```

References the `WorkspacePaths` instance being managed.

---

## `domain_path()`

```python
domain_manager.domain_path(
    domain_name: str,
) -> Path
```

Returns the expected domain path.

The domain does not need to exist.

Domain names must be single directory names.

Absolute paths, `.` and `..`, and multi-part paths are rejected.

---

## `exists()`

```python
domain_manager.exists(
    domain_name: str,
) -> bool
```

Returns `True` only when both exist:

```text
domain directory
      +
domain.json
```

A plain directory without a domain manifest is not considered a managed domain.

---

## `ensure_domain()`

```python
domain_manager.ensure_domain(
    domain_name: str,
) -> DomainPaths
```

Creates the domain when necessary and returns its paths.

Example:

```python
sensing = domain_manager.ensure_domain(
    "sensing"
)
```

The resulting structure is:

```text
workspace/
└── sensing/
    └── domain.json
```

Calling `ensure_domain()` for an existing managed domain does not rewrite an existing manifest.

---

## `load_domain()`

```python
domain_manager.load_domain(
    domain_name: str,
) -> DomainPaths
```

Loads an existing managed domain.

It raises an error when:

- the path does not exist;
- the path is not a directory;
- `domain.json` is missing.

---

## `list_domains()`

```python
domain_manager.list_domains() -> list[DomainPaths]
```

Returns managed domains sorted by directory name.

Only directories containing:

```text
domain.json
```

are included.

---

# EntryPaths

```python
@dataclass(frozen=True)
class EntryPaths
```

Represents one managed entry.

## Public Attributes

```python
entry.root
entry.entry_name
entry.manifest
```

| Attribute | Meaning |
|---|---|
| `root` | Entry root directory. |
| `entry_name` | Entry name. |
| `manifest` | Path to `entry.json`. |

---

# EntryManager

```python
class EntryManager
```

Manages persistent entries inside one domain.

## Constructor

```python
EntryManager(
    domain: DomainPaths,
)
```

Example:

```python
from framework.workspace import (
    EntryManager,
)

entry_manager = EntryManager(
    domain=sensing,
)
```

---

## Public Attributes

```python
entry_manager.domain
```

References the managed `DomainPaths`.

---

## `entry_path()`

```python
entry_manager.entry_path(
    entry_name: str,
) -> Path
```

Returns the expected path for an entry.

The entry does not need to exist.

Entry names must be single directory names.

---

## `exists()`

```python
entry_manager.exists(
    entry_name: str,
) -> bool
```

Returns `True` only when the entry directory and `entry.json` both exist.

---

## `ensure_entry()`

```python
entry_manager.ensure_entry(
    entry_name: str,
) -> EntryPaths
```

Creates an entry if necessary.

Example:

```python
entry = entry_manager.ensure_entry(
    "entry_001"
)
```

Result:

```text
sensing/
├── domain.json
└── entry_001/
    └── entry.json
```

---

## `load_entry()`

```python
entry_manager.load_entry(
    entry_name: str,
) -> EntryPaths
```

Loads an existing managed entry.

Missing directories or manifests are rejected.

---

## `list_entries()`

```python
entry_manager.list_entries() -> list[EntryPaths]
```

Returns managed entries sorted by directory name.

Only directories containing `entry.json` are returned.

---

# Optional Entity Layer

The remainder of this README describes the optional indexed-entity model.

Applications that use only `Workspace → Domain → Entry` do not need to instantiate `EntityManager` or create `EntityPaths`.

---

# EntityPaths

```python
@dataclass(frozen=True)
class EntityPaths
```

Represents one registered persistent entity.

## Public Attributes

```python
entity.root
entity.entity_id
entity.manifest
```

| Attribute | Meaning |
|---|---|
| `root` | Entity root directory. |
| `entity_id` | Persistent entity identifier. |
| `manifest` | Path to `entity.json`. |

The entity root is also the location where the application can store entity-specific artifacts.

---

# EntityManager

```python
class EntityManager
```

`EntityManager` manages persistent entities and the workspace-wide entity index.

It combines:

```text
entry
  │
  └── location for NEW entities

workspace
  │
  └── scope for entity indexing and discovery
```

This distinction is important.

An `EntityManager` is constructed with one `EntryPaths`, but registered entities are indexed in one database shared by the entire workspace.

---

## Constructor

```python
EntityManager(
    workspace: WorkspacePaths,
    entry: EntryPaths,
    index_schema: dict[str, str] | None = None,
)
```

Example:

```python
from framework.workspace import (
    EntityManager,
)

entity_manager = EntityManager(
    workspace=workspace,
    entry=entry,
    index_schema={
        "color": "TEXT",
        "length_mm": "REAL",
        "width_mm": "REAL",
    },
)
```

Construction initializes or evolves:

```text
<workspace>/index/entities.db
```

---

## Public Attributes

```python
entity_manager.workspace
entity_manager.entry
entity_manager.index_schema
entity_manager.index_directory
entity_manager.database_path
```

These represent:

| Attribute | Meaning |
|---|---|
| `workspace` | Workspace containing the shared entity index. |
| `entry` | Entry where new entities created by this manager are placed. |
| `index_schema` | Validated application-defined indexed columns. |
| `index_directory` | `<workspace>/index`. |
| `database_path` | `<workspace>/index/entities.db`. |

---

# Entity Index

Every entity managed by `EntityManager` is registered in the workspace-level SQLite table:

```text
entities
```

Framework-owned columns are:

```text
entity_id
entity_type
relative_path
created_at
availability_status
claimed_by
```

Applications can extend the index with selected metadata fields.

Example:

```python
index_schema = {
    "color": "TEXT",
    "length_mm": "REAL",
    "width_mm": "REAL",
    "thickness_mm": "REAL",
    "area_mm2": "REAL",
}
```

Supported SQLite types are:

```text
TEXT
INTEGER
REAL
BLOB
```

Application schemas cannot redefine framework-owned columns.

---

# Canonical Metadata vs Indexed Metadata

Entity metadata and indexed metadata serve different purposes.

Suppose an entity is created with:

```python
metadata={
    "color": "brown",
    "length_mm": 1200.0,
    "species": "pine",
}
```

and the index schema is:

```python
{
    "color": "TEXT",
    "length_mm": "REAL",
}
```

The canonical `entity.json` retains the complete metadata dictionary:

```json
{
  "metadata": {
    "color": "brown",
    "length_mm": 1200.0,
    "species": "pine"
  }
}
```

The SQLite database indexes only:

```text
color
length_mm
```

`species` remains canonical entity metadata but is not queryable through `query_entities()`.

Conceptually:

```text
entity.json
    │
    └── complete canonical metadata

entities.db
    │
    └── selected searchable projection
```

---

# `entity_path()`

```python
entity_manager.entity_path(
    entity_id: str,
) -> Path
```

Returns the operational path where a new entity with that ID belongs under the manager's current entry.

```text
<entry>/<entity_id>
```

The entity does not need to exist.

Entity IDs must be valid single directory names.

---

# Creating an Entity

## `create_entity()`

```python
entity_manager.create_entity(
    entity_id: str,
    entity_type: str,
    metadata: dict | None = None,
) -> EntityPaths
```

Example:

```python
entity = entity_manager.create_entity(
    entity_id="material_001",
    entity_type="material",
    metadata={
        "length_mm": 1200.0,
        "width_mm": 180.0,
    },
)
```

Creation performs:

```text
validate identity
      │
      ▼
create entity directory
      │
      ▼
write entity.json
      │
      ▼
register entity in entities.db
      │
      ▼
return EntityPaths
```

New entities begin as:

```text
availability_status = available
claimed_by = null
```

---

# Entity Manifest

A newly created entity contains:

```text
entity.json
```

with data equivalent to:

```json
{
  "entity_id": "material_001",
  "entity_type": "material",
  "created_at": "2026-01-01T10:00:00",
  "availability_status": "available",
  "claimed_by": null,
  "metadata": {
    "length_mm": 1200.0,
    "width_mm": 180.0
  }
}
```

This manifest is the canonical entity-local metadata/state representation.

---

# Entity Artifacts

The framework creates the entity directory and `entity.json`.

Applications may add their own files:

```text
material_001/
├── entity.json
├── image.jpg
├── measurements.json
├── model.obj
└── ...
```

`EntityManager` does not define or register those artifact filenames.

The meaning and format of additional files remain application-specific.

---

# Entity Registration Timing

`create_entity()` writes the entity manifest and registers the entity in the SQLite index before returning.

Application-specific artifacts are normally written afterward by application code.

Therefore:

```text
create_entity()
      │
      ▼
entity becomes registered/queryable
      │
      ▼
application may write additional artifacts
```

The framework currently does not provide an atomic staging/finalization mechanism covering application-defined artifact creation.

Applications that require such semantics must account for this boundary.

---

# `exists()`

```python
entity_manager.exists(
    entity_id: str,
) -> bool
```

Checks whether the entity ID is registered in the workspace SQLite index.

This is a registration check rather than a filesystem scan.

---

# `load_entity()`

```python
entity_manager.load_entity(
    entity_id: str,
) -> EntityPaths
```

Locates a registered entity through the workspace index.

Resolution is:

```text
entity_id
    │
    ▼
entities.db
    │
    ▼
relative_path
    │
    ▼
workspace root
    │
    ▼
entity directory
```

The method then verifies that the entity directory and `entity.json` exist.

Because lookup uses the workspace-level database, the entity can belong to another entry in the same workspace.

---

# `list_entities()`

```python
entity_manager.list_entities(
    entity_type: str | None = None,
) -> list[EntityPaths]
```

Returns registered entities ordered by entity ID.

Without a type:

```python
entities = entity_manager.list_entities()
```

all registered entities are considered.

With:

```python
entities = entity_manager.list_entities(
    entity_type="material",
)
```

only that entity type is returned.

Like `load_entity()`, this operates through the workspace-level index rather than only the manager's current entry.

---

# Entity Availability

Entities have three framework-defined availability states:

```text
available
claimed
unavailable
```

The normal lifecycle is:

```text
AVAILABLE
    │
    │ claim_entity()
    ▼
CLAIMED
    │
    ├── release_entity()
    │       │
    │       ▼
    │   AVAILABLE
    │
    └── mark_unavailable()
            │
            ▼
       UNAVAILABLE
```

Availability state is persisted in both:

```text
entity.json
entities.db
```

---

# `claim_entity()`

```python
entity_manager.claim_entity(
    entity_id: str,
    claimed_by: str,
) -> EntityPaths
```

Claims an available entity for one consumer.

Example:

```python
entity_manager.claim_entity(
    entity_id="material_001",
    claimed_by="consumer_01",
)
```

The transition is:

```text
available
    │
    ▼
claimed
```

and:

```text
claimed_by = "consumer_01"
```

The SQLite update only succeeds if the entity is currently available.

Attempting to claim a non-available entity raises `RuntimeError`.

---

# `release_entity()`

```python
entity_manager.release_entity(
    entity_id: str,
    claimed_by: str,
) -> EntityPaths
```

Returns a claimed entity to the available pool.

The caller must match the current claimant.

```text
claimed
    │
    ▼
available

claimed_by
    │
    ▼
null
```

If the entity is not claimed by the supplied consumer, `RuntimeError` is raised.

---

# `mark_unavailable()`

```python
entity_manager.mark_unavailable(
    entity_id: str,
    claimed_by: str,
) -> EntityPaths
```

Marks a claimed entity as unavailable.

The caller must be the current claimant.

```text
claimed
    │
    ▼
unavailable

claimed_by
    │
    ▼
null
```

This can represent an entity that has been consumed, removed from circulation, or otherwise made unavailable according to application semantics.

---

# `set_availability()`

```python
entity_manager.set_availability(
    entity_id: str,
    availability_status: str,
) -> EntityPaths
```

Explicitly overrides availability.

This method is intended for:

```text
administration
testing
simulation
```

Accepted states are only:

```text
available
unavailable
```

It does not manually set an entity to `claimed`.

Manual availability overrides clear `claimed_by`.

---

# Querying Entities

## `query_entities()`

```python
entity_manager.query_entities(
    filters: dict | None = None,
) -> list[EntityPaths]
```

Queries the workspace-level entity index.

Without filters:

```python
entities = entity_manager.query_entities()
```

all valid registered entities are returned.

Filters can reference:

```text
framework-owned columns
        +
application-defined indexed columns
```

Multiple filters are combined with logical `AND`.

---

# Simple Equality Queries

Example:

```python
entities = entity_manager.query_entities(
    filters={
        "entity_type": "material",
        "availability_status": "available",
        "color": "brown",
    }
)
```

Conceptually:

```text
entity_type = material
        AND
availability_status = available
        AND
color = brown
```

---

# Comparison Queries

Supported operators are:

| Operator | Meaning |
|---|---|
| `eq` | Equal |
| `ne` | Not equal |
| `gt` | Greater than |
| `gte` | Greater than or equal |
| `lt` | Less than |
| `lte` | Less than or equal |

Example:

```python
entities = entity_manager.query_entities(
    filters={
        "length_mm": {
            "gte": 1200.0,
        },
        "width_mm": {
            "gte": 180.0,
        },
    }
)
```

This represents:

```text
length_mm >= 1200
        AND
width_mm >= 180
```

---

# Combined Selection Query

A realistic selection can combine framework and application properties:

```python
entities = entity_manager.query_entities(
    filters={
        "entity_type": "material",
        "availability_status": "available",
        "length_mm": {
            "gte": 1200.0,
        },
        "width_mm": {
            "gte": 180.0,
        },
        "thickness_mm": {
            "gte": 35.0,
        },
    }
)
```

The query itself performs the selection.

No separate entity-selection mechanism is required.

---

# NULL Queries

Simple syntax:

```python
{
    "thickness_mm": None,
}
```

means:

```text
thickness_mm IS NULL
```

Explicit syntax:

```python
{
    "thickness_mm": {
        "eq": None,
    }
}
```

also means:

```text
IS NULL
```

while:

```python
{
    "thickness_mm": {
        "ne": None,
    }
}
```

means:

```text
IS NOT NULL
```

`None` cannot be used with:

```text
gt
gte
lt
lte
```

---

# Query Restrictions

Each comparison dictionary must contain exactly one operator.

This is valid:

```python
{
    "length_mm": {
        "gte": 1200.0,
    }
}
```

This is currently invalid:

```python
{
    "length_mm": {
        "gte": 1200.0,
        "lte": 1600.0,
    }
}
```

Multiple independent fields can still be combined in the same query.

Unsupported operators raise `ValueError`.

---

# Only Indexed Properties Are Queryable

Suppose:

```python
metadata={
    "color": "brown",
    "species": "pine",
}
```

but only:

```python
index_schema={
    "color": "TEXT",
}
```

is configured.

This works:

```python
entity_manager.query_entities(
    filters={
        "color": "brown",
    }
)
```

This does not:

```python
entity_manager.query_entities(
    filters={
        "species": "pine",
    }
)
```

because `species` is not indexed.

The metadata can still exist in `entity.json`; it simply cannot be used as a database query field.

---

# Workspace-Wide Entity Discovery

An important distinction is:

```text
EntityManager.entry
      │
      └── determines where create_entity() places NEW entities

EntityManager.workspace
      │
      └── determines the scope of entities.db
```

Consider:

```text
workspace/
├── sensing/
│   └── entry_001/
│       └── entity_A/
│
└── design/
    └── entry_002/
        └── entity_B/
```

Both entities are registered in:

```text
workspace/index/entities.db
```

Therefore an `EntityManager` constructed with a valid entry can discover registered entities throughout the workspace through:

```python
load_entity()
list_entities()
query_entities()
```

The constructor entry is not an implicit query filter.

If an application needs entry-specific results, it must apply that semantic scope outside the current generic query API or through higher-level application logic.

---

# Index Persistence

The entity database persists independently of the Python `EntityManager` instance.

For example:

```text
EntityManager created
      │
      ▼
entities registered
      │
      ▼
process ends
      │
      ▼
new EntityManager created
      │
      ▼
same entities remain queryable
```

Application-defined index columns are also persisted.

When a manager is reconstructed with an index schema, missing declared columns are added to the existing table.

If a declared column already exists with an incompatible SQLite type, construction raises `ValueError`.

---

# Example: Runtime-Oriented Workspace

A project that does not require indexed entities can stop at the entry level.

Create a workspace:

```python
from framework.workspace import (
    init_workspace,
    DomainManager,
    EntryManager,
)

workspace = init_workspace(
    project_root="/path/to/project",
    workspace_name="session_001",
    layout={},
)
```

Create a domain and entry:

```python
domain_manager = DomainManager(
    workspace=workspace,
)

processing = domain_manager.ensure_domain(
    "processing"
)

entry_manager = EntryManager(
    domain=processing,
)

entry = entry_manager.ensure_entry(
    "run_001"
)
```

Application code can then use the entry as its persistent context:

```python
state_path = (
    entry.root
    / "processing_state.json"
)

output_directory = (
    entry.root
    / "outputs"
)
```

The resulting structure may be:

```text
workspace/
├── workspace.json
└── processing/
    ├── domain.json
    └── run_001/
        ├── entry.json
        ├── processing_state.json
        └── outputs/
```

Any runtime query against those files or manifests is implemented by application logic.

No entity database is required.

---

# Example: Indexed Entity Workspace

Create a workspace:

```python
from framework.workspace import (
    init_workspace,
)

workspace = init_workspace(
    project_root="/path/to/project",
    workspace_name="session_001",
    layout={},
)
```

Create a domain:

```python
from framework.workspace import (
    DomainManager,
)

domain_manager = DomainManager(
    workspace=workspace,
)

domain = domain_manager.ensure_domain(
    "sensing"
)
```

Create an entry:

```python
from framework.workspace import (
    EntryManager,
)

entry_manager = EntryManager(
    domain=domain,
)

entry = entry_manager.ensure_entry(
    "entry_001"
)
```

Create the entity manager:

```python
from framework.workspace import (
    EntityManager,
)

entity_manager = EntityManager(
    workspace=workspace,
    entry=entry,
    index_schema={
        "length_mm": "REAL",
        "width_mm": "REAL",
        "thickness_mm": "REAL",
    },
)
```

Create an entity:

```python
entity = entity_manager.create_entity(
    entity_id="material_001",
    entity_type="material",
    metadata={
        "length_mm": 1500.0,
        "width_mm": 200.0,
        "thickness_mm": 40.0,
    },
)
```

The structure becomes:

```text
workspace/
├── workspace.json
├── index/
│   └── entities.db
└── sensing/
    ├── domain.json
    └── entry_001/
        ├── entry.json
        └── material_001/
            └── entity.json
```

Application files can then be written under:

```python
entity.root
```

For example:

```python
result_path = (
    entity.root
    / "result.json"
)
```

Later, suitable entities can be discovered:

```python
suitable = entity_manager.query_entities(
    filters={
        "entity_type": "material",
        "availability_status": "available",
        "length_mm": {
            "gte": 1200.0,
        },
        "width_mm": {
            "gte": 180.0,
        },
    }
)
```

and one can be claimed:

```python
entity_manager.claim_entity(
    entity_id=suitable[0].entity_id,
    claimed_by="consumer_01",
)
```

---

# Workspace and Communication

The workspace framework and communication framework solve different problems.

Workspace answers questions such as:

```text
What persistent workspace is active?

What domains and entries exist?

Where should operational data be stored?
```

When the optional entity layer is used, it additionally answers:

```text
What registered entities exist?

What indexed properties do they have?

Which entities are available?
```

Communication answers:

```text
What distributed action exists?

Which agent claims it?

Has execution started?

Has execution finished?
```

Conceptually:

```text
COMMUNICATION
     │
     │ coordinates distributed operations
     ▼
APPLICATION
     │
     │ interprets project semantics
     ▼
WORKSPACE
     │
     ├── runtime/application data
     │
     └── optional indexed entities
```

Neither framework requires the other to define its internal model.

For distributed communication details, see:

[`../communication/README.md`](../communication/README.md)

---

# Workspace and Orchestration

Orchestration determines which work becomes available next.

Workspace provides the persistent context used by the application performing that work.

```text
ORCHESTRATION
      │
      ▼
distributed Action
      │
      ▼
application operation
      │
      ▼
WORKSPACE
      │
      ├── runtime/application data
      │
      └── optional entities
```

The generic orchestration framework does not directly manipulate workspace entities or application runtime data.

For orchestration details, see:

[`../orchestration/README.md`](../orchestration/README.md)

---

# Public API

The supported package-level imports are:

```python
from framework.workspace import (
    DirectoryManager,
    WorkspacePaths,
    init_workspace,
    load_workspace,
    DomainManager,
    DomainPaths,
    EntryManager,
    EntryPaths,
    EntityManager,
    EntityPaths,
)
```

The API can be understood in two layers:

| Layer | Object | Purpose |
|---|---|---|
| Core | `DirectoryManager` | Manage a project-defined directory layout. |
| Core | `WorkspacePaths` | Represent paths belonging to one workspace. |
| Core | `init_workspace` | Create or initialize a persistent workspace. |
| Core | `load_workspace` | Load an existing workspace. |
| Core | `DomainManager` | Create, load, and discover workspace domains. |
| Core | `DomainPaths` | Represent paths belonging to one domain. |
| Core | `EntryManager` | Create, load, and discover entries within a domain. |
| Core | `EntryPaths` | Represent paths belonging to one entry. |
| Optional entity layer | `EntityManager` | Create, register, discover, query, and manage persistent entities. |
| Optional entity layer | `EntityPaths` | Represent paths belonging to one persistent entity. |

Private validation, manifest-writing, SQLite initialization, and state-synchronization helpers are implementation details and are not part of the public API.

---

# Summary

The core workspace framework establishes:

```text
Workspace
    ↓
Domain
    ↓
Entry
```

This is the generic persistent organizational hierarchy.

From that common foundation, an application can choose how its operational data are represented and discovered:

```text
                         ENTRY
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       runtime-oriented            entity-oriented
        application                 application
              │                         │
              ▼                         ▼
     application-specific          EntityManager
     manifests / state /               │
     files / stores                entity.json
                                        +
                                  entities.db
```

The separation is therefore:

```text
Workspace / Domain / Entry
    │
    └── generic persistent organization

runtime/application data
    │
    └── application-defined resolution

EntityManager
    │
    └── optional persistent indexed-object model
```

For entity-oriented applications, discovery operates at workspace scope:

```text
Entity directories
       │
       ├── canonical entity.json
       │
       ▼
workspace/index/entities.db
       │
       ▼
EntityManager.query_entities()
```

For runtime-oriented applications:

```text
Workspace / Domain / Entry
       │
       ▼
application manifests / state / files
       │
       ▼
application-specific runtime resolution
```

This allows the same workspace framework to support both runtime-driven workflows and database-indexed entity workflows without forcing either data model onto the other.