from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import random

# Helper function for toy portrayal
def toy_overlay(toy, dog):
    """Create a miniature portrayal of the toy for overlaying on the dog."""
    return [
        {
            "Shape": dog.image,  # Dog image
            "Layer": 1,  # Base layer
            "scale": 1.0  # Full size
        },
        {
            "Shape": "BallPic.png",  # Toy image
            "Layer": 2,  # Overlay layer above the dog
            "scale": 0.30,  # Miniature size (15% of cell size)
            "Position": "bottom-left"  # Position in the cell
        }
    ]

def agent_portrayal(agent, Dog, ParkObject):
    if isinstance(agent, Dog):
        portrayal = {
            "Shape": agent.image,  # Path to dog image
            "Layer": 1,
            "scale": 1.0  # Adjust scale to enlarge the image
        }
        if agent.carrying_toy:
            # Add the toy overlay when the dog is carrying a toy
            portrayal["Overlay"] = toy_overlay(agent.carrying_toy, agent)
        return portrayal
    elif isinstance(agent, ParkObject):
        if agent.type == "Tree":
            return {
                "Shape": "TreePic.png",  # Path to tree image
                "Layer": 1,
                "scale": 1.0  # Adjust scale to enlarge the image
            }
        elif agent.type == "Food Bowl":
            return {
                "Shape": "BowlPic.png",  # Path to bowl image
                "Layer": 1,
                "scale": 1.0  # Adjust scale to enlarge the image
            }
        elif agent.type == "Toy":
            return {
                "Shape": "BallPic.png",  # Path to ball image
                "Layer": 1,
                "scale": 1.0  # Normal size when not carried
            }

class Dog(Agent):
    DOG_IMAGES = ["DogPic1.png", "DogPic2.png", "DogPic3.png", "DogPic4.png"]  # Different dog emojis

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = random.randint(10, 100)  # Energy in minutes
        self.image = random.choice(self.DOG_IMAGES)  # Randomly assign an emoji
        self.carrying_toy = None  # Reference to the toy being carried, if any

    def drop_toy(self):
        """Drop the toy in the current cell."""
        if self.carrying_toy:
            self.carrying_toy.being_carried = False
            self.model.grid.place_agent(self.carrying_toy, self.pos)
            self.carrying_toy = None

    def step(self):
        if self.energy > 0:
            # Check for food bowls and toys in adjacent squares
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            food_bowl = None
            toy = None
            for neighbor in neighbors:
                cell_contents = self.model.grid.get_cell_list_contents([neighbor])
                for obj in cell_contents:
                    if isinstance(obj, ParkObject) and obj.type == "Food Bowl":
                        food_bowl = obj
                        break
                    elif isinstance(obj, ParkObject) and obj.type == "Toy" and self.carrying_toy is None:
                        toy = obj
                if food_bowl:
                    break

            if food_bowl:
                # Move to the food bowl and consume it
                self.model.grid.move_agent(self, food_bowl.pos)
                self.model.grid.remove_agent(food_bowl)
                self.model.schedule.remove(food_bowl)

                # Drop the toy if carrying one
                if self.carrying_toy:
                    self.drop_toy()

                # Add a new food bowl elsewhere
                self.model.add_food_bowl()
            elif toy:
                # Pick up the toy
                self.model.grid.remove_agent(toy)
                toy.being_carried = True
                self.carrying_toy = toy
            else:
                # Move randomly if no food or toy is found
                possible_steps = [step for step in self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                                  if self.model.can_move_to(step)]
                if possible_steps:
                    new_position = self.random.choice(possible_steps)
                    self.model.grid.move_agent(self, new_position)

            self.energy -= 1
        else:
            # Drop the toy if carrying one
            if self.carrying_toy:
                self.drop_toy()

            # Move towards exit if energy is depleted
            exit_position = (self.model.grid.width // 2, 0)
            path_to_exit = [exit_position]
            if self.pos != exit_position:
                path_to_exit = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                path_to_exit = [step for step in path_to_exit if self.model.can_move_to(step) and step == exit_position]

            if not path_to_exit:
                # Exit from current position if path is blocked
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
            else:
                self.model.grid.move_agent(self, exit_position)

class ParkObject(Agent):
    def __init__(self, unique_id, model, obj_type):
        super().__init__(unique_id, model)
        self.type = obj_type
        self.being_carried = False  # State to track if the toy is being carried

    def step(self):
        # Skip action if the toy is being carried
        if self.being_carried:
            return

class DogPark(Model):
    def __init__(self, width, height, num_dogs, num_trees, num_food_bowls, num_toys, arrival_rate):
        super().__init__()  # Explicitly initialize the Model superclass
        self.num_agents = num_dogs
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.current_dogs = 0  # Track how many dogs are currently in the park
        self.total_dogs_added = 0  # Track total dogs introduced
        self.max_dogs = num_dogs  # Maximum number of dogs
        self.entrance = (width // 2, 0)  # Entrance is at the middle of the bottom row
        self.arrival_rate = arrival_rate

        # Add Trees
        for i in range(num_trees):
            self.add_tree()

        # Add Food Bowls
        for i in range(num_food_bowls):
            self.add_food_bowl()

        # Add Toys
        for i in range(num_toys):
            self.add_toy()

        self.running = True

    def can_move_to(self, pos):
        """Determine if a dog can move to a specific cell."""
        cell_contents = self.grid.get_cell_list_contents([pos])
        for obj in cell_contents:
            if isinstance(obj, Dog) or (isinstance(obj, ParkObject) and obj.type == "Tree"):
                return False
        return True

    def add_dog(self):
        """Introduce a new dog at the entrance if under max_dogs."""
        if self.total_dogs_added < self.max_dogs:
            dog = Dog(f"Dog_{self.total_dogs_added}", self)
            self.schedule.add(dog)
            self.grid.place_agent(dog, self.entrance)
            self.total_dogs_added += 1

    def add_food_bowl(self):
        """Add a new food bowl to a random unoccupied space."""
        while True:
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(0, self.grid.height - 1)
            if self.grid.is_cell_empty((x, y)):
                bowl = ParkObject(f"Bowl_{random.randint(1000, 9999)}", self, "Food Bowl")
                self.schedule.add(bowl)
                self.grid.place_agent(bowl, (x, y))
                break

    def add_tree(self):
        """Add a new tree to a random unoccupied space."""
        while True:
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(1, self.grid.height - 1)
            if self.grid.is_cell_empty((x, y)):
                tree = ParkObject(f"Tree_{random.randint(1000, 9999)}", self, "Tree")
                self.schedule.add(tree)
                self.grid.place_agent(tree, (x, y))
                break

    def add_toy(self):
        """Add a new toy to a random unoccupied space."""
        while True:
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(1, self.grid.height - 1)
            if self.grid.is_cell_empty((x, y)):
                toy = ParkObject(f"Toy_{random.randint(1000, 9999)}", self, "Toy")
                self.schedule.add(toy)
                self.grid.place_agent(toy, (x, y))
                break

    def step(self):
        """Advance the model by one step."""
        # Randomly add a dog based on the arrival rate
        if random.random() < self.arrival_rate:
            self.add_dog()

        self.schedule.step()

# Grid size and parameters
grid_width = 10
grid_height = 10
num_dogs = 100
