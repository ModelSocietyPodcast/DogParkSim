import streamlit as st
from PIL import Image, ImageDraw
from DogPark_04Jan2025 import DogPark, Dog, ParkObject, agent_portrayal   # Importing the simulation components

def render_grid(model):
    """Render the grid using images specified in agent portrayal."""
    grid_width = model.grid.width
    grid_height = model.grid.height
    cell_size = 50  # Size of each cell in the grid

    # Create a blank image for the grid
    grid_image = Image.new("RGBA", (grid_width * cell_size, grid_height * cell_size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(grid_image)

    # Draw the outer border
    draw.rectangle(
        [(0, 0), (grid_width * cell_size - 1, grid_height * cell_size - 1)],
        outline="black",
        width=2
    )

    # Draw grid lines for cells (dashed lines)
    dash_length = 5
    for x in range(1, grid_width):
        for y in range(0, grid_height * cell_size, 2 * dash_length):
            draw.line(
                [(x * cell_size, y), (x * cell_size, min(y + dash_length, grid_height * cell_size))],
                fill="grey",
                width=1
            )
    for y in range(1, grid_height):
        for x in range(0, grid_width * cell_size, 2 * dash_length):
            draw.line(
                [(x, y * cell_size), (min(x + dash_length, grid_width * cell_size), y * cell_size)],
                fill="grey",
                width=1
            )

    for agent in model.schedule.agents:
        if agent.pos is not None:  # Skip agents without valid positions
            portrayal = agent_portrayal(agent, Dog, ParkObject)
            if portrayal and "Shape" in portrayal:
                x, y = agent.pos
                # Calculate pixel position for the agent
                px = x * cell_size + int(cell_size * 0.05)  # Offset for smaller image (5% padding)
                py = (grid_height - y - 1) * cell_size + int(cell_size * 0.05)  # Invert y-axis and offset

                if portrayal["Shape"] and portrayal["Shape"].endswith(".png"):
                    # Load the image for the agent
                    agent_image = Image.open(portrayal["Shape"]).resize((int(cell_size * 0.9), int(cell_size * 0.9)))  # 90% of cell size
                    grid_image.paste(agent_image, (px, py), agent_image)
                    
                # Check for overlay
                if "Overlay" in portrayal:
                    overlays = portrayal["Overlay"]
                    if isinstance(overlays, list):
                        for overlay in overlays:
                            if "Shape" in overlay and overlay["Shape"].endswith(".png"):
                                overlay_image = Image.open(overlay["Shape"]).resize(
                                    (int(cell_size * overlay["scale"]), int(cell_size * overlay["scale"]))
                                )
                                overlay_px = x * cell_size + int(cell_size * 0.05)  # Offset for smaller image (5% padding)
                                overlay_py = (grid_height - y - 1) * cell_size + int(cell_size * 0.05)  # Invert y-axis and offset
                                grid_image.paste(overlay_image, (overlay_px, overlay_py), overlay_image)

    return grid_image

def main():
    st.title("Jemmy's Dog Run Simulation")

    # Sidebar instructions
    st.sidebar.write("Happy Birthday, Rameet!!")
    st.sidebar.write("This is a simulation of Jemmy's Dog Run in Manhattan.")
    st.sidebar.write("Dogs enter the park at the bottom of the screen and will move around, playing and exploring. When they see bowls of food, they will move towards them and eat them, whereupon more food will appear elsewhere. If they see toys, they will pick them up (but they prioritize food). When they get tired, they will leave the park to go home and nap.")    
    st.sidebar.write("You can use the sliders to control the size of the dog park, how busy it is (i.e., how often dogs arrive), and how many trees, food bowls, and toys there are.")
    st.sidebar.write("I hope you enjoy it :)")

    # Sidebar controls for user input
    st.sidebar.header("Simulation Settings")
    grid_width = st.sidebar.slider("Width of the Dog Park:", 10, 12, 15)
    grid_height = st.sidebar.slider("Height of the Dog Park:", 10, 12, 15)
    arrival_rate = st.sidebar.slider("Dog Arrival Rate (probability per step):", 0.01, 1.0, 0.15, step=0.01)
    num_trees = st.sidebar.slider("Number of Trees:", 1, 20, 10)
    num_food_bowls = st.sidebar.slider("Number of Food Bowls:", 1, 10, 3)
    num_toys = st.sidebar.slider("Number of Food Bowls:", 1, 10, 5)

    # Grid settings
    num_dogs = 25  # Maximum number of dogs

    # Button to start simulation
    if st.sidebar.button("Run Simulation"):
        # Initialize the simulation model
        st.text("Initializing simulation...")
        model = DogPark(
            width=grid_width,
            height=grid_height,
            num_dogs=num_dogs,
            num_trees=num_trees,
            num_food_bowls=num_food_bowls,
            num_toys=num_toys,
            arrival_rate=arrival_rate
        )

        # Run the simulation loop
        st.text("Running simulation...")
        placeholder = st.empty()

        for step in range(100):  # Run for 100 steps
            model.step()
            grid_image = render_grid(model)
            placeholder.image(grid_image, caption=f"Step {step + 1}", use_container_width=True)

# Run the Streamlit app
if __name__ == "__main__":
    main()
