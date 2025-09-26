import pandas as pd
import matplotlib.pyplot as plt

# Load the final risk matrix data from the updated file path
file_path = "/Users/nic/code/charts/Wilhelmina_Full_Detailed_Risk_Matrix.xlsx"
risk_matrix_df = pd.read_excel(file_path, sheet_name="Sheet1")

# Create a 5x5 risk matrix plot with risk IDs displayed in the appropriate cells
fig, ax = plt.subplots(figsize=(8, 8))

# Define risk levels and likelihood levels
risk_levels = ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"]
likelihood_levels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]

# Define colors for risk levels based on score ranges
color_map = {
    "Low": "#90EE90",         # Light Green
    "Medium": "#FFD700",      # Yellow
    "High": "#FFA500",        # Orange
    "Critical": "#FF4500",    # Red-Orange
    "Severe": "#8B0000"       # Dark Red
}

# Map risk scores to risk levels
def score_to_level(score):
    if score <= 5:
        return "Low"
    elif 6 <= score <= 10:
        return "Medium"
    elif 11 <= score <= 15:
        return "High"
    elif 16 <= score <= 20:
        return "Critical"
    else:
        return "Severe"

# Fill the entire chart with colors based on risk scores and add borders
for i in range(5):
    for j in range(5):
        score = (i + 1) * (j + 1)  # Calculate the risk score for each cell
        risk_level = score_to_level(score)
        color = color_map[risk_level]
        # Draw each cell with borders and color
        ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=True, edgecolor="black", linewidth=0.5, color=color))

# Add risk IDs to the appropriate cells
positions = {}  # Track occupied positions
for index, row in risk_matrix_df.iterrows():
    # Adjust the coordinates to ensure they fit within the 5x5 matrix
    x = min(max(row['Consequence Score'] - 1, 0), 4)  # X-axis: Consequence
    y = min(max(row['Likelihood Score'] - 1, 0), 4)   # Y-axis: Likelihood
    risk_id = str(row['Risk ID'])  # Ensure the Risk ID is a string
    pos_key = (x, y)
    if pos_key in positions:
        positions[pos_key].append(risk_id)
    else:
        positions[pos_key] = [risk_id]

# Place the risk IDs in the correct cells, handling multiple risks per cell
for (x, y), risk_ids in positions.items():
    combined_risk_ids = "\n".join(risk_ids)
    ax.text(x + 0.5, y + 0.5, combined_risk_ids, ha='center', va='center', fontsize=10, color="black", fontweight='bold')

# Set axis labels and title
ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_yticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_xticklabels(risk_levels, fontsize=12)
ax.set_yticklabels(likelihood_levels, fontsize=12)
ax.set_xlabel("Consequence", fontsize=14)
ax.set_ylabel("Likelihood", fontsize=14)
ax.set_title("5x5 Risk Matrix with Risk IDs - Wilhelmina Energy Kuantan", fontsize=16, fontweight='bold')
ax.set_xlim(0, 5)
ax.set_ylim(0, 5)
ax.invert_yaxis()  # Invert Y-axis to match standard risk matrix layout

# Save the plot with borders to the specified path
chart_path = "/Users/nic/code/charts/Wilhelmina_5x5_Risk_Matrix_Final.png"
plt.savefig(chart_path)
plt.close()
print(f"Chart saved successfully at {chart_path}")
