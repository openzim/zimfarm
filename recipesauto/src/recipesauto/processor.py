from typing import Any

import requests
import yaml

from recipesauto.constants import logger
from recipesauto.context import Context
from recipesauto.definition import Definition

context = Context.get()


class Processor:

    def run(self):

        logger.info(f"Managing recipes for {context.set} set")
        if context.push:
            logger.warning("Changes will be pushed to the Zimfarm")
        else:
            logger.info("Dry-run, no changes will be made")

        input("Press Enter to continue...")

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

        if context.set == "ted":
            import recipesauto.ted as setmodule
        else:
            raise Exception(f"Unsupported set: {context.set}")

        self.recipe_tag = setmodule.get_recipe_tag()

        existing_recipe_names = self.get_existing_recipes()

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

        self.create_new_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

        self.maintain_existing_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

        self.delete_obsolete_recipes(
            expected_recipes=expected_recipes,
            existing_recipe_names=existing_recipe_names,
        )

    def create_new_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
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
                # manual at creation
                # /!\ beware that it means that if you run this tool twice in a /!\
                # /!\  row, second run will erase these "on-creation" settings  /!\
                input("Press Enter to really create this recipe...")

    def patch_dictionary(
        self, existing_dict: dict[str, Any], patch_dict: dict[str, Any]
    ):
        for key, value in patch_dict.items():
            if key in existing_dict and isinstance(value, dict):
                self.patch_dictionary(existing_dict[key], patch_dict[key])
            else:
                existing_dict[key] = value

    def _get_recipe_overrides(self, recipe_name: str) -> dict[str, Any] | None:
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

    def maintain_existing_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
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
                    self.patch_dictionary(expected_recipe, override["overrides"])
                changes = {}
                current_recipe = self.get_current_recipe(expected_recipe["name"])
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
                    input("Press Enter to really update this recipe...")
                    self.patch_existing_recipe(expected_recipe["name"], changes)
                    logger.info("Recipe updated successfully")

    def patch_existing_recipe(self, recipe_name: str, changes: dict[str, Any]):
        response = requests.patch(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json=changes,
        )
        response.raise_for_status()

    def delete_obsolete_recipes(
        self, expected_recipes: list[dict[str, Any]], existing_recipe_names: list[str]
    ):
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
                input("Press Enter to really delete this recipe...")
                self.delete_existing_recipe(recipe)

    def delete_existing_recipe(self, recipe_name: str):
        response = requests.delete(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        response.raise_for_status()

    def get_existing_recipes(self) -> list[str]:

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

    def get_current_recipe(self, recipe_name: str) -> dict[str, Any]:

        response = requests.get(
            self.get_zf_url(f"/schedules/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_zf_url(self, path: str):
        return "/".join(
            [context.zimnfarm_api_url, path[1:] if path[0] == "/" else path]
        )

    def get_zf_headers(self):
        return {
            "Authorization": f"Token {self.zf_access_token}",
            "Content-type": "application/json",
        }

    def get_zf_token(self):
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
