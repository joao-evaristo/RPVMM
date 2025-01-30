from box import Box

class Wave:
    def __init__(self, wave_class: str):
        self.wave_class = wave_class
        self.boxes: set[int] = set()
        self.corridors: dict[str, set[int]] = {}
        self.floors: set[int] = set()
        self.max_min_even_corridor: dict[int, list[int]] = {}
        self.max_min_odd_corridor: dict[int, list[int]] = {}
        self.total_products: int = 0

    def add_box(self, box_id: int, box_pieces: int) -> None:
        self.boxes.add(box_id)
        self.total_products += box_pieces

    def add_corridor(self, corridor_key: str, box_id: int) -> None:
        if corridor_key not in self.corridors:
            self.corridors[corridor_key] = set()
        self.corridors[corridor_key].add(box_id)

    def add_floor(self, floor: int) -> None:
        self.floors.add(floor)

    def insert_corridor(self, corridor_key: str, box_id: int) -> None:
        corridor_id, floor = self.extract_corridor_id_floor(corridor_key)
        self.add_corridor(corridor_key, box_id)
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

    def update_max_min_corridor(self):
        corridors = set()
        for corridor_key in self.corridors:
            corridor_id, floor = self.extract_corridor_id_floor(corridor_key)
            corridors.add(corridor_id)
        print([corridor for corridor in corridors if corridor % 2 == 0])
        even_corridors = [corridor for corridor in corridors if corridor % 2 == 0]
        odd_corridors = [corridor for corridor in corridors if corridor % 2 != 0]
        even_corridors.sort()
        odd_corridors.sort()
        self.max_min_even_corridor = {floor: [even_corridors[-1], even_corridors[0]] for floor in self.floors}
        self.max_min_odd_corridor = {floor: [odd_corridors[-1], odd_corridors[0]] for floor in self.floors}


    def update_floors(self):
        floors_used = set()
        for corridor_key in self.corridors:
            corridor_id, floor = self.extract_corridor_id_floor(corridor_key)
            floors_used.add(floor)
        self.floors = floors_used

    def remove_box_corridor(self, box: Box) -> None:
        for corridor_key in box.get_corridors():
            if corridor_key in self.corridors and box.id in self.corridors[corridor_key]:
                self.corridors[corridor_key].remove(box.id)
                if not self.corridors[corridor_key]:
                    del self.corridors[corridor_key]
                    self.update_floors()
                    self.update_max_min_corridor()

    def remove_box(self, box: Box) -> None:
        self.boxes.remove(box.id)
        self.total_products -= box.get_total_products()
        self.remove_box_corridor(box)

    def insert_box(self, box: Box, corridors_keys: [str]) -> None: # mudar isso aqui depois
        self.add_box(box.id, box.get_total_products())
        for corridor_key in corridors_keys:
            self.insert_corridor(corridor_key, box.id)