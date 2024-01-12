# GitLab Repository Analyzer

This project provides a comprehensive analysis of GitLab repositories. It gathers data on various aspects like commits,
branches, CI/CD pipelines, and more. The analysis includes conventional commit adherence, language usage, presence of
tests, and other vital metrics, compiled into a detailed Excel report.

## Features

- **Commit Analysis**: Evaluates commit messages against Conventional Commit standards.
- **Branch Analysis**: Enumerates commits in each branch.
- **CI/CD Pipeline Detection**: Checks for the presence of CI/CD configurations.
- **Test Detection**: Identifies if the project contains tests.
- **Language Usage**: Breaks down the percentage usage of programming languages in each project.
- **File Path Analysis**: Retrieves all file paths, including those in subdirectories.

## Requirements

- Python 3.x
- GitLab Access Token
- Python libraries: `gitlab`, `pandas`, `PyYAML`, `tqdm`

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://your-repository-url.git
   ```
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

### Dockerfile

```bash
docker build -t gitlab_analyser:latest .

```

## Usage

1. Set your GitLab access token in the .env or via parser arguments.

a. Via .env 

   ```.env
   gitlab_url = <your gitlab url>
   access_token = < access token with read access to your repositories>
   ```
   ```bash
   python main.py
   ```

b. Via Parser:

   ```bash
   python main.py --access_token <token>  --gitlab_url <token>
   ```

2. The script will generate an Excel file with the analysis data.


## Contributing

Contributions to this project are welcome. Please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to GitLab for their powerful API and extensive documentation.

## Contact

For any queries or feedback, please contact [Your Email](mailto:alikazemi@ieee.org).

```

### Explanation of Sections:

- **Features**: Summarizes what the project does.
- **Requirements**: Lists the necessary tools and libraries.
- **Installation**: Provides step-by-step instructions to set up the project.
- **Usage**: Explains how to run the script and what to expect.
- **Contributing**: Encourages others to contribute to the project.
- **License**: Mentions the license type (you can choose an appropriate license).
- **Acknowledgments**: Credits to anyone or any resource that aided the project.
- **Contact**: Provides a way to reach out for more information or support.

