def generate_list():
    """Generates and returns a sample list."""
    items = [
        "Item 1: Review project milestones",
        "Item 2: Update documentation",
        "Item 3: Coordinate with team members",
        "Item 4: Finalize operational invoice logs",
        "Item 5: Backup local digital assets"
    ]
    return items

if __name__ == "__main__":
    task_list = generate_list()
    print("--- Generated List ---")
    for item in task_list:
        print(f"* {item}")
