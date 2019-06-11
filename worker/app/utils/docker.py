

def remove_existing_container(docker_client, name):
    """remove container matching its name, if exists"""
    for container in docker_client.containers.list(all=True, filters={'name': name}):
        container.stop()
        container.remove()


def get_ip_address(docker_client, name):
    """IP Address (first) of a named container"""
    return docker_client.api.inspect_container(name)["NetworkSettings"]["IPAddress"]
