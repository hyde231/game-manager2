import json
from dataclasses import asdict, is_dataclass
from typing import Type, TypeVar, Generic, List, Dict
from pathlib import Path

T = TypeVar('T')  # A generic type variable

class JsonStorage(Generic[T]):
    def __init__(self, filename: str):
        self.filename = Path(filename)
        if not self.filename.exists():
            self.filename.write_text('[]')  # Initialize file if it doesn't exist

    def load(self, cls: Type[T]) -> List[T]:
        """Load all instances of type T from the JSON file."""
        data = json.loads(self.filename.read_text())
        return [cls(**item) for item in data]

    def save(self, items: List[T]):
        """Save all instances of type T to the JSON file."""
        data = [self._dataclass_to_dict(item) for item in items]
        self.filename.write_text(json.dumps(data, indent=4))

    def add(self, item: T):
        """Add a new instance of type T to the JSON file."""
        items = self.load(type(item))
        items.append(item)
        self.save(items)

    def remove(self, item_id: int, cls: Type[T], id_field: str = 'id'):
        """Remove an instance of type T by its id."""
        items = self.load(cls)
        items = [item for item in items if getattr(item, id_field) != item_id]
        self.save(items)

    def _dataclass_to_dict(self, instance: T) -> Dict:
        """Convert a dataclass instance to a dictionary excluding non-dataclass fields."""
        to_dict = getattr(instance, "to_dict", None)
        if to_dict and callable(to_dict):
            return instance.to_dict()
        if is_dataclass(instance):
            return asdict(instance)
        if isinstance(instance,dict):
            return instance
        raise ValueError("Instance is not a dataclass.")
