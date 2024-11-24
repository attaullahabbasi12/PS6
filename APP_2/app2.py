from shiny import App, ui, render
import pandas as pd
import altair as alt
import os
import tempfile

# Load the collapsed dataset
data_path = "/Users/attaullah/Documents/PS-6-/top_alerts_map_byhour/top_alerts_map_byhour.csv"
collapsed_data = pd.read_csv(data_path)

# Add the 'type_subtype' column
collapsed_data["type_subtype"] = collapsed_data["type"] + " x " + collapsed_data["subtype"].fillna("Unclassified")

# Filter the data to ensure latitude and longitude are within valid bounds
latitude_bounds = [41.64, 42.02]
longitude_bounds = [-87.93, -87.55]

collapsed_data = collapsed_data[
    (collapsed_data["latitude"] >= latitude_bounds[0]) &
    (collapsed_data["latitude"] <= latitude_bounds[1]) &
    (collapsed_data["longitude"] >= longitude_bounds[0]) &
    (collapsed_data["longitude"] <= longitude_bounds[1])
]

# Ensure hour is in proper datetime format
collapsed_data["hour"] = pd.to_datetime(collapsed_data["hour"], errors="coerce")

# Get unique type_subtype combinations for the dropdown menu
unique_combinations = collapsed_data["type_subtype"].unique().tolist()

# Define the Shiny app UI
app_ui = ui.page_fluid(
    ui.h2("Top Alert Locations by Type, Subtype, and Hour"),
    ui.input_select(
        id="type_subtype", 
        label="Select Type and Subtype", 
        choices=unique_combinations, 
        selected=unique_combinations[0] if unique_combinations else None
    ),
    ui.input_slider(
        id="hour", 
        label="Select Hour", 
        min=0, 
        max=23, 
        value=12, 
        step=1, 
        ticks=True
    ),
    ui.output_image("alert_plot")  # Render the plot as an image
)

# Define the server logic for the Shiny app
def server(input, output, session):
    @output
    @render.image
    def alert_plot():
        # Filter the data based on user input
        filtered_data = collapsed_data[
            (collapsed_data["type_subtype"] == input.type_subtype()) &
            (collapsed_data["hour"].dt.hour == input.hour())
        ]

        # Get the Top 10 locations by alert count
        top_10_data = filtered_data.nlargest(10, "alert_count")

        # Handle cases where no data is available
        if top_10_data.empty:
            return None

        # Create the scatter plot using Altair
        chart = alt.Chart(top_10_data).mark_circle().encode(
            x=alt.X("longitude:Q", title="Longitude", scale=alt.Scale(domain=longitude_bounds)),
            y=alt.Y("latitude:Q", title="Latitude", scale=alt.Scale(domain=latitude_bounds)),
            size="alert_count:Q",
            tooltip=["latitude", "longitude", "alert_count"]
        ).properties(
            width=700,
            height=500,
            title=f"Top 10 Alert Locations for '{input.type_subtype()}' at {input.hour()}:00"
        )

        # Save the chart as a temporary PNG file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        chart.save(temp_file.name)
        
        return {
            "src": temp_file.name,
            "width": 700,
            "height": 500
        }

# Create the Shiny app
app = App(app_ui, server)

# Run the app
if __name__ == "__main__":
    app.run()
