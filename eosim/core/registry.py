# SPDX-License-Identifier: MIT
"""Platform registry for querying and filtering platforms."""
from typing import Dict, List, Optional
from collections import defaultdict
from eosim.core.platform import Platform, discover_platforms


class PlatformRegistry:
    def __init__(self, root_dir: str = ""):
        self._platforms: Dict[str, Platform] = {}
        if root_dir:
            self._platforms = discover_platforms(root_dir)

    @classmethod
    def from_dict(cls, platforms: Dict[str, Platform]) -> "PlatformRegistry":
        reg = cls.__new__(cls)
        reg._platforms = dict(platforms)
        return reg

    def count(self) -> int:
        return len(self._platforms)

    def all(self) -> List[Platform]:
        return list(self._platforms.values())

    def get(self, name: str) -> Optional[Platform]:
        return self._platforms.get(name)

    def filter(self, arch: str = None, vendor: str = None,
               platform_class: str = None, engine: str = None,
               domain: str = None) -> List[Platform]:
        results = list(self._platforms.values())
        if arch is not None:
            results = [p for p in results if p.arch.lower() == arch.lower()]
        if vendor is not None:
            results = [p for p in results if p.vendor.lower() == vendor.lower()]
        if platform_class is not None:
            results = [p for p in results if p.platform_class.lower() == platform_class.lower()]
        if engine is not None:
            results = [p for p in results if p.engine.lower() == engine.lower()]
        if domain is not None:
            results = [p for p in results if p.domain.lower() == domain.lower()]
        return results

    def group_by(self, field: str) -> Dict[str, List[Platform]]:
        groups: Dict[str, List[Platform]] = defaultdict(list)
        for p in self._platforms.values():
            key = getattr(p, field, "")
            groups[key].append(p)
        return dict(groups)

    def search(self, query: str) -> List[Platform]:
        q = query.lower()
        results = []
        for p in self._platforms.values():
            searchable = " ".join([
                p.name, p.arch, p.engine, p.vendor,
                p.platform_class, p.soc, p.domain, p.display_name,
            ]).lower()
            if q in searchable:
                results.append(p)
        return results

    def stats(self) -> Dict[str, Dict[str, int]]:
        st: Dict[str, Dict[str, int]] = {
            "arch": defaultdict(int),
            "vendor": defaultdict(int),
            "platform_class": defaultdict(int),
            "engine": defaultdict(int),
            "domain": defaultdict(int),
        }
        for p in self._platforms.values():
            st["arch"][p.arch] += 1
            if p.vendor:
                st["vendor"][p.vendor] += 1
            if p.platform_class:
                st["platform_class"][p.platform_class] += 1
            st["engine"][p.engine] += 1
            if p.domain:
                st["domain"][p.domain] += 1
        return {k: dict(v) for k, v in st.items()}

    def vendors(self) -> List[str]:
        return sorted({p.vendor for p in self._platforms.values() if p.vendor})

    def arches(self) -> List[str]:
        return sorted({p.arch for p in self._platforms.values() if p.arch})

    def classes(self) -> List[str]:
        return sorted({p.platform_class for p in self._platforms.values() if p.platform_class})
