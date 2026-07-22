# Database Design & Schema Specification - Nexora AI

Nexora AI uses a multi-tier database model:
- **PostgreSQL**: Primary transactional, relational, and structured analytical database.
- **ChromaDB**: Native vector store for semantic similarity and metadata retrieval.
- **Redis**: In-memory caching, task state tracking, and rate limiting.

---

## 1. PostgreSQL Schema (SQLAlchemy Models)

### 1.1 `tenants` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Unique organization identifier |
| `name` | VARCHAR(255) | NOT NULL | Company Name |
| `slug` | VARCHAR(255) | UNIQUE, NOT NULL | Unique subdomain / URL slug |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration timestamp |

### 1.2 `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | User identifier |
| `tenant_id` | UUID | Foreign Key (`tenants.id`) | Belongs to tenant |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| `role` | VARCHAR(50) | NOT NULL | `CEO`, `Director`, `Manager`, `Employee` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | User creation timestamp |

### 1.3 `datasets` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Dataset identifier |
| `tenant_id` | UUID | Foreign Key (`tenants.id`) | Belongs to tenant |
| `name` | VARCHAR(255) | NOT NULL | Dataset label |
| `department` | VARCHAR(50) | NOT NULL | `sales`, `finance`, `hr`, `marketing`, `operations` |
| `row_count` | INTEGER | NOT NULL | Total records ingested |
| `file_path` | VARCHAR(500) | NOT NULL | Storage path |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Upload timestamp |

### 1.4 `dataset_schemas` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Schema record ID |
| `dataset_id` | UUID | Foreign Key (`datasets.id`) | Target dataset |
| `columns_metadata` | JSONB | NOT NULL | Auto-detected column names, data types, null counts |
| `kpis_extracted` | JSONB | NOT NULL | Computed key metrics (Totals, Averages, Variances) |
| `trends_detected` | JSONB | NOT NULL | Time series metrics & growth rates |

### 1.5 `sentinel_alerts` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Alert identifier |
| `tenant_id` | UUID | Foreign Key (`tenants.id`) | Target tenant |
| `metric_name` | VARCHAR(255) | NOT NULL | Affected metric |
| `severity` | VARCHAR(50) | NOT NULL | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `target_role` | VARCHAR(50) | NOT NULL | Recipient role (`Employee`, `Manager`, `Director`, `CEO`) |
| `title` | VARCHAR(255) | NOT NULL | Alert summary |
| `description` | TEXT | NOT NULL | Root cause analysis & details |
| `acknowledged` | BOOLEAN | DEFAULT FALSE | Review status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Alert timestamp |
