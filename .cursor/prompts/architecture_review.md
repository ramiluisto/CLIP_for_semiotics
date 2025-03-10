@PROFILE-project-architecture.mdc

Please analyze the current project. I see at least some test files in the root folder, they should probably be somewhere else. Those test files being lost is probably a smell that there has been sloppy work, and you should review the project carefully.

Before starting, make sure that tests pass. Whenever you make changes or move files, make sure that the tests pass and fix any issues until they do.

You are allowed to edit the python files as well if needed, including functionality, but you should mainly focus on getting the structure right. If you edit Python files, remember to apply the @COLLECTION-python.mdc  rules.
