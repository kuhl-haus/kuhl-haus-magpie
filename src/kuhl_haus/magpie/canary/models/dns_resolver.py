from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass()
class DnsResolver:
    name: str
    ip_address: str


@dataclass_json(letter_case=LetterCase.SNAKE)
@dataclass()
class DnsResolverList:
    name: str
    resolvers: List[DnsResolver]
