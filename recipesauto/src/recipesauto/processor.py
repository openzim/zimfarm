# ruff: noqa: PLC0415

import base64
import copy
import hashlib
from http import HTTPStatus
from pathlib import Path
from typing import Any

import requests
import yaml

from recipesauto.constants import logger
from recipesauto.context import Context

context = Context.get()

# marker stored in comments of blobs uploaded by this tool, followed by the sha256 of
# the source content ; needed because Zimfarm converts some blobs (e.g. images to
# PNG) at upload, so the blob checksum is not the checksum of the source content
BLOB_SOURCE_CHECKSUM_MARKER = "source sha256: "


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

        self.blob_flags_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}

        logger.info("Authenticating with zimfarm")
        self.authenticate()
        logger.info("Authenticated with zimfarm")

        if context.kind == "ted":
            import recipesauto.ted as setmodule
        elif context.kind == "devdocs":
            import recipesauto.devdocs as setmodule
        elif context.kind == "freecodecamp":
            import recipesauto.freecodecamp as setmodule
        elif context.kind == "shamela":
            import recipesauto.shamela as setmodule
        elif context.kind == "phet":
            import recipesauto.phet as setmodule
        elif context.kind == "gutenberg":
            import recipesauto.gutenberg as setmodule
        elif context.kind == "stackexchange":
            import recipesauto.stackexchange as setmodule
        elif context.kind == "maps":
            import recipesauto.maps as setmodule
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
            f"{len(self.overrides['do_not_create'])} recipes overridden for no create"
        )
        for recipe in self.overrides["do_not_create"]:
            logger.info(f"- {recipe}")
        logger.info(
            f"{len(self.overrides['do_not_update'])} recipes overridden for no update"
        )
        for recipe in self.overrides["do_not_update"]:
            logger.info(f"- {recipe}")
        logger.info(
            f"{len(self.overrides['do_not_delete'])} recipes overridden for no delete"
        )
        for recipe in self.overrides["do_not_delete"]:
            logger.info(f"- {recipe}")
        logger.info(
            f"{len(self.overrides['overrides'])} recipes overridden for settings"
        )
        for recipe in self.overrides["overrides"]:
            logger.info(f"- {recipe['name']}")

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
            ask_for_confirmation = True
            for recipe in recipes_to_create:
                logger.info(f"- {recipe['name']}")
                if not self._check_blob_sources(recipe):
                    logger.warning(
                        f"Skipping creation of {recipe['name']} since some blob "
                        "sources are not available"
                    )
                    continue
                if not context.push:
                    continue
                if ask_for_confirmation:
                    response = input(
                        "Do you really want to create this recipe? [y/N/a]"
                    ).upper()
                    if response not in ("Y", "A"):
                        continue
                    if response == "A":
                        ask_for_confirmation = False
                created_offliner_flags = self._create_recipe_on_zf(recipe)
                logger.info("Recipe created successfully")
                # blobs can only be uploaded once the recipe exists, so recipe has
                # been created without blob flags, which we now upload
                offliner_flags = copy.deepcopy(recipe["config"]["offliner"])
                self._resolve_blob_flags(
                    recipe_name=recipe["name"],
                    version=recipe["version"],
                    offliner_flags=offliner_flags,
                    current_offliner_flags=created_offliner_flags,
                    upload=True,
                )
                if offliner_flags != created_offliner_flags:
                    self._patch_recipe_on_zf(recipe["name"], {"flags": offliner_flags})
                    logger.info("Recipe blobs uploaded successfully")

    def _create_recipe_on_zf(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Really create the recipe on the Zimfarm

        Blob flags are omitted (except required remote URLs) since blobs can only be
        uploaded once the recipe exists. Returns the offliner flags used at creation.
        """
        patched_recipe = copy.deepcopy(recipe)
        offliner_flags = patched_recipe["config"]["offliner"]
        for flag in self._get_blob_flags(
            offliner_flags["offliner_id"], recipe["version"]
        ):
            source = offliner_flags.get(flag["data_key"])
            if not source:
                continue
            if flag["required"]:
                if isinstance(source, Path):
                    raise Exception(
                        f"Cannot create {recipe['name']} recipe: required "
                        f"{flag['data_key']} flag is a local file, which can only be "
                        "uploaded once recipe exists"
                    )
                continue
            del offliner_flags[flag["data_key"]]
        response = requests.post(
            self.get_zf_url("/recipes"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json=patched_recipe,
        )

        if not HTTPStatus(response.status_code).is_success:
            logger.error(response.text)
        response.raise_for_status()
        return offliner_flags

    def _patch_dictionary(
        self, existing_dict: dict[str, Any], patch_dict: dict[str, Any]
    ):
        """Small utility function to patch only leaf values of a dictionary"""
        for key, value in patch_dict.items():
            if key in existing_dict and isinstance(value, dict):
                self._patch_dictionary(existing_dict[key], value)
            else:
                existing_dict[key] = value

    def _get_recipe_overrides(self, recipe_name: str) -> dict[str, Any] | None:
        """Get the overridden values for a given recipes"""
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
            ask_for_confirmation = True
            for expected_recipe in recipes_to_maintain:
                logger.info(f"- {expected_recipe['name']}")
                if override := self._get_recipe_overrides(expected_recipe["name"]):
                    logger.debug(f"Overriding config with {override['overrides']}")
                    self._patch_dictionary(expected_recipe, override["overrides"])
                changes = {}
                current_recipe = self._get_recipe_definition_on_zf(
                    expected_recipe["name"]
                )
                blob_version = expected_recipe.get("version", current_recipe["version"])
                self._resolve_blob_flags(
                    recipe_name=expected_recipe["name"],
                    version=blob_version,
                    offliner_flags=expected_recipe["config"]["offliner"],
                    current_offliner_flags=current_recipe["config"]["offliner"],
                    upload=False,
                )
                for current_recipe_key, current_recipe_value in current_recipe.items():
                    if current_recipe_key in [
                        # keys handled separately
                        "config",
                        "language",
                        # read-only keys
                        "duration",
                        "most_recent_task",
                        "notification",
                        "is_requested",
                        "is_valid",
                        "id",
                        "teams",
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

                # handle special case of language (read != write)
                current_recipe_value = current_recipe["language"]["code"]
                expected_value = expected_recipe["language"]
                if current_recipe_value != expected_value:
                    logger.info(f"language: {current_recipe_value} => {expected_value}")
                    changes["language"] = expected_value

                # handle special case of config
                for current_recipe_key, current_recipe_value in current_recipe[
                    "config"
                ].items():
                    if current_recipe_key in [
                        "command",
                        "mount_point",
                        "str_command",
                        "artifacts_globs",
                    ]:
                        continue
                    expected_value = expected_recipe["config"][current_recipe_key]
                    if hasattr(current_recipe_value, "items"):
                        keys_to_remove = []
                        for key, value in current_recipe_value.items():
                            if value is None or value == []:
                                keys_to_remove.append(key)
                        for key in keys_to_remove:
                            del current_recipe_value[key]
                    if hasattr(expected_value, "items"):
                        keys_to_remove = []
                        for key, value in expected_value.items():
                            if value is None or value == []:
                                keys_to_remove.append(key)
                        for key in keys_to_remove:
                            del expected_value[key]
                    if current_recipe_value == expected_value:
                        continue
                    if current_recipe_key != "offliner":
                        logger.info(
                            f"config.{current_recipe_key}: {current_recipe_value} => "
                            f"{expected_value}"
                        )
                        changes[current_recipe_key] = expected_value
                    else:
                        logger.info("Flags have changed:")
                        current_flags = set(current_recipe_value.items())
                        expected_flags = set(
                            expected_recipe["config"]["offliner"].items()
                        )
                        if new_keys := expected_flags - current_flags:
                            logger.info(f"Added keys: {new_keys}")
                        if previous_keys := current_flags - expected_flags:
                            logger.info(f"Removed keys: {previous_keys}")
                        # 'offliner' at read time ends up in 'flags' at write time
                        changes["flags"] = expected_value
                if changes and context.push:
                    if ask_for_confirmation:
                        response = input(
                            "Do you really want to update this recipe? [y/N/a]"
                        ).upper()
                        if response not in ("Y", "A"):
                            continue
                        if response == "A":
                            ask_for_confirmation = False
                    if "flags" in changes:
                        # upload blobs which are not yet known, now that we know
                        # recipe will really be updated
                        self._resolve_blob_flags(
                            recipe_name=expected_recipe["name"],
                            version=blob_version,
                            offliner_flags=changes["flags"],
                            current_offliner_flags=current_recipe["config"]["offliner"],
                            upload=True,
                        )
                    self._patch_recipe_on_zf(expected_recipe["name"], changes)
                    logger.info("Recipe updated successfully")

    def _patch_recipe_on_zf(self, recipe_name: str, changes: dict[str, Any]):
        """Really patch a recipe on the Zimfarm"""
        response = requests.patch(
            self.get_zf_url(f"/recipes/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json=changes,
        )
        if not HTTPStatus(response.status_code).is_success:
            logger.error(response.text)
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
            ask_for_confirmation = True
            for recipe in recipes_to_delete:
                logger.info(f"- {recipe}")
                if not context.push:
                    continue
                if ask_for_confirmation:
                    response = input(
                        "Do you really want to delete this recipe? [y/N/a]"
                    ).upper()
                    if response not in ("Y", "A"):
                        continue
                    if response == "A":
                        ask_for_confirmation = False
                self._delete_recipe_on_zf(recipe)
                logger.info("Recipe deleted successfully")

    def _delete_recipe_on_zf(self, recipe_name: str):
        """Really delete a recipe from Zimfarm"""
        response = requests.delete(
            self.get_zf_url(f"/recipes/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        if not HTTPStatus(response.status_code).is_success:
            logger.error(response.text)
        response.raise_for_status()

    def _list_zf_recipes(self) -> list[str]:
        """Get a list of existing recipes on zimfarm matching our set"""

        skip = 0
        per_page = 200

        recipe_names: list[str] = []
        while True:
            response = requests.get(
                self.get_zf_url(
                    f"/recipes/?limit={per_page}&skip={skip}&tag={self.recipe_tag}"
                ),
                headers=self.get_zf_headers(),
                timeout=context.http_timeout,
            )

            if not HTTPStatus(response.status_code).is_success:
                logger.error(response.text)
            response.raise_for_status()

            recipes = response.json()
            recipe_names.extend(recipe["name"] for recipe in recipes["items"])

            if (
                recipes["meta"]["limit"] + recipes["meta"]["skip"]
                < recipes["meta"]["count"]
            ):
                skip += per_page
            else:
                break

        return sorted(recipe_names)

    def _get_recipe_definition_on_zf(self, recipe_name: str) -> dict[str, Any]:
        """Get the recipe details on zimfarm"""

        response = requests.get(
            self.get_zf_url(f"/recipes/{recipe_name}?hide_secrets=False"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        if not HTTPStatus(response.status_code).is_success:
            logger.error(response.text)
        response.raise_for_status()
        return response.json()

    def _get_blob_flags(self, offliner_id: str, version: str) -> list[dict[str, Any]]:
        """Get flags of type blob for a given offliner definition version"""
        cache_key = (offliner_id, version)
        if cache_key not in self.blob_flags_cache:
            response = requests.get(
                self.get_zf_url(f"/offliners/{offliner_id}/{version}"),
                headers=self.get_zf_headers(),
                timeout=context.http_timeout,
            )
            if not HTTPStatus(response.status_code).is_success:
                logger.error(response.text)
            response.raise_for_status()
            self.blob_flags_cache[cache_key] = [
                flag for flag in response.json()["flags"] if flag["type"] == "blob"
            ]
        return self.blob_flags_cache[cache_key]

    def _list_zf_blobs(self, recipe_name: str) -> list[dict[str, Any]]:
        """Get the list of blobs of a recipe on Zimfarm"""
        skip = 0
        per_page = 200

        blobs: list[dict[str, Any]] = []
        while True:
            response = requests.get(
                self.get_zf_url(f"/blobs/{recipe_name}?limit={per_page}&skip={skip}"),
                headers=self.get_zf_headers(),
                timeout=context.http_timeout,
            )
            if not HTTPStatus(response.status_code).is_success:
                logger.error(response.text)
            response.raise_for_status()

            result = response.json()
            blobs.extend(result["items"])

            if (
                result["meta"]["limit"] + result["meta"]["skip"]
                < result["meta"]["count"]
            ):
                skip += per_page
            else:
                break

        return blobs

    def _get_blob_source_content(self, source: str | Path) -> bytes | None:
        """Get content of a blob source, either a local file or a remote URL

        Returns None (and logs a warning) when source is not available.
        """
        try:
            if isinstance(source, Path):
                return source.read_bytes()
            response = self._download_blob_source(source)
        except OSError as exc:  # requests exceptions are OSError as well
            logger.warning(f"Blob source {source} is not available: {exc}")
            return None
        return response.content

    def _download_blob_source(self, source: str) -> requests.Response:
        response = requests.get(
            source,
            headers={
                "User-Agent": (
                    "zimfarm-recipesauto (https://github.com/openzim/zimfarm; "
                    f"contact+crawl@kiwix.org) requests/{requests.__version__}"
                )
            },
            timeout=context.http_timeout,
        )
        response.raise_for_status()
        return response

    def _check_blob_sources(self, recipe: dict[str, Any]) -> bool:
        """Check (and warn about) availability of all recipe blob sources"""
        offliner_flags = recipe["config"]["offliner"]
        all_available = True
        for flag in self._get_blob_flags(
            offliner_flags["offliner_id"], recipe["version"]
        ):
            source = offliner_flags.get(flag["data_key"])
            if source and self._get_blob_source_content(source) is None:
                all_available = False
        return all_available

    def _create_blob_on_zf(
        self,
        *,
        recipe_name: str,
        flag: dict[str, Any],
        source: str | Path,
        content: bytes,
        checksum: str,
    ) -> dict[str, Any]:
        """Upload content as a blob of the recipe"""
        response = requests.post(
            self.get_zf_url(f"/blobs/{recipe_name}"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
            json={
                "flag_name": flag["key"],
                "kind": flag["kind"],
                "data": base64.b64encode(content).decode("ascii"),
                "comments": f"Uploaded by recipesauto from "
                f"{source.name if isinstance(source, Path) else source} "
                f"({BLOB_SOURCE_CHECKSUM_MARKER}{checksum})",
            },
        )
        if not HTTPStatus(response.status_code).is_success:
            logger.error(response.text)
        response.raise_for_status()
        return response.json()

    def _resolve_blob_flags(
        self,
        *,
        recipe_name: str,
        version: str,
        offliner_flags: dict[str, Any],
        current_offliner_flags: dict[str, Any],
        upload: bool,
    ):
        """Replace (in-place) sources of blob flags by Zimfarm blob URLs

        Recipes are expressed with sources of blob flags, either a local file (Path)
        or a remote URL (str). Matching blobs are found by comparing the sha256 of
        the source content with either the blob checksum (blob stored as-is) or the
        source checksum stored in blob comments (blob uploaded by this tool).

        When no matching blob is found, the source is uploaded as a new blob if
        `upload` is set, otherwise it is kept, so that a change is detected.

        When source is not available (missing local file, download error), a
        warning is logged and current value of the flag is kept (flag is removed if
        it has no current value).
        """
        blob_flags = [
            flag
            for flag in self._get_blob_flags(offliner_flags["offliner_id"], version)
            if offliner_flags.get(flag["data_key"])
        ]
        if not blob_flags:
            return

        blobs = self._list_zf_blobs(recipe_name)
        blobs_urls = {blob["url"] for blob in blobs}

        for flag in blob_flags:
            source = offliner_flags[flag["data_key"]]
            if source in blobs_urls:
                # already a blob URL (e.g. from overrides)
                continue

            content = self._get_blob_source_content(source)
            if content is None:
                if current_value := current_offliner_flags.get(flag["data_key"]):
                    offliner_flags[flag["data_key"]] = current_value
                else:
                    del offliner_flags[flag["data_key"]]
                continue
            checksum = hashlib.sha256(content).hexdigest()

            matching_blob = next(
                (
                    blob
                    for blob in blobs
                    if blob["flag_name"] == flag["key"]
                    and (
                        blob["checksum"] == checksum
                        or f"{BLOB_SOURCE_CHECKSUM_MARKER}{checksum}"
                        in (blob["comments"] or "")
                    )
                ),
                None,
            )
            if matching_blob:
                offliner_flags[flag["data_key"]] = matching_blob["url"]
                continue

            if not upload:
                logger.info(
                    f"New blob would be uploaded for {flag['data_key']} from {source}"
                )
                continue

            new_blob = self._create_blob_on_zf(
                recipe_name=recipe_name,
                flag=flag,
                source=source,
                content=content,
                checksum=checksum,
            )
            logger.info(
                f"Blob uploaded for {flag['data_key']} from {source}: {new_blob['url']}"
            )
            offliner_flags[flag["data_key"]] = new_blob["url"]
            blobs.append(new_blob)
            blobs_urls.add(new_blob["url"])

    def get_zf_url(self, path: str):
        """Build full Zimfarm URL from a path"""
        return "/".join([context.zimfarm_api_url, path[1:] if path[0] == "/" else path])

    def get_zf_headers(self):
        """Build zimfarm headers"""
        return {
            "Authorization": f"Bearer {context.zimfarm_access_token}",
            "Content-type": "application/json",
        }

    def authenticate(self):
        response = requests.get(
            self.get_zf_url("/auth/me"),
            headers=self.get_zf_headers(),
            timeout=context.http_timeout,
        )
        response.raise_for_status()
