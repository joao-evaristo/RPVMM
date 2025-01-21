class Wave:
    def __init__(self, wave_class: str):
        self.wave_class = wave_class
        self.boxes: set[int] = set()
        self.corridors: set[str] = set()
        self.floors: set[int] = set()
        self.max_min_even_corridor: dict[int, list[int]] = {}
        self.max_min_odd_corridor: dict[int, list[int]] = {}
        self.total_products: int = 0

    def add_box(self, box_id: int, box_pieces: int) -> None:
        self.boxes.add(box_id)
        self.total_products += box_pieces

    def add_corridor(self, corridor_key: str) -> None:
        self.corridors.add(corridor_key)

    def add_floor(self, floor: int) -> None:
        self.floors.add(floor)

    def insert_corridor(self, corridor_key: str) -> None:
        corridor_id, floor = self.extract_corridor_id_floor(corridor_key)
        self.add_corridor(corridor_key)
        self.add_floor(floor)
        self.update_corridor_bounds(corridor_id, floor)

    def extract_corridor_id_floor(self, corridor_key: str) -> tuple[int, int]:
        try:
            corridor_id, floor = corridor_key.split("_")
            return int(corridor_id), int(floor)
        except ValueError:
            raise ValueError(f"Invalid corridor_key format: {corridor_key}")

    def update_corridor_bounds(self, corridor_id: int, floor: int) -> None:
        is_even = corridor_id % 2 == 0
        bounds_dict = self.max_min_even_corridor if is_even else self.max_min_odd_corridor

        if floor not in bounds_dict:
            bounds_dict[floor] = [corridor_id, corridor_id]
        else:
            bounds_dict[floor][0] = max(bounds_dict[floor][0], corridor_id)  # Update max
            bounds_dict[floor][1] = min(bounds_dict[floor][1], corridor_id)  # Update min
