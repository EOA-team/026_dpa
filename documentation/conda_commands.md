# Conda Environment: Create and Update Commands

This guide shows how to create your Conda environment from the YAML file, update it, and list all environments.

---

## 1. Activate Your Environment

Activate your Conda environment using:

```bash
conda activate 026_dpa_py312
```

Replace `026_dpa_py312` with your environment name if different.

---

## 2. Maintain environment.yml by Hand

`environment.yml` lists **only the direct dependencies** of this project (plus `python=3.12`).
Transitive dependencies are resolved by conda at install time and are deliberately not listed.

- Add a package to `environment.yml` when you start importing it in code, then apply with the update command below.
- Do **not** regenerate the file via `conda env export` — it dumps every transitive
  dependency and platform-specific pins, which makes the file unusable as a dependency
  declaration.
- Only pin a version when strictly necessary (e.g. `python=3.12`); otherwise leave packages
  unpinned or use a lower bound (`numpy >= 2.0`).

---

## 3. Create Environment from YAML

To recreate the environment on the same or another machine:

```bash
conda env create -f environment.yml
```

This will create a new Conda environment with the same name and packages as saved.

---
## 4. Update Environment from YAML

To update a conda environment from a YAML file:

```bash
conda env update --file environment.yml --prune
```

---

## 5. List All Conda Environments

Verify your environments with:

```bash
conda env list
```

This shows all Conda environments available on your system.

---

### Summary of Commands

```bash
conda activate 026_dpa_py312
conda env create -f environment.yml
conda env update --file environment.yml --prune
conda env list
```

This workflow keeps `environment.yml` small, platform-independent, and reproducible.