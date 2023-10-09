# Docker Based Scrapers for LinkedIn and Facebook

This repository contains Docker-based scrapers for Facebook and LinkedIn. These scrapers are designed to extract information from business profiles and pages on both platforms for various purposes, such as data analysis, research, and more. Using these scrapers for comme By using Docker, the scrapers can be easily set up and run in isolated environments without the need for complex configuration.

## Table of Contents
- Prerequisites
- Getting Started
- Usage
- Configuration
- Contributing
- License


### Prerequisites
Before you begin, ensure you have the following prerequisites installed on your system:

**Docker** - Docker is used to containerize the scrapers and their dependencies, making it easy to deploy them in various environments.

**Docker Compose** - Docker Compose simplifies the management of multi-container Docker applications.

**Microsoft Azure Storage Account** - Azure storage will be used in storing of data inputs and outputs produced by the scraper.

### Getting Started
1. Clone this repository to your local machine:

```
git clone https://github.com/yourusername/docker-facebook-linkedin-scraper.git
```
2. Update the secrets.env file with the expected credentials

3. Create the four blob containers on the Azure storage account named as follows:

        - facebook-inputs
        - facebook-outputs
        - linkedin-inputs
        - linkedin-outputs


Build the Docker containers:

docker-compose build
Start the containers:

shell
Copy code
docker-compose up -d