# Docker Hub Organization Repository Migrator

A Python tool to migrate private repositories from one Docker Hub organization to another, including all image tags.

## Overview

This script automates the process of migrating private repositories between Docker Hub organizations by:

1. Authenticating with Docker Hub API
2. Discovering all private repositories in the source organization
3. Creating matching repositories in the target organization
4. Automatically pulling, tagging, and pushing all image tags

## Requirements

- Python 3.6+
- Docker CLI installed and running
- Docker Hub account with access to both source and target organizations
- Administrative rights to create repositories in the target organization

## Installation

1. Clone this repository or download the script to your local machine:

```bash
git clone https://github.com/Yusful33/hub_migrate_repos.git
cd hub_migrate_repos
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with:

```bash
python docker_hub_migrate.py SOURCE_ORG TARGET_ORG -u YOUR_USERNAME
```

Replace:
- `SOURCE_ORG`: The name of the source Docker Hub organization
- `TARGET_ORG`: The name of the target Docker Hub organization
- `YOUR_USERNAME`: Your Docker Hub username

The script will prompt you for your Docker Hub password.

### Example

```bash
python docker_hub_migrate.py oldcompany newcompany -u johndoe
```

## Docker Usage

You can also run this tool using Docker:

```bash
# Build the Docker image
docker build -t hub-migrator .

# Run the container (mounting the Docker socket)
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  hub-migrator SOURCE_ORG TARGET_ORG -u YOUR_USERNAME
```

## Features

- Authenticates with Docker Hub API and Docker CLI
- Fetches all private repositories from the source organization
- Creates equivalent repositories in the target organization
- Fetches all available tags for each repository
- Handles the pulling, tagging, and pushing of each image tag
- Provides detailed progress output and error handling
- Generates a summary report of migrated repositories

## Troubleshooting

### Permission Issues

If you encounter permission errors:
- Ensure you have administrative access to both organizations
- Verify the organization names are correct
- Check that you can manually create repositories in the target organization

### Docker Login Failures

If Docker login fails:
- Ensure Docker is running on your system
- Try logging in manually with `docker login` first
- Consider using a Docker Hub access token instead of your password

### Docker Hub API Errors

If you receive HTTP errors from the API:
- The script provides detailed error information which can help diagnose issues
- For 400 errors when creating repositories, check your organization permissions
- For 404 errors, verify the organization names and repository paths

## Notes

- The migration process can take a significant amount of time depending on the number and size of images
- Docker Hub API rate limits may apply
- Large images will require sufficient disk space and network bandwidth

## License

This project is licensed under the MIT License - see the LICENSE file for details.