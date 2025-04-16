# lionsentry-python-lamdba-content-generator
lionsentry-python-lamdba-content-generator

# Setting Up a Virtual Environment for Python 3.11

This guide will help you set up a virtual environment using Python 3.11.

---

## Prerequisites
- Ensure Python 3.13 is installed on your system.
- On macOS, you can install it using Homebrew:

```bash
brew install python@3.13
```

Verify the installation:

```bash
python3.13 --version
```

---

## Step 1: Create a Project Directory
Clone the repository and navigate into it:

```bash
git clone git@github.com:Curt-Landry-Ministries/lionsentry-python-lamdba-content-generator.git
cd lionsentry-python-lamdba-content-generator
```

---

## Step 2: Create a Virtual Environment
Create a virtual environment named `venv`:

```bash
python3.13 -m venv venv
```

This will create a directory called `venv` in your project folder.

---

## Step 3: Activate the Virtual Environment
Activate the virtual environment using the following command:

- **macOS/Linux**:

  ```bash
  source venv/bin/activate
  ```

- **Windows (Command Prompt)**:

  ```cmd
  venv\Scripts\activate
  ```

You should see `(venv)` in your terminal prompt, indicating that the virtual environment is active.

---


## Step 4: Install Python Packages
With the virtual environment activated, install Python packages using `pip`. For example:

```bash
pip install -r requirements.txt
```

---

## Step 5: Run the files
Run the python files in virtual env, run:

```bash
python generate_devotional.py
python generate_whyStatement.py
```

---

## Step 6: Deactivate the Virtual Environment
To deactivate the virtual environment, run:

```bash
deactivate
```

## Making changes to the code and uploading to github

Create a new branch before making any changes to the code or files. DO NOT PUSH TO MAIN.

```bash
git checkout -b update/my-new-changes
```

Once your changes are made, add them to the git head:

```bash
git add filename.py filename.txt
```

Create a commit message describing the changes:

```bash
git commit -m "Some message about the code changes"
```

Push to your new branch:

```bash
git push origin update/my-new-changes
```

## Opening a pull request in github.

Navigate to the [repository](https://github.com/Curt-Landry-Ministries/lionsentry-python-lamdba-content-generator) in github. Click on pull requests tab. Click New Pull Request button. Select `update/my-new-changes` as the compare branch and leave the base branch as main.