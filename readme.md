Project name: Drone Pipeline Automation
Project PI: Helge Aasen
Project colaborators: Valerie Schneider

Link to confluence page: https://eoa-team.atlassian.net/wiki/spaces/EOAintern/pages/686359066/026_DPA_DronePipelineAutomation
Link to github repo: https://github.com/EOA-team/026_dpa


## Changes

**2025-12-15**
- Environment upgraded to Python 3.12.12
- Added working scripts for 019_Hypercover (Valerie Master Thesis)

For detailed documentation, see [026_Rolling_Documentation](https://eoa-team.atlassian.net/wiki/spaces/EOAintern/pages/686359066/026_Rolling_Documentation#Intermediate-Process-Documentation)


# Unit Tests
python -m pytest
# Code Style
pylint code
# Static Type Checking 
mypy code 

# Conda Environment: Save and Load Commands

This guide shows how to save your Conda environment to a YAML file, recreate it, and list all environments.

---

## 1. Activate Your Environment

Activate your Conda environment using:

```bash
conda activate 026_dpa
```

Replace `026_dpa` with your environment name if different.

---

## 2. Export Environment to YAML

Export your current environment to a YAML file:

```bash
conda env export --no-builds > environment.yml
```

This will create `environment.yml` containing all packages and dependencies.

---

## 3. Create Environment from YAML

To recreate the environment on the same or another machine:

```bash
conda env create -f environment.yml
```

This will create a new Conda environment with the same name and packages as saved.

---

## 4. List All Conda Environments

Verify your environments with:

```bash
conda env list
```

This shows all Conda environments available on your system.

---

### Summary of Commands

```bash
conda activate 026_dpa
conda env export > environment.yml
conda env create -f environment.yml
conda env list
```

This workflow ensures you can save, share, and recreate your Conda environments reliably.