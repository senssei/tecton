# Baseline Architecture Specification & APM Module Design

## 1. Architectural Purpose and Principles

**Tecton** implements **Hexagonal Architecture (Ports and Adapters / Clean Architecture)**, establishing complete decoupling between core analytical domain logic and external repository mechanisms.

The system ensures:
1. A pure, self-contained **Core Domain** completely independent of external API schemas or vendor SDKs.
2. Explicit **Repository Ports** defining inbound and outbound contracts, enabling interchangeable infrastructure adapters (remote Graph APIs, local JSON/YAML files, in-memory test doubles).
3. Deterministic **Analytic Engines** that resolve the critical gaps identified in the adversarial analysis.
4. A unified **CLI Toolchain** and sovereign visual exporters targeting the open **Mermaid** and **Markdown** standards.

---

## 2. Hexagonal Architecture Blueprint

```mermaid
flowchart TD
    subgraph Presentation_Layer["Presentation Layer (Inbound Adapters)"]
        CLI["CLI Commands: tecton apm [list|analyze|export-matrix|patch-time]"]
        MermaidExp["Exporter: Mermaid quadrantChart"]
        MDExp["Exporter: Living Markdown Report"]
    end

    subgraph Application_Layer["Application Layer (Orchestration)"]
        APMService["APMService (Orchestrating Ingestion, Evaluation & Mutations)"]
    end

    subgraph Domain_Layer["Domain Layer (Core Domain & Engines)"]
        TimeEngine["TimeScoringEngine (TIME Classifier)"]
        RedundancyEngine["RedundancyDetectionEngine (Weighted Jaccard)"]
        LifecycleVal["LifecycleValidator (Chronological Consistency)"]
        DomainModels["Models: Application, Lifecycle, Suitability, RedundancyCluster"]
    end

    subgraph Infrastructure_Layer["Infrastructure Layer (Outbound Adapters)"]
        RepoPort["<<interface>> ArchitectureRepositoryPort"]
        GraphAdapter["GraphQLRepositoryAdapter (Remote Graph API)"]
        MockAdapter["InMemoryRepositoryAdapter (Offline / Testing / CI)"]
        LocalFileAdapter["FileRepositoryAdapter (JSON / YAML / CSV)"]
    end

    CLI --> APMService
    APMService --> Domain_Layer
    APMService --> RepoPort
    RepoPort <|.. GraphAdapter
    RepoPort <|.. MockAdapter
    RepoPort <|.. LocalFileAdapter
    APMService --> MermaidExp
    APMService --> MDExp
```

---

## 3. Core Business Logic & Algorithmic Rules

### A. Gartner TIME Evaluation Framework
Evaluation is determined by two normalized dimensions on a 1.0 – 5.0 scale:
*   **Business Fit (Functional Suitability):** Process coverage, criticality, business user value.
*   **Technical Fit (Technical Suitability):** Architecture quality, maintainability, stability, technical debt.

```
                      High (>= 3.5)
                            ▲
                            │
             TOLERATE       │        INVEST
        (High Business Fit, │   (High Business Fit,
          Low Tech Fit)     │     High Tech Fit)
    ────────────────────────┼────────────────────────► Technical Fit
                            │                        (>= 3.5)
            ELIMINATE       │        MIGRATE
        (Low Business Fit,  │   (Low Business Fit,
          Low Tech Fit)     │     High Tech Fit)
                            │
                            ▼ Low
```

### B. Functional Redundancy Clustering (Weighted Jaccard Metric)
Functional similarity between applications $A_1$ and $A_2$ is computed as:
$$J(A_1, A_2) = w_c \cdot \frac{|C_1 \cap C_2|}{|C_1 \cup C_2|} + w_u \cdot \frac{|U_1 \cap U_2|}{|U_1 \cup U_2|}$$
where:
*   $C_1, C_2$ – sets of realized business capabilities,
*   $U_1, U_2$ – sets of supported user groups or organizational units,
*   $w_c, w_u$ – configurable weights (defaults: $w_c = 0.70, w_u = 0.30$).

Pairs with $J(A_1, A_2) \ge \theta$ (default $\theta = 0.70$) are clustered as functional redundancies with automated rationalization recommendations.

### C. Safety-First Mutation Policy
All mutating commands interacting with repositories operate by default in **`--dry-run`** mode. Permanent updates require explicit `--apply` invocation.

---

## 4. Module Structure and Code Contracts

### A. Core Domain Models (`src/tecton/core/models.py`)
```python
from enum import Enum
from pydantic import BaseModel, Field

class TimeQuadrant(str, Enum):
    INVEST = "INVEST"
    TOLERATE = "TOLERATE"
    MIGRATE = "MIGRATE"
    ELIMINATE = "ELIMINATE"
    UNKNOWN = "UNKNOWN"

class LifecyclePhase(str, Enum):
    PLAN = "plan"
    PHASE_IN = "phaseIn"
    ACTIVE = "active"
    PHASE_OUT = "phaseOut"
    END_OF_LIFE = "endOfLife"

class Application(BaseModel):
    id: str
    name: str
    business_criticality: str | None = None
    functional_suitability: float | None = None
    technical_suitability: float | None = None
    time_classification: TimeQuadrant = TimeQuadrant.UNKNOWN
    current_phase: LifecyclePhase | None = None
    capabilities: list[str] = Field(default_factory=list)
    user_groups: list[str] = Field(default_factory=list)
```

### B. Outbound Repository Port (`src/tecton/adapters/base.py`)
```python
from typing import Any, Protocol

class ArchitectureRepositoryPort(Protocol):
    def fetch_applications(self) -> list[Application]: ...
    def apply_patches(self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True) -> dict[str, Any]: ...
```

### C. Deterministic Analytic Engines (`src/tecton/engines/`)
*   `TimeScoringEngine`: Threshold-driven quadrant classification.
*   `RedundancyDetectionEngine`: Weighted Jaccard set similarity clustering.
*   `LifecycleValidator`: Chronological order and anomaly governance.

### D. Sovereign Visual Exporters (`src/tecton/exporters/`)
*   `MermaidExporter`: Generates clean, native `quadrantChart` Mermaid code.
*   `MarkdownExporter`: Assembles executive living documentation reports.

---

## 5. Verification Strategy
*   **Engine Unit Tests:** Exhaustive parameterized unit tests verifying all quadrants, boundary scores, empty sets, and chronological anomalies.
*   **Adapter Unit Tests:** Offline verification of JSON/YAML hydration and JSON Patch simulation.
*   **Service Integration Tests:** End-to-end orchestration tests auditing portfolios and confirming patch preparation.
*   **CLI Integration Tests:** Automated runner invocation checking output formatting, error handling, and exit codes.
