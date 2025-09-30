# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-30

### Added
- Initial release of Bitbucket CLI for Claude Code
- Complete pull request management functionality
- Support for repository access tokens and app password authentication
- Rich terminal output with formatted tables and colors
- Comprehensive command set:
  - `create` - Create new pull requests
  - `list` - List pull requests with filtering options
  - `show` - Display detailed PR information
  - `comment` - Add comments to pull requests
  - `approve` - Approve pull requests
  - `unapprove` - Remove approvals
  - `decline` - Decline pull requests
  - `merge` - Merge pull requests with different strategies
  - `config` - Manage authentication and configuration
- JSON output support for automation and scripting
- Auto-detection of workspace and repository from Git remotes
- Robust error handling with retry logic
- Interactive configuration setup
- Environment variable support for CI/CD integration
- Comprehensive documentation and examples

### Technical Features
- Built with modern Python packaging (pyproject.toml)
- Click framework for CLI interface
- Rich library for beautiful terminal output
- Pydantic for data validation and type safety
- Requests with retry strategies for API reliability
- GitPython for repository introspection
- YAML configuration file support
- Comprehensive test coverage
- Pre-commit hooks for code quality

### API Compatibility
- Bitbucket Cloud REST API v2.0 support
- Repository access token authentication (recommended)
- Username/app password fallback authentication
- OAuth token support for enterprise setups
- Comprehensive error handling for all API responses

### Documentation
- Detailed README with installation and usage instructions
- Complete command reference with examples
- Claude Code integration examples
- Troubleshooting guide
- Contributing guidelines
- MIT License

### Fixes
- Fixed Pydantic v2 compatibility (regex → pattern parameter)
- Fixed comment API payload format for successful posting
- Fixed author field access in PR listings (handles nickname/display_name variants)
- Fixed authentication validation for repository tokens
- Implemented proper table formatting for PR lists

### Known Issues
- Approve/unapprove commands may fail with 400 errors due to Bitbucket self-approval restrictions
- Pre-commit hooks require pytest installation in virtual environment

## [Unreleased]

### Planned Features
- Interactive PR review mode
- Diff viewing capabilities  
- Activity timeline display
- Batch operations for multiple PRs
- PR template support
- Webhook integration
- Enhanced error messages with suggested fixes

---

## Version History

- **1.0.0** - Initial stable release with full PR management capabilities