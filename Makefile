schema:
	python ./utils/convert_schema.py
tf-init-tf:
	terraform -chdir=./infrastructure init
tf-plan:
	terraform -chdir=./infrastructure plan
tf-apply:
	terraform -chdir=./infrastructure apply
tf-init: schema tf-init-tf
