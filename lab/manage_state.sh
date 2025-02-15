#!/bin/bash

STATES_DIR="db_states"
DB_FILE="hospital.db"
UPLOADS_DIR="uploads"

# Create states directory if it doesn't exist
mkdir -p "$STATES_DIR"

# Function to show usage
show_usage() {
    echo "Database State Management for Turwin Medical Center"
    echo
    echo "Usage:"
    echo "  $0 save <state_name> [-d \"description\"]  Save current state"
    echo "  $0 load <state_name>                     Load a saved state"
    echo "  $0 list                                  List all saved states"
    echo "  $0 delete <state_name>                   Delete a saved state"
    echo
    echo "Examples:"
    echo "  $0 save clean_install -d \"Fresh database with no users\""
    echo "  $0 save with_test_users -d \"Database with sample users and records\""
    echo "  $0 load clean_install"
    echo "  $0 list"
}

# Function to save current state
save_state() {
    local state_name="$1"
    local description="$2"
    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local state_dir="$STATES_DIR/$state_name"
    
    # Check if database exists
    if [ ! -f "$DB_FILE" ]; then
        echo "Error: Database file not found!"
        exit 1
    fi
    
    # Create state directory
    mkdir -p "$state_dir"
    
    # Copy database
    cp "$DB_FILE" "$state_dir/${DB_FILE}_${timestamp}"
    
    # Copy uploads directory if it exists
    if [ -d "$UPLOADS_DIR" ]; then
        cp -r "$UPLOADS_DIR" "$state_dir/uploads_${timestamp}"
    fi
    
    # Save metadata
    echo "{
        \"timestamp\": \"$timestamp\",
        \"description\": \"$description\",
        \"db_file\": \"${DB_FILE}_${timestamp}\",
        \"uploads_dir\": \"uploads_${timestamp}\"
    }" > "$state_dir/metadata.json"
    
    echo "State '$state_name' saved successfully!"
    echo "Description: $description"
    echo "Timestamp: $timestamp"
}

# Function to load a state
load_state() {
    local state_name="$1"
    local state_dir="$STATES_DIR/$state_name"
    
    # Check if state exists
    if [ ! -d "$state_dir" ]; then
        echo "Error: State '$state_name' not found!"
        exit 1
    fi
    
    # Read metadata
    if [ ! -f "$state_dir/metadata.json" ]; then
        echo "Error: Metadata file not found!"
        exit 1
    fi
    
    # Get latest state file
    local latest_db=$(ls -t "$state_dir"/${DB_FILE}_* | head -1)
    local latest_uploads=$(ls -td "$state_dir"/uploads_* 2>/dev/null | head -1)
    
    if [ ! -f "$latest_db" ]; then
        echo "Error: Database file not found in state!"
        exit 1
    fi
    
    # Stop any running Flask server
    pkill -f "python app.py" || true
    
    # Backup current state if it exists
    if [ -f "$DB_FILE" ]; then
        mv "$DB_FILE" "${DB_FILE}.backup"
    fi
    if [ -d "$UPLOADS_DIR" ]; then
        mv "$UPLOADS_DIR" "${UPLOADS_DIR}.backup"
    fi
    
    # Restore state
    cp "$latest_db" "$DB_FILE"
    if [ -d "$latest_uploads" ]; then
        cp -r "$latest_uploads" "$UPLOADS_DIR"
    fi
    
    echo "State '$state_name' loaded successfully!"
    
    # Restart Flask server
    python app.py &
}

# Function to list states
list_states() {
    echo "Saved States:"
    echo "-------------"
    
    for state_dir in "$STATES_DIR"/*; do
        if [ -d "$state_dir" ]; then
            local state_name=$(basename "$state_dir")
            if [ -f "$state_dir/metadata.json" ]; then
                local description=$(grep "description" "$state_dir/metadata.json" | cut -d'"' -f4)
                local timestamp=$(grep "timestamp" "$state_dir/metadata.json" | cut -d'"' -f4)
                echo "Name: $state_name"
                echo "Description: $description"
                echo "Last saved: $timestamp"
                echo "-------------"
            fi
        fi
    done
}

# Function to delete a state
delete_state() {
    local state_name="$1"
    local state_dir="$STATES_DIR/$state_name"
    
    if [ ! -d "$state_dir" ]; then
        echo "Error: State '$state_name' not found!"
        exit 1
    fi
    
    rm -rf "$state_dir"
    echo "State '$state_name' deleted successfully!"
}

# Main script
case "$1" in
    save)
        if [ "$#" -lt 2 ]; then
            show_usage
            exit 1
        fi
        description=""
        if [ "$3" = "-d" ] && [ "$#" -ge 4 ]; then
            description="$4"
        fi
        save_state "$2" "$description"
        ;;
    load)
        if [ "$#" -ne 2 ]; then
            show_usage
            exit 1
        fi
        load_state "$2"
        ;;
    list)
        list_states
        ;;
    delete)
        if [ "$#" -ne 2 ]; then
            show_usage
            exit 1
        fi
        delete_state "$2"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
