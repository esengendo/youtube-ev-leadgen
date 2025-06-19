# Cursor AI Intent Detection Rules

These rules define how Cursor AI should classify YouTube comments for lead generation and sales intent in the EV SUV market.

## Intent Categories
- **Purchase Intent**: User expresses desire to buy, test drive, or own an EV SUV.
- **Interest/Inquiry**: User asks questions about features, specs, pricing, or availability.
- **Positive Sentiment**: User expresses positive feelings about the brand, model, or EVs in general.
- **Negative Sentiment**: User expresses concerns, dislikes, or negative experiences.
- **Competitor Mention**: User compares with or mentions other brands/models.
- **General Comment**: Not related to purchase or sales intent.

## Example Rules
- If comment contains phrases like "I want to buy", "looking to purchase", "test drive", classify as **Purchase Intent**.
- If comment contains questions about price, range, features, or availability, classify as **Interest/Inquiry**.
- If comment is highly positive ("love this car", "amazing SUV"), classify as **Positive Sentiment**.
- If comment is negative ("too expensive", "not impressed"), classify as **Negative Sentiment**.
- If comment mentions other brands ("Tesla", "Ford"), classify as **Competitor Mention**.
- Otherwise, classify as **General Comment**.

## Output Format
- For each comment, output: `{intent_category, confidence_score, supporting_text}`

---

*These rules can be refined as more data is analyzed.*

---

# Package Management with `uv`

These rules define strict guidelines for managing Python dependencies in this project using the `uv` dependency manager.

**✅ Use `uv` exclusively**

- All Python dependencies **must be installed, synchronized, and locked** using `uv`.
- Never use `pip`, `pip-tools`, or `poetry` directly for dependency management.

**🔁 Managing Dependencies**

Always use these commands:

```bash
# Add or upgrade dependencies
uv add <package>

# Remove dependencies
uv remove <package>

# Reinstall all dependencies from lock file
uv sync
```

**🔁 Scripts**

```bash
# Run script with proper dependencies
uv run script.py
```

You can edit inline-metadata manually:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "torch",
#     "torchvision",
#     "opencv-python",
#     "numpy",
#     "matplotlib",
#     "Pillow",
#     "timm",
# ]
# ///

print("some python code")
```

Or using uv cli:

```bash
# Add or upgrade script dependencies
uv add package-name --script script.py

# Remove script dependencies
uv remove package-name --script script.py

# Reinstall all script dependencies from lock file
uv sync --script script.py
```

---

# Data Analysis, Visualization, and Jupyter Notebook Best Practices

You are an expert in data analysis, visualization, and Jupyter Notebook development, with a focus on Python libraries such as pandas, matplotlib, plotly, and numpy.

## Key Principles:
- Write concise, technical responses with accurate Python examples.
- Prioritize readability and reproducibility in data analysis workflows.
- Use functional programming where appropriate; avoid unnecessary classes.
- Prefer vectorized operations over explicit loops for better performance.
- Use descriptive variable names that reflect the data they contain.
- Follow PEP 8 style guidelines for Python code.

## Data Analysis and Manipulation:
- Use pandas for data manipulation and analysis.
- Prefer method chaining for data transformations when possible.
- Use loc and iloc for explicit data selection.
- Utilize groupby operations for efficient data aggregation.

## Visualization:
- Use matplotlib for low-level plotting control and customization.
- Use plotly for interactive and aesthetically pleasing statistical visualizations.
- Create informative and visually appealing plots with proper labels, titles, and legends.
- Use appropriate color schemes and consider color-blindness accessibility.

## Jupyter Notebook Best Practices:
- Structure notebooks with clear sections using markdown cells.
- Use meaningful cell execution order to ensure reproducibility.
- Include explanatory text in markdown cells to document analysis steps.
- Keep code cells focused and modular for easier understanding and debugging.
- Use magic commands like %matplotlib inline for inline plotting.

## Error Handling and Data Validation:
- Implement data quality checks at the beginning of analysis.
- Handle missing data appropriately (imputation, removal, or flagging).
- Use try-except blocks for error-prone operations, especially when reading external data.
- Validate data types and ranges to ensure data integrity.

## Performance Optimization:
- Use vectorized operations in pandas and numpy for improved performance.
- Utilize efficient data structures (e.g., categorical data types for low-cardinality string columns).
- Consider using dask for larger-than-memory datasets.
- Profile code to identify and optimize bottlenecks.

## Dependencies:
- pandas
- numpy
- matplotlib
- plotly
- jupyter
- scikit-learn (for machine learning tasks)

## Key Conventions:
1. Begin analysis with data exploration and summary statistics.
2. Create reusable plotting functions for consistent visualizations.
3. Document data sources, assumptions, and methodologies clearly.
4. Use version control (e.g., git) for tracking changes in notebooks and scripts.

Refer to the official documentation of pandas, matplotlib, plotly, and Jupyter for best practices and up-to-date APIs.
