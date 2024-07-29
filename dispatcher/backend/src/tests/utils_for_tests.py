def patch_dict(data, patch):
    """Apply a patch to a dictionnary

    - data is the dictionnary to modify (in-place)
    - patch is a dictionnary of modifications to apply (could contain nested dictionnary
    when the value to modify is deep inside the data dictionnary)

    E.g. if data is { "key1": { "subkey1": "value1", subkey2": "value2" } } and patch is
    { "key1": { "subkey2": "newvalue2"}} then after the operation data will become
    { "key1": { "subkey1": "value1", subkey2": "newvalue2" } }
    """
    for key, patch_value in patch.items():
        if key in data:
            if patch_value is None:
                # If the patch value is None, remove the key from the original
                # dictionary
                del data[key]
            else:
                original_value = data[key]
                if isinstance(original_value, dict) and isinstance(patch_value, dict):
                    # If both values are dictionaries, recursively patch the nested
                    # dictionaries
                    patch_dict(original_value, patch_value)
                else:
                    # Otherwise, update the value in the original dictionary
                    data[key] = patch_value
        else:
            # If the key is not present in the original dictionary, set it with the
            # patch value
            data[key] = patch_value


def update_dict(dict: dict, key_path: str, new_value: any):
    """Update a nested key value in a dictionary

    E.g if key_path is 'key1.subkey2', then dict['key1']['subkey2'] will be set"""

    # Split the key path into individual keys
    keys = key_path.split(".")

    # Initialize a reference to the nested dictionary
    current_dict = dict

    # Navigate through the nested structure
    for key in keys[:-1]:
        current_dict = current_dict[key]

    # Update the value using the last key
    current_dict[keys[-1]] = new_value
