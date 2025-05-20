import json
from typing import Any, List

import requests

from kuhl_haus.magpie.canary.env import (
    CONFIG_API,
    CANARY_CONFIG_FILE_PATH,
    RESOLVERS_CONFIG_FILE_PATH,
)
from kuhl_haus.magpie.endpoints.models import DnsResolver, DnsResolverList, EndpointModel


def from_file(file_path, model) -> List[Any]:
    try:
        with open(file_path, 'r') as file:
            file_contents = json.load(file)
        return [model(**x) for x in file_contents]
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file {file_path}")
        return []


def get_endpoints():
    if CONFIG_API:
        response = requests.get(f"{CONFIG_API}/endpoints/")
        json_data = response.json()
        return [EndpointModel(**x) for x in json_data]
    else:
        return from_file(CANARY_CONFIG_FILE_PATH, EndpointModel)


def get_resolvers():
    if CONFIG_API:
        response = requests.get(f"{CONFIG_API}/resolvers/")
        json_data = response.json()
        return [DnsResolver(**x) for x in json_data]
    else:
        resolver_names = set()
        resolvers = []
        resolver_lists = get_resolver_lists()
        for rl in resolver_lists:
            for resolver in rl.resolvers:
                if resolver.name in resolver_names:
                    continue
                else:
                    resolver_names.add(resolver.name)
                    resolvers.append(resolver)
        return resolvers


def get_resolver_lists():
    if CONFIG_API:
        response = requests.get(f"{CONFIG_API}/resolver-lists/")
        json_data = response.json()
        return [DnsResolverList(**x) for x in json_data]
    else:
        return from_file(RESOLVERS_CONFIG_FILE_PATH, DnsResolverList)


def get_default_resolver_list():
    if CONFIG_API:
        response = requests.get(f"{CONFIG_API}/resolver-lists/1/")
        json_data = response.json()
        resolver_list = DnsResolverList(**json_data)
    else:
        resolver_list = from_file(RESOLVERS_CONFIG_FILE_PATH, DnsResolverList)

    if resolver_list:
        return [DnsResolver(**x) for x in resolver_list.resolvers]
    return []
