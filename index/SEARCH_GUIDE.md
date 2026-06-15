# Search Guide

Use deterministic search before considering semantic memory.

## Project Start

```bash
python scripts/experience_vault.py search --mode project-start --query "<task terms>"
```

Search order:

1. `runbooks/`
2. `knowledge/`
3. `incidents/`
4. `projects/`

## Incident Recall

```bash
python scripts/experience_vault.py search --mode incident --query "<error terms>"
```

Search order:

1. `incidents/`
2. `knowledge/`
3. `runbooks/`
4. `projects/`

## Promotion

```bash
python scripts/experience_vault.py search --mode promotion --query "<workflow terms>"
```

Search order:

1. `knowledge/`
2. `runbooks/`
3. `incidents/`
4. `projects/`
5. `evals/`

## Applicability

Every hit must be classified as:

- directly applicable
- partially applicable
- not applicable

Do not apply a historical record without checking trigger signals, required inputs, non-applicable cases, environment compatibility, confidence, and recency.

