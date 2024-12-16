## Recipes Auto

This project is aimed at automatically creating and maintaining a group of Zimfarm recipes.

First uses cases are for StackExchange and TED recipes, for which we want one recipe per StackExchange domain / TED topic. We know other will come (we already have shamela.ws recipes waiting in the pipe, libretexts.org would benefit from this as well, devdocs, ...).

The goals of this project are:

- easily create many recipes following the same "model", but with specificities for all of them
- easily maintain these recipes over time
  - detect missing recipes and create them as needed (typically a new StackExchange website or a new TED topic appeared)
  - delete obsolete ones (typically a StackExchange website or TED topic is abandonned)
  - update parameters as needed (e.g. change all recipes periodicity, ...)
- source data for these recipes from "source of truth", typically local / remote "data" files or APIs (potentially mixing data from multiple sources)
- easy to configure when new project arise, reusing building blocks
- two modes: "dry-run" (to check what is going to happen) and "apply" (to really apply it)
- easily handle recipe configuration exceptions (because there is always exceptions)
- write everything in Python for easy maintainability

Out of scope for now:

- GUI
- permission management

The dry-run mode will allow to:

- easily observe what is going to be applied without risking breaking the configuration
- modify the configuration / code until the plan is accurate

Sample usage:

```
recipesauto --zimfarm-username benoit --zimfarm-password $ZIMFARM_PASS --values ted_optim_url=$TED_OPTIM_URL ted
```
