.PHONY: help
help: ## Show this help.
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.PHONY: format
format: ## Automatically format files.
	@echo "🚀 Linting code with pre-commit (prek)"
	@uv run prek run -a

.PHONY: test
test: ## Test the code with pytest.
	@echo "🚀 Testing code with pytest"
	@uv run pytest
