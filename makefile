.PHONY: test
flags=--profile pc --region ap-southeast-2

test:
	sam local invoke "ProcessVisitorsFunction" --event events/photo.json ${flags}

deploy:
	sam package --s3-bucket djenny-sam-builds --output-template-file packaged.yaml ${flags}
	sam deploy --template-file packaged.yaml --stack-name sam-app-process-visitors --capabilities CAPABILITY_IAM ${flags}

