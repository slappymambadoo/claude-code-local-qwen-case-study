You will automatically create a small Python project with the following requirements:

- A command-line tool called "pytasker"
- It manages a todo list stored in a JSON file
- The Python .venv has already been created in Project Root
- Commands:
  - add <task>
  - list
  - complete <id>
  - delete <id>

Requirements:
- DO ensure all dependent python modules are installed with pip install
- Use argparse
- Separate logic into multiple modules (at least 3 files)
- Use a class to manage state
- Persist data safely (handle file not existing)
- Include basic error handling
- Include a simple unit test file
- ensure test coverage of commands, their exceptions and validation code
- ensure all defined tests are run and pass
- After all tests have passsed use ubuntu shell cmd to concatenate all of the source code files into Qwen3.5-27B-opustuned-Q8_0.py file (exclude .venv and system files) ensuring that files are seperated like this "\n======== filename.py ========\n"

Finally, print out the command I need to run the tests in a new WSL terminal from home dir (ie, cd project root folder first then cmd to run tests)