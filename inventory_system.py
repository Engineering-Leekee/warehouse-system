# Basic Warehouse Management System
inventory = {}

def add_item(part_number, location, quantity):
    """Add new item to inventory"""
    if part_number in inventory:
        inventory[part_number]['quantity'] += quantity
    else:
        inventory[part_number] = {
            'location': location,
            'quantity': quantity
        }

def remove_item(part_number, quantity):
    """Remove item from inventory"""
    if part_number in inventory:
        if inventory[part_number]['quantity'] >= quantity:
            inventory[part_number]['quantity'] -= quantity
            if inventory[part_number]['quantity'] == 0:
                del inventory[part_number]
            return True
    return False

def get_item_location(part_number):
    """Get location of specific part"""
    return inventory.get(part_number, {}).get('location', 'Not found')

def print_inventory():
    """Display current inventory"""
    # This function is now primarily for console debugging if needed
    # The web UI will handle display
    for part, details in inventory.items():
        print(f"Part: {part}, Location: {details['location']}, Qty: {details['quantity']}")

# Example usage (these will run once when app.py imports this)
add_item("PN123", "A1-45", 10)
add_item("PN456", "B2-12", 5)
add_item("PN789", "C3-01", 20)