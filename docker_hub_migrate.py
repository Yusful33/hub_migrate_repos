#!/usr/bin/env python3
import requests
import json
import argparse
import sys
import time
import subprocess
import os
from getpass import getpass

class DockerHubMigrator:
    def __init__(self, username, password, source_org, target_org):
        self.username = username
        self.password = password
        self.source_org = source_org
        self.target_org = target_org
        self.token = None
        self.api_base = "https://hub.docker.com/v2/"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def authenticate(self):
        """Authenticate with Docker Hub and get a token"""
        print(f"Authenticating as {self.username}...")
        auth_url = f"{self.api_base}users/login"
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = requests.post(auth_url, data=json.dumps(auth_data), headers=self.headers)
            response.raise_for_status()
            self.token = response.json()["token"]
            self.headers["Authorization"] = f"JWT {self.token}"
            print("Authentication successful!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def docker_login(self):
        """Log in to Docker CLI using environment variables"""
        print("Logging in to Docker CLI...")
        try:
            # Create a modified environment with DOCKER_PASSWORD
            env = os.environ.copy()
            env["DOCKER_PASSWORD"] = self.password
            
            # Use echo to pipe the password to docker login
            login_command = f'echo "$DOCKER_PASSWORD" | docker login -u {self.username} --password-stdin'
            
            # Use shell=True to properly handle the pipe
            result = subprocess.run(
                login_command,
                shell=True,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("Docker CLI login successful!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Docker login failed: {e}")
            print(f"Error output: {e.stderr}")
            return False