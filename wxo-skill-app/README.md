# Example for wxo skill app

## Requirements
- Python 3.11

## Setup Instructions

### Deploy the wxo skill app to Code Engine

1. [Create a project](https://cloud.ibm.com/docs/codeengine?topic=codeengine-manage-project#create-a-project) of Code Engine.
2. [Deploy the application](https://cloud.ibm.com/docs/codeengine?topic=codeengine-app-source-code) from this repository source code.
   - In **Create application**, click **Specify build details** and enter the following:
      - Source
         - Code repo URL: ex. `https://github.com/IBM/CodeEngine`
         - Code repo access: `None`
         - Branch name: `main`
         - Context directory: `wxo-skill-app`
      - Strategy
         - Strategy: `Dockerfile`
      - Output
         - Enter your container image registry information.
   - Open **Environment variables (optional)**, and add environment variables.
   - We recommend setting **Min number of instances** to `1`.
3. Confirm that the application status changes to **Ready**.

### Run on your local

1. `python main.py`