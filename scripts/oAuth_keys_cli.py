#!/usr/bin/env python3
"""Script to generate OAuth keys using the provided environment variables."""

import os

def generate_oauth_key():
    client_id = os.environ.get('OAUTH_CLIENT_ID')
    client_secret = os.environ.get('OAUTH_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError("Missing client ID or client secret in environment variables.")

    # Simulated key generation logic
    oauth_key = f"key_{client_id}_{client_secret}"

    return oauth_key

if __name__ == "__main__":
    print("Generated OAuth Key:", generate_oauth_key())
