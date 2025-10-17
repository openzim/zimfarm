#!/bin/bash

# Script to register offliners in Zimfarm
# - retrieve an admin token
# - fetch offliner definitions from their respective GitHub repositories
# - register each offliner and its definition with the backend API

set -e

# List of offliners to register
OFFLINERS=("devdocs" "freecodecamp" "gutenberg" "ifixit" "kolibri" "mindtouch" "mwoffliner" "nautilus" "openedx" "phet" "sotoki" "ted" "youtube" "zimit")

# Base URL for offliner definitions
BASE_URL="https://raw.githubusercontent.com/openzim"

# Offliner configuration data for API registration
declare -A offliner_configs

# Initialize offliner configurations
setup_offliner_configs() {
    # DashModel offliners
    offliner_configs["devdocs"]='{"base_model":"DashModel","docker_image_name":"openzim/devdocs","command_name":"devdocs2zim"}'
    offliner_configs["freecodecamp"]='{"base_model":"DashModel","docker_image_name":"openzim/freecodecamp","command_name":"fcc2zim"}'
    offliner_configs["gutenberg"]='{"base_model":"DashModel","docker_image_name":"openzim/gutenberg","command_name":"gutenberg2zim"}'
    offliner_configs["sotoki"]='{"base_model":"DashModel","docker_image_name":"openzim/sotoki","command_name":"sotoki2zim"}'
    offliner_configs["wikihow"]='{"base_model":"DashModel","docker_image_name":"openzim/wikihow","command_name":"wikihow2zim"}'
    offliner_configs["ifixit"]='{"base_model":"DashModel","docker_image_name":"openzim/ifixit","command_name":"ifixit2zim"}'
    offliner_configs["mwoffliner"]='{"base_model":"DashModel","docker_image_name":"openzim/mwoffliner","command_name":"mwoffliner"}'
    offliner_configs["youtube"]='{"base_model":"DashModel","docker_image_name":"openzim/youtube","command_name":"youtube2zim"}'
    offliner_configs["ted"]='{"base_model":"DashModel","docker_image_name":"openzim/ted","command_name":"ted2zim"}'
    offliner_configs["openedx"]='{"base_model":"DashModel","docker_image_name":"openzim/openedx","command_name":"openedx2zim"}'
    offliner_configs["nautilus"]='{"base_model":"DashModel","docker_image_name":"openzim/nautilus","command_name":"nautiluszim"}'
    offliner_configs["kolibri"]='{"base_model":"DashModel","docker_image_name":"openzim/kolibri","command_name":"kolibri2zim"}'
    offliner_configs["mindtouch"]='{"base_model":"DashModel","docker_image_name":"openzim/mindtouch","command_name":"mindtouch2zim"}'
    offliner_configs["phet"]='{"base_model":"DashModel","docker_image_name":"openzim/phet","command_name":"phet2zim"}'

    # CamelModel offliners
    offliner_configs["zimit"]='{"base_model":"CamelModel","docker_image_name":"openzim/zimit","command_name":"zimit"}'
}

die() {
    echo "ERROR: $1" >&2
    exit 1
}

fetch_offliner_definition() {
    local offliner_name="$1"
    local url="${BASE_URL}/${offliner_name}/refs/heads/main/offliner-definition.json"

    local definition
    if ! definition=$(curl -s -f "$url"); then
        die "Failed to fetch offliner definition for ${offliner_name} from ${url}"
    fi

    if ! echo "$definition" | jq . >/dev/null 2>&1; then
        die "Invalid JSON received for ${offliner_name}"
    fi

    echo "$definition"
}

register_offliner_via_api() {
    local offliner_id="$1"
    local config="${offliner_configs[$offliner_id]}"
    echo "Registering ${offliner} via API..."

    if [ -z "$config" ]; then
        die "No configuration found for offliner: ${offliner_id}"
    fi
    # Create the payload with offliner_id used as ci_secret_hash
    local payload
    payload=$(echo "$config" | jq --arg offliner_id "$offliner_id" '. + {"ci_secret_hash": $offliner_id, "offliner_id": $offliner_id}')

    local response
    local http_code
    response=$(curl -s -w "\n%{http_code}" -X 'POST' \
        "http://localhost:8000/v2/offliners" \
        -H 'accept: application/json' \
        -H "Authorization: Bearer ${ZF_ADMIN_TOKEN}" \
        -H 'Content-Type: application/json' \
        -d "$payload")

    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    response=$(echo "$response" | head -n -1)

    case "$http_code" in
        201)
            echo "Successfully registered ${offliner_id}"
            ;;
        409)
            echo "WARNING: Offliner ${offliner_id} already exists, skipping..."
            ;;
        *)
            local error_msg
            error_msg=$(echo "$response" | jq -r '.errors // .message // .detail // "Unknown error"' 2>/dev/null || echo "HTTP $http_code")
            die "Registration failed for ${offliner_id}: ${error_msg}"
            ;;
    esac
}

# Function to create offliner definition schema
create_offliner_definition() {
    local offliner_id="$1"
    local spec="${offliner_definitions[$offliner_id]}"

    if [ -z "$spec" ]; then
        die "No definition found for offliner: ${offliner_id}"
    fi

    echo "Creating definition for ${offliner_id}..."

    # Create the payload for schema creation
    local payload
    payload=$(jq -n \
        --arg version "dev" \
        --arg ci_secret "$offliner_id" \
        --argjson spec "$spec" \
        '{version: $version, ci_secret: $ci_secret, spec: $spec}')


    # Create the schema via API
    local response
    local http_code
    response=$(curl -s -w "\n%{http_code}" -X 'POST' \
        "http://localhost:8000/v2/offliners/${offliner_id}/versions" \
        -H 'accept: application/json' \
        -H "Authorization: Bearer ${ZF_ADMIN_TOKEN}" \
        -H 'Content-Type: application/json' \
        -d "$payload")

    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    response=$(echo "$response" | head -n -1)

    case "$http_code" in
        201)
            echo "Successfully created schema for ${offliner_id}"
            ;;
        409)
            echo "WARNING: Offliner ${offliner_id} already exists, skipping..."
            ;;
        *)
            local error_msg
            error_msg=$(echo "$response" | jq -r '.errors // .message  // .detail // "Unknown error"' 2>/dev/null || echo "HTTP $http_code")
            die "Definition creation failed for ${offliner_id}: ${error_msg}"
            ;;
    esac
}

echo "Retrieving admin access token"

ZF_ADMIN_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v2/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"username": "admin", "password": "admin"}' \
    | jq -r '.access_token')"

if [ -z "$ZF_ADMIN_TOKEN" ] || [ "$ZF_ADMIN_TOKEN" = "null" ]; then
    die "Failed to retrieve admin access token"
fi

echo "Admin token retrieved successfully"

# Setup offliner configurations for API registration
setup_offliner_configs

# Declare associative array to store offliner definitions
declare -A offliner_definitions

echo "Fetching offliner definitions..."

for offliner in "${OFFLINERS[@]}"; do
    echo "Fetching ${offliner} definition..."
    offliner_definitions["$offliner"]=$(fetch_offliner_definition "$offliner" | jq -c '.')
done

echo "All offliner definitions fetched successfully"

for offliner in "${OFFLINERS[@]}"; do
    register_offliner_via_api "$offliner"
    create_offliner_definition "$offliner"
done
echo "All offliners registered via API successfully!"
