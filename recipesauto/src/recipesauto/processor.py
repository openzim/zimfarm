import copy
from typing import Any

import requests
import yaml

from recipesauto.constants import logger
from recipesauto.context import Context

context = Context.get()


class Processor:

    def run(self):
        """Run the tool allowing to create / maintain Zimfarm recipes automatically"""

        logger.info(f"Managing recipes for {context.kind} kind")
        if context.push:
            logger.warning("Changes will be pushed to the Zimfarm")
        else:
            logger.info("Dry-run, no changes will be made")

        if input("Do you want to continue? [y/N]").upper() != "Y":
            return

        if context.overrides.exists():
            self.overrides = yaml.safe_load(context.overrides.read_text())
            if "overrides" not in self.overrides:
                self.overrides["overrides"] = []
            if "do_not_create" not in self.overrides:
                self.overrides["do_not_create"] = []
            if "do_not_update" not in self.overrides:
                self.overrides["do_not_update"] = []
            if "do_not_delete" not in self.overrides:
                self.overrides["do_not_delete"] = []
        else:
            self.overrides = {
                "overrides": [],
                "do_not_create": [],
                "do_not_update": [],
                "do_not_delete": [],
            }

        logger.info("Getting Zimfarm authorization")
        self.get_zf_token()

        if context.kind == "ted":
            import recipesauto.ted as setmodule
        elif context.kind == "devdocs":
            import recipesauto.devdocs as setmodule
        else:
            raise Exception(f"Unsupported kind: {context.kind}")

        self.recipe_tag = setmodule.get_recipe_tag()

        existing_recipe_names = self._list_zf_recipes()

        logger.info(f"{len(existing_recipe_names)} recipes already exist in ZF")
        logger.debug(",".join(existing_recipe_names))

        expected_recipes = setmodule.get_expected_recipes()

        logger.info(f"{len(expected_recipes)} recipes expected to exist in ZF")
        logger.debug(
            ",".join(
                sorted(expected_recipe["name"] for expected_recipe in expected_recipes)
            )
        )

        logger.info(
            f'{len(self.overrides["do_not_create"])} recipes overriden for no create'
        )
        for recipe in self.overrides["do_not_create"]:
            logger.info(f"- {recipe}")
        logger.info(
            f'{len(self.overrides["do_not_update"])} recipes overriden for no update'
        )
        for recipe in self.overrides["do_not_update"]:
            logger.info(f"- {recipe}")
        logger.info(
            f'{len(self.overrides["do_not_delete"])} recipes overriden for no delete'
        )
        for recipe in self.overrides["do_not_delete"]:
            logger.info(f"- {recipe}")
        logger.info(
            f'{len(self.overrides["overrides"])} recipes overriden for settings'
        )
        for recipe in self.overrides["overrides"]:
            logger.info(f'- {recipe["name"]}')

        self._create_new_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

        self._maintain_existing_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

        self._delete_obsolete_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

    def _create_new_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
        """Phase where we create the new recipes"""
        recipes_to_create = [
            recipe
            for recipe in expected_recipes
            if recipe["name"]
            not in [*existing_recipe_names, *self.overrides["do_not_create"]]
        ]
        if len(recipes_to_create) == 0:
            logger.info("No recipe to create")
        else:
            if context.push:
                logger.info(f"Creating automatically {len(recipes_to_create)} recipes:")
            else:
                logger.info(
                    f"{len(recipes_to_create)} recipes would have been created:"
                )
            for recipe in recipes_to_create:
                logger.info(f'- {recipe["name"]}')
                if not context.push:
                    continue
                # automatically set warehouse_path to /.hidden/dev and periodicity to
                # manually at creation
                # /!\ beware that it means that if you run this tool twice in a /!\
                # /!\  row, second run will erase these "on-creation" settings  /!\

                if (
                    input("Do you really want to create this recipe? [y/N]").upper()
                    != "Y"
                ):
                    continue
                self._create_recipe_on_zf(recipe)
                logger.info("Recipe created successfully")

    def _create_recipe_on_zf(self, recipe: dict[str, Any]):
        """Really create the recipe on the Zimfarm"""
        patched_recipe = copy.deepcopy(recipe)
        patched_recipe["config"]["warehouse_path"] = "/.hidden/dev"
        patched_recipe["periodicity"] = "manually"
        response = requests.post(
            self.get_zf_url("/schedules/"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json=recipe,
        )
        response.raise_for_status()

    def _patch_dictionary(
        self, existing_dict: dict[str, Any], patch_dict: dict[str, Any]
    ):
        """Small utility function to patch only leaf values of a dictionnary"""
        for key, value in patch_dict.items():
            if key in existing_dict and isinstance(value, dict):
                self._patch_dictionary(existing_dict[key], patch_dict[key])
            else:
                existing_dict[key] = value

    def _get_recipe_overrides(self, recipe_name: str) -> dict[str, Any] | None:
        """Get the overriden values for a given recipes"""
        matches = [
            override
            for override in self.overrides["overrides"]
            if override["name"] == recipe_name
        ]
        if len(matches) == 0:
            return None
        elif len(matches) > 1:
            raise Exception(f"Too many overrides found for {recipe_name}")
        else:
            return matches[0]

    def _maintain_existing_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
        """Phase where we maintain already existing recipes"""
        recipes_to_maintain = [
            recipe
            for recipe in expected_recipes
            if recipe["name"] in existing_recipe_names
            and recipe["name"] not in self.overrides["do_not_update"]
        ]
        if len(recipes_to_maintain) == 0:
            logger.info("No recipe to maintain")
        else:
            if context.push:
                logger.info(
                    f"Maintaining automatically {len(recipes_to_maintain)} recipes:"
                )
            else:
                logger.info(
                    f"{len(recipes_to_maintain)} recipes would have been maintained:"
                )
            for expected_recipe in recipes_to_maintain:
                logger.info(f'- {expected_recipe["name"]}')
                if override := self._get_recipe_overrides(expected_recipe["name"]):
                    logger.debug(f'Overriding config with {override["overrides"]}')
                    self._patch_dictionary(expected_recipe, override["overrides"])
                changes = {}
                current_recipe = self._get_recipe_definition_on_zf(
                    expected_recipe["name"]
                )
                for current_recipe_key, current_recipe_value in current_recipe.items():
                    if current_recipe_key in [
                        "config",
                        "duration",
                        "most_recent_task",
                        "notification",
                        "is_requested",
                    ]:
                        continue
                    expected_value = expected_recipe[current_recipe_key]
                    if current_recipe_value == expected_value:
                        continue
                    logger.info(
                        f"{current_recipe_key}: {current_recipe_value} => "
                        f"{expected_value}"
                    )
                    changes[current_recipe_key] = expected_value
                for current_recipe_key, current_recipe_value in current_recipe[
                    "config"
                ].items():
                    if current_recipe_key in [
                        "command",
                        "mount_point",
                        "str_command",
                    ]:
                        continue
                    expected_value = expected_recipe["config"][current_recipe_key]
                    if current_recipe_value == expected_value:
                        continue
                    if current_recipe_key != "flags":
                        logger.info(
                            f"config.{current_recipe_key}: {current_recipe_value} => "
                            f"{expected_value}"
                        )
                    else:
                        logger.info("Flags have changed:")
                        current_flags = set(current_recipe_value.items())
                        expected_flags = set(expected_recipe["config"]["flags"].items())
                        if new_keys := expected_flags - current_flags:
                            logger.info(f"Added keys: {new_keys}")
                        if previous_keys := current_flags - expected_flags:
                            logger.info(f"Removed keys: {previous_keys}")
                    changes[current_recipe_key] = expected_value
                if changes and context.push:
                    if (
                        input("Do you really want to update this recipe? [y/N]").upper()
                        != "Y"
                    ):
                        continue
                    self._patch_recipe_on_zf(expected_recipe["name"], changes)
                    logger.info("Recipe updated successfully")

    def _patch_recipe_on_zf(self, recipe_name: str, changes: dict[str, Any]):
        """Really patch a recipe on the Zimfarm"""
        response = requests.patch(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json=changes,
        )
        response.raise_for_status()

    def _delete_obsolete_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
        """Phase where we delete obsolete recipes"""
        recipes_to_delete = [
            existing_recipe_name
            for existing_recipe_name in existing_recipe_names
            if not any(
                1 if recipe["name"] == existing_recipe_name else 0
                for recipe in expected_recipes
            )
            and existing_recipe_name not in self.overrides["do_not_delete"]
        ]
        if len(recipes_to_delete) == 0:
            logger.info("No recipe to delete")
        else:
            if context.push:
                logger.info(f"Deleting automatically {len(recipes_to_delete)} recipes:")
            else:
                logger.info(
                    f"{len(recipes_to_delete)} recipes would have been deleted:"
                )
            for recipe in recipes_to_delete:
                logger.info(f"- {recipe}")
                if not context.push:
                    continue
                if (
                    input("Do you really want to delete this recipe? [y/N]").upper()
                    != "Y"
                ):
                    continue
                self._delete_recipe_on_zf(recipe)
                logger.info("Recipe deleted successfully")

    def _delete_recipe_on_zf(self, recipe_name: str):
        """Really delete a recipe from Zimfarm"""
        response = requests.delete(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        response.raise_for_status()

    def _list_zf_recipes(self) -> list[str]:
        """Get a list of existing recipes on zimfarm matching our set"""

        skip = 0
        per_page = 200

        schedule_names: list[str] = []
        while True:
            response = requests.get(
                self.get_zf_url(
                    f"/schedules/?limit={per_page}&skip={skip}&tag={self.recipe_tag}"
                ),
                headers=self.get_zf_headers(),
                timeout=context.http_timeout,
            )
            response.raise_for_status()

            schedules = response.json()
            schedule_names.extend(schedule["name"] for schedule in schedules["items"])

            if (
                schedules["meta"]["limit"] + schedules["meta"]["skip"]
                < schedules["meta"]["count"]
            ):
                skip += per_page
            else:
                break

        return sorted(schedule_names)

    def _get_recipe_definition_on_zf(self, recipe_name: str) -> dict[str, Any]:
        """Get the recipe details on zimfarm"""

        response = requests.get(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_zf_url(self, path: str):
        """Build full Zimfarm URL from a path"""
        return "/".join([context.zimfarm_api_url, path[1:] if path[0] == "/" else path])

    def get_zf_headers(self):
        """Build zimfarm headers"""
        return {
            "Authorization": f"Token {self.zf_access_token}",
            "Content-type": "application/json",
        }

    def get_zf_token(self):
        """Authenticate and get zimfarm tokens"""
        req = requests.post(
            url=self.get_zf_url("/auth/authorize"),
            headers={
                "username": context.zimfarm_username,
                "password": context.zimfarm_password,
                "Content-type": "application/json",
            },
            timeout=context.http_timeout,
        )
        req.raise_for_status()
        self.zf_access_token = req.json().get("access_token")
        self.zf_refresh_token = req.json().get("refresh_token")
