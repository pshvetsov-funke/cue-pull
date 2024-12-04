.PHONY: help
help:
	@echo "Available targets:"
	@echo "  terraform-plan      Run Terraform plan for the selected environment. Default environment - dev. Runs update-schema first"
	@echo "  terraform-apply     Run Terraform apply for the selected environment"


# Variables
ENVIRONMENT ?= dev
TERRAGRUNT_DIR = ./infra/live/$(ENVIRONMENT)

.PHONY: terraform-plan
terraform-plan:
	@echo "Running Terraform plan for $(ENVIRONMENT)..."
	terragrunt plan --terragrunt-working-dir $(TERRAGRUNT_DIR)

.PHONY: terraform-apply
terraform-apply:
	@echo "Running Terraform apply for $(ENVIRONMENT)..."
	terragrunt apply --terragrunt-working-dir $(TERRAGRUNT_DIR)

.PHONY: terraform-destroy
terraform-destroy:
	@echo "Running Terraform destroy for $(ENVIRONMENT)..."
	terragrunt destroy --terragrunt-working-dir $(TERRAGRUNT_DIR)