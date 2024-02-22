def patch_dict(data, patch):
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
    return data
