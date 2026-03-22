from src.engine import DomainParser
import re

parser = DomainParser()

# Test Z_12 -> projection to Z_3
desc1 = {'name': 'Advanced Crystal', 'group': 'Z_12', 'subgroup': 'Z_4', 'set': 'Z_12/Z_4', 'k': 3}
domain1 = parser.parse(desc1)
print(f"Domain 1: name={domain1.name}, m={domain1.m}, G={domain1.G}, H={domain1.H}, tags={domain1.tags}")

# Test direct m
desc2 = {'group': 'SO(3)', 'm': 7, 'k': 3}
domain2 = parser.parse(desc2)
print(f"Domain 2: name={domain2.name}, m={domain2.m}, G={domain2.G}")

# Test Z_8
desc3 = {'group': 'Z_8', 'k': 3}
domain3 = parser.parse(desc3)
print(f"Domain 3: name={domain3.name}, m={domain3.m}, G={domain3.G}")
