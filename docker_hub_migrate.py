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
    
    def get_repositories(self):
        """Get list of private repositories in the source organization"""
        print(f"Fetching repositories from {self.source_org}...")
        repos = []
        page = 1
        page_size = 100
        
        while True:
            repo_url = f"{self.api_base}repositories/{self.source_org}?page={page}&page_size={page_size}"
            try:
                response = requests.get(repo_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # Filter for private repositories
                private_repos = [repo for repo in data["results"] if repo["is_private"]]
                repos.extend(private_repos)
                
                if not data["next"]:
                    break
                page += 1
            except requests.exceptions.RequestException as e:
                print(f"Error fetching repositories: {e}")
                return None
        
        print(f"Found {len(repos)} private repositories in {self.source_org}")
        return repos
    
    def get_tags(self, repo_name):
        """Get all tags for a repository"""
        tags_url = f"{self.api_base}repositories/{self.source_org}/{repo_name}/tags"
        try:
            response = requests.get(tags_url, headers=self.headers)
            response.raise_for_status()
            tags = response.json()["results"]
            return [tag["name"] for tag in tags]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tags for {repo_name}: {e}")
            return ["latest"]  # Default to latest if we can't get tags
    
    def create_repository(self, repo_name, repo_description=""):
        """Create a new repository in the target organization"""
        create_url = f"{self.api_base}repositories/{self.target_org}"
        create_data = {
            "name": repo_name,
            "description": repo_description,
            "is_private": True
        }
        
        try:
            response = requests.post(create_url, data=json.dumps(create_data), headers=self.headers)
            response.raise_for_status()
            print(f"Created repository {self.target_org}/{repo_name}")
            return True
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e):
                print(f"Repository {self.target_org}/{repo_name} already exists")
                return True
            
            print(f"Error creating repository {repo_name}: {e}")
            # Print detailed error response if available
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print("Could not parse error details")
            
            # Check if the issue is with organization access
            print(f"Checking permissions for organization {self.target_org}...")
            try:
                org_check_url = f"{self.api_base}user/orgs/"
                org_response = requests.get(org_check_url, headers=self.headers)
                org_response.raise_for_status()
                orgs = org_response.json()
                
                # Check if target org is in user's organizations
                org_names = [org["orgname"] for org in orgs["results"]]
                if self.target_org not in org_names:
                    print(f"WARNING: You may not have access to organization '{self.target_org}'")
                    print(f"Available organizations: {', '.join(org_names)}")
            except Exception as org_error:
                print(f"Could not verify organization access: {org_error}")
                
            return False
    
    def docker_pull(self, repo_name, tag):
        """Pull a Docker image"""
        source_image = f"{self.source_org}/{repo_name}:{tag}"
        print(f"Pulling {source_image}...")
        
        try:
            result = subprocess.run(
                ["docker", "pull", source_image],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pulling image: {e}")
            print(e.stderr)
            return False
    
    def docker_tag(self, repo_name, tag):
        """Tag a Docker image for the target organization"""
        source_image = f"{self.source_org}/{repo_name}:{tag}"
        target_image = f"{self.target_org}/{repo_name}:{tag}"
        print(f"Tagging {source_image} as {target_image}...")
        
        try:
            result = subprocess.run(
                ["docker", "tag", source_image, target_image],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error tagging image: {e}")
            print(e.stderr)
            return False
    
    def docker_push(self, repo_name, tag):
        """Push a Docker image to the target organization"""
        target_image = f"{self.target_org}/{repo_name}:{tag}"
        print(f"Pushing {target_image}...")
        
        try:
            result = subprocess.run(
                ["docker", "push", target_image],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing image: {e}")
            print(e.stderr)
            return False
    
    def migrate_repository_with_images(self, repo):
        """Migrate a repository with all its images from source to target org"""
        repo_name = repo["name"]
        repo_description = repo.get("description", "")
        
        print(f"\nMigrating {self.source_org}/{repo_name} to {self.target_org}/{repo_name}...")
        
        # Create the repository in the target organization
        if not self.create_repository(repo_name, repo_description):
            return False
        
        # Get all tags for this repository
        tags = self.get_tags(repo_name)
        if not tags:
            print(f"No tags found for {repo_name}, using 'latest'")
            tags = ["latest"]
        
        success_count = 0
        for tag in tags:
            print(f"\nProcessing {repo_name}:{tag}")
            
            # Pull, tag, and push the image
            if not self.docker_pull(repo_name, tag):
                print(f"Failed to pull {repo_name}:{tag}, skipping...")
                continue
                
            if not self.docker_tag(repo_name, tag):
                print(f"Failed to tag {repo_name}:{tag}, skipping...")
                continue
                
            if not self.docker_push(repo_name, tag):
                print(f"Failed to push {repo_name}:{tag}, skipping...")
                continue
                
            success_count += 1
            
        print(f"Successfully migrated {success_count}/{len(tags)} tags for {repo_name}")
        return success_count > 0
    
    def migrate_all_repositories(self):
        """Migrate all private repositories from source to target org"""
        if not self.authenticate():
            return False
            
        if not self.docker_login():
            return False
        
        repositories = self.get_repositories()
        if not repositories:
            return False
        
        success_count = 0
        for repo in repositories:
            print("\n" + "-" * 50)
            if self.migrate_repository_with_images(repo):
                success_count += 1
            time.sleep(1)  # Avoid rate limiting
        
        print("\n" + "=" * 50)
        print(f"Migration summary: {success_count}/{len(repositories)} repositories processed.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Migrate private Docker Hub repositories between organizations")
    parser.add_argument("source_org", help="Source Docker Hub organization")
    parser.add_argument("target_org", help="Target Docker Hub organization")
    parser.add_argument("-u", "--username", help="Docker Hub username")
    
    args = parser.parse_args()
    
    if not args.username:
        args.username = input("Docker Hub username: ")
    
    password = getpass("Docker Hub password: ")
    
    migrator = DockerHubMigrator(args.username, password, args.source_org, args.target_org)
    if not migrator.migrate_all_repositories():
        sys.exit(1)


if __name__ == "__main__":
    main()