from shiny import ui, App, render, run_app
import pandas as pd
import altair as alt
import os

# Load your processed data
data_path = '/Users/attaullah/Documents/PS-6-/waze_data/processed_waze_data_fixed.csv'
waze_data = pd.read_csv(data_path)

# Ensure valid coordinates
waze_data = waze_data[
    (waze_data['latitude'] >= 41.6) & (waze_data['latitude'] <= 42.1) &
    (waze_data['longitude'] >= -87.9) & (waze_data['longitude'] <= -87.5)
]

# Create unique type x subtype combinations
waze_data['type_subtype'] = waze_data['type'] + " x " + waze_data['subtype'].fillna("Unclassified")
unique_combinations = sorted(waze_data['type_subtype'].unique())

# Generate dropdown choices as a dictionary
dropdown_choices = {combo: combo for combo in unique_combinations}

# Create the dropdown UI
app_ui = ui.page_fluid(
    ui.h2("Top Alert Locations in Chicago"),
    ui.input_select(
        "type_subtype",
        "Select Type and Subtype",
        choices=dropdown_choices,
        multiple=False
    ),
    ui.output_image("top_10_plot")  # Render the plot as an image
)

# Server logic for the Shiny app
def server(input, output, session):
    @output
    @render.image
    def top_10_plot():
        # Get the selected type and subtype from the dropdown
        selected_type_subtype = input.type_subtype()

        # Filter the data for the selected type x subtype
        filtered_data = waze_data[waze_data['type_subtype'] == selected_type_subtype]

        # Group by latitude and longitude and calculate alert counts
        top_10 = (
            filtered_data.groupby(["latitude", "longitude"])
            .size()
            .reset_index(name="count")
            .nlargest(10, "count")
        )

        # Create a scatter plot using Altair
        scatter_plot = alt.Chart(top_10).mark_circle().encode(
            x=alt.X('longitude:Q', title='Longitude', scale=alt.Scale(domain=[-87.9, -87.5])),
            y=alt.Y('latitude:Q', title='Latitude', scale=alt.Scale(domain=[41.6, 42.1])),
            size=alt.Size('count:Q', title='Number of Alerts'),
            tooltip=['latitude', 'longitude', 'count']
        ).properties(
            title=f"Top 10 Alert Locations for {selected_type_subtype}",
            width=800,
            height=600
        )

        # Save the plot as a PNG file
        output_path = "/tmp/top_10_plot.png"
        scatter_plot.save(output_path)

        # Return the path to the PNG file
        return {"src": output_path, "width": 800, "height": 600}

# Create the Shiny app
app = App(app_ui, server)

# Start the Shiny app server
if __name__ == "__main__":
    run_app(app)

print(f"Total type x subtype combinations: {len(unique_combinations)}")

