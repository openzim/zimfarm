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

## Contribute

To create a kind of recipes which are automatically maintained, you need to create a new
module where two methods are implemented:

- `get_recipe_tag` which return the Zimfarm tag (not ZIM tag) which is set on all recipes of this kind
- `get_expected_recipes` which returns a list of recipes, where each recipe is in fact a dict of key, values
  just like it is used to create a new recipe (once transformed into JSON)

The `get_expected_recipes` can source its list of recipes to create from anywhere (local file, online, ...).

You then have to add the new kind of recipes to the `entrypoint.py`:

```
parser.add_argument("kind", choices=["ted", "devdocs"])
```

And add it to the logic loading proper module based on passed kind in `processor.py`:

```
if context.kind == "ted":
    import recipesauto.ted as setmodule
elif context.kind == "devdocs":
    import recipesauto.devdocs as setmodule
else:
    raise Exception(f"Unsupported kind: {context.kind}")
```

The tool then takes care of diffing existing recipes with the list of expected recipes.

Should you need, you can override some values with `overrides.yaml` file:

- add a recipe name to the `do_not_create` list (could obviously be done by tweaking the `get_expected_recipes` function as well)
- add a recipe name to the `do_not_delete` list (typically because the special Zimfarm tag is also attached to this recipe which should not be maintained with this tool)
- tweak (typically temporarily) a recipe configuration with the `overrides` list (also obviously doable with a tweak of the `get_expected_recipes`, but more readable in a YAML file than in code)
